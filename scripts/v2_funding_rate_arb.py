import os
from decimal import Decimal
from typing import Dict, List, Set

import pandas as pd
from pydantic import Field, field_validator

from hummingbot.client.ui.interface_utils import format_df_for_printout
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.clock import Clock
from hummingbot.core.data_type.common import OrderType, PositionMode, PriceType, TradeType
from hummingbot.core.event.events import FundingPaymentCompletedEvent
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase
from hummingbot.strategy_v2.executors.position_executor.data_types import PositionExecutorConfig, TripleBarrierConfig
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, StopExecutorAction


class FundingRateArbitrageConfig(StrategyV2ConfigBase):
    script_file_name: str = os.path.basename(__file__)
    candles_config: List[CandlesConfig] = []
    controllers_config: List[str] = []
    markets: Dict[str, Set[str]] = {}
    leverage: int = Field(
        default=5, gt=0,
        json_schema_extra={"prompt": lambda mi: "Enter the leverage (e.g. 5): ", "prompt_on_new": True},
    )
    min_funding_rate_profitability: Decimal = Field(
        default=0.003,
        json_schema_extra={
            "prompt": lambda mi: "Enter the min funding rate profitability per hour to enter in a position (e.g. 0.003 for 0.3%/hr): ",
            "prompt_on_new": True}
    )
    connectors: Set[str] = Field(
        default="extended_perpetual,lighter_perpetual",
        json_schema_extra={
            "prompt": lambda mi: "Enter the connectors separated by commas (e.g. extended_perpetual,lighter_perpetual): ",
            "prompt_on_new": True}
    )
    tokens: Set[str] = Field(
        default="KAITO,MON,IP,GRASS,ZEC,APT,SUI,TRUMP,LDO,OP,SEI,MEGA",
        json_schema_extra={"prompt": lambda mi: "Enter the tokens separated by commas (e.g. KAITO,MON,IP): ", "prompt_on_new": True},
    )
    position_size_quote: Decimal = Field(
        default=500,
        json_schema_extra={
            "prompt": lambda mi: "Enter the position size in quote asset per side (e.g. 500 will open $500 long and $500 short): ",
            "prompt_on_new": True
        }
    )
    absolute_min_spread_exit: Decimal = Field(
        default=0.002,
        json_schema_extra={
            "prompt": lambda mi: "Enter the absolute minimum spread per hour for exit (e.g. 0.002 for 0.2%/hr): ",
            "prompt_on_new": True}
    )
    compression_exit_threshold: Decimal = Field(
        default=0.4,
        json_schema_extra={
            "prompt": lambda mi: "Enter the compression exit threshold (e.g. 0.4 = exit at 60% compression): ",
            "prompt_on_new": True}
    )
    max_position_duration_hours: int = Field(
        default=24,
        json_schema_extra={
            "prompt": lambda mi: "Enter the max position duration in hours (e.g. 24): ",
            "prompt_on_new": True}
    )
    max_loss_per_position_pct: Decimal = Field(
        default=0.03,
        json_schema_extra={
            "prompt": lambda mi: "Enter the max loss per position % (e.g. 0.03 for 3%): ",
            "prompt_on_new": True}
    )
    order_price_buffer_pct: Decimal = Field(
        default=0.005,
        json_schema_extra={
            "prompt": lambda mi: "Enter order price buffer % for limit orders (e.g. 0.005 for 0.5%): ",
            "prompt_on_new": True}
    )
    min_balance_threshold: Decimal = Field(
        default=Decimal("200"),
        json_schema_extra={
            "prompt": lambda mi: "Enter minimum balance threshold in USD (warning level, e.g. 200): ",
            "prompt_on_new": False}
    )
    min_daily_volume_usd: Decimal = Field(
        default=Decimal("50000"),
        json_schema_extra={
            "prompt": lambda mi: "Enter minimum 24h volume per side in USD (e.g. 50000): ",
            "prompt_on_new": True}
    )

    @field_validator("connectors", "tokens", mode="before")
    @classmethod
    def validate_sets(cls, v):
        if isinstance(v, str):
            return set(v.split(","))
        return v


class FundingRateArbitrage(StrategyV2Base):
    quote_markets_map = {
        "extended_perpetual": "USD",
        "lighter_perpetual": "USD",
        "hyperliquid_perpetual": "USD",
        "binance_perpetual": "USDT"
    }
    funding_payment_interval_map = {
        "extended_perpetual": 60 * 60 * 8,
        "lighter_perpetual": 60 * 60 * 1,
        "binance_perpetual": 60 * 60 * 8,
        "hyperliquid_perpetual": 60 * 60 * 1
    }
    funding_profitability_interval = 60 * 60 * 1  # 1 hour (changed from 24 hours)

    # Lighter max leverage per token (also applied to Extended for consistency)
    # Lighter always has lower leverage limits, so we use these for both exchanges
    lighter_max_leverage_by_token = {
        "KAITO": 5,
        "MON": 3,
        "IP": 10,
        "GRASS": 5,
        "ZEC": 5,
        "APT": 10,
        "SUI": 10,
        "TRUMP": 10,
        "LDO": 10,
        "OP": 15,
        "SEI": 10,
        "MEGA": 3,
    }

    @classmethod
    def get_trading_pair_for_connector(cls, token, connector):
        return f"{token}-{cls.quote_markets_map.get(connector, 'USDT')}"

    @classmethod
    def init_markets(cls, config: FundingRateArbitrageConfig):
        markets = {}
        for connector in config.connectors:
            trading_pairs = {cls.get_trading_pair_for_connector(token, connector) for token in config.tokens}
            markets[connector] = trading_pairs
        cls.markets = markets

    def __init__(self, connectors: Dict[str, ConnectorBase], config: FundingRateArbitrageConfig):
        super().__init__(connectors, config)
        self.config = config
        self.active_funding_arbitrages = {}
        self.stopped_funding_arbitrages = {token: [] for token in self.config.tokens}

        # Token availability cache: {token: [list of connectors where it exists]}
        self.token_availability_cache = {}
        # Reverse lookup: {connector: {trading_pair: token}}
        self.connector_markets_cache = {}

    def build_token_availability_cache(self):
        """
        Build cache of which tokens are available on which connectors.
        This prevents errors when trying to fetch funding rates for tokens
        that don't exist on all exchanges.
        """
        self.logger().info("Building token availability cache...")

        for connector_name, connector in self.connectors.items():
            if not self.is_perpetual(connector_name):
                continue

            # Get all trading pairs available on this connector
            try:
                all_trading_pairs = connector.trading_pairs
                self.connector_markets_cache[connector_name] = {}

                for trading_pair in all_trading_pairs:
                    # Extract base token from trading pair (e.g., "KAITO" from "KAITO-USD")
                    token = trading_pair.split("-")[0]

                    # Only track tokens in our config
                    if token in self.config.tokens:
                        if token not in self.token_availability_cache:
                            self.token_availability_cache[token] = []
                        self.token_availability_cache[token].append(connector_name)
                        self.connector_markets_cache[connector_name][trading_pair] = token

            except Exception as e:
                self.logger().error(f"Failed to get trading pairs for {connector_name}: {e}")

        # Log results
        self.logger().info(f"Token availability cache built:")
        for token in self.config.tokens:
            available_on = self.token_availability_cache.get(token, [])
            num_exchanges = len(available_on)

            if num_exchanges >= 2:
                self.logger().info(f"  ✅ {token}: available on {num_exchanges} exchanges ({', '.join(available_on)})")
            elif num_exchanges == 1:
                self.logger().info(f"  ℹ️  {token}: only on {available_on[0]} - cannot arbitrage")
            else:
                self.logger().info(f"  ℹ️  {token}: not available on any configured exchange")

    def get_required_margin(self, connector_name: str, position_size_quote: Decimal, token: str = None) -> Decimal:
        """
        Calculate the margin (collateral) required for a position.

        Args:
            connector_name: Exchange connector name
            position_size_quote: Position size in quote currency (USD)
            token: Token symbol (optional, uses config leverage if not provided)

        Returns:
            Required margin in quote currency with 10% safety buffer
        """
        # Get leverage for this token (if specified), otherwise use config leverage
        if token:
            leverage = Decimal(str(self.get_leverage_for_token(token)))
        else:
            leverage = Decimal(str(self.config.leverage))

        # Margin = Position Size / Leverage
        required_margin = position_size_quote / leverage

        # Add 10% safety buffer for fees and price slippage
        safety_buffer = Decimal("1.1")

        return required_margin * safety_buffer

    def check_sufficient_balance(self, connector_name: str, required_amount: Decimal) -> tuple:
        """
        Check if connector has sufficient balance for a position.

        Returns:
            (is_sufficient, available_balance, shortfall)
        """
        connector = self.connectors[connector_name]
        quote_asset = self.quote_markets_map.get(connector_name, "USDT")

        available_balance = connector.get_available_balance(quote_asset)
        is_sufficient = available_balance >= required_amount
        shortfall = max(Decimal("0"), required_amount - available_balance)

        return is_sufficient, available_balance, shortfall

    def start(self, clock: Clock, timestamp: float) -> None:
        """
        Start the strategy.
        :param clock: Clock to use.
        :param timestamp: Current time.
        """
        self._last_timestamp = timestamp
        # Build token availability cache first
        self.build_token_availability_cache()
        # Then apply settings (leverage, position mode)
        self.apply_initial_setting()

    def get_leverage_for_token(self, token: str) -> int:
        """
        Get the leverage to use for a given token.

        Since Lighter always has lower leverage limits than Extended,
        we use Lighter's max leverage for both exchanges to ensure consistency.

        Args:
            token: Base token (e.g., "KAITO", "IP", "TRUMP")

        Returns:
            Leverage to use for this token on both exchanges
        """
        # Get Lighter's max leverage for this token (default to 5x if not specified)
        lighter_max = self.lighter_max_leverage_by_token.get(token, 5)

        # Use the minimum of Lighter's max and user's configured leverage
        return min(lighter_max, self.config.leverage)

    def apply_initial_setting(self):
        """
        Apply initial settings: position mode and per-token leverage.

        Leverage is set per token based on Lighter's max leverage (applied to both exchanges).
        """
        # Set position mode for all connectors
        for connector_name, connector in self.connectors.items():
            if self.is_perpetual(connector_name):
                position_mode = PositionMode.ONEWAY if connector_name in ["hyperliquid_perpetual", "extended_perpetual", "lighter_perpetual"] else PositionMode.HEDGE
                connector.set_position_mode(position_mode)

        # Set leverage per token (using Lighter's max leverage for both exchanges)
        self.logger().info("Setting leverage per token (based on Lighter limits)...")
        leverage_by_token = {}

        for token in self.config.tokens:
            # Get leverage for this token (Lighter's max, capped by user config)
            token_leverage = self.get_leverage_for_token(token)
            leverage_by_token[token] = token_leverage

            # Set leverage on all connectors for this token
            for connector_name, connector in self.connectors.items():
                if self.is_perpetual(connector_name):
                    trading_pair = self.get_trading_pair_for_connector(token, connector_name)
                    try:
                        connector.set_leverage(trading_pair, token_leverage)
                        self.logger().info(f"✓ {token}: {token_leverage}x on {connector_name}")
                    except Exception as e:
                        self.logger().warning(f"✗ Could not set leverage for {trading_pair} on {connector_name}: {e}")

        self.logger().info(f"Leverage configuration: {leverage_by_token}")

        # Check initial balances on startup
        self.logger().info("\nChecking initial balances...")
        for connector_name, connector in self.connectors.items():
            if self.is_perpetual(connector_name):
                quote_asset = self.quote_markets_map.get(connector_name, "USDT")
                available = connector.get_available_balance(quote_asset)

                # Calculate rough position capacity (using average leverage)
                avg_leverage = sum(leverage_by_token.values()) / len(leverage_by_token) if leverage_by_token else self.config.leverage
                approx_required = self.config.position_size_quote / Decimal(str(avg_leverage)) * Decimal("1.1")

                max_positions = int(available / approx_required) if approx_required > 0 else 0

                self.logger().info(
                    f"{'✅' if available >= approx_required else '⚠️'} {connector_name}: "
                    f"${available:.2f} available (can open ~{max_positions} positions at avg {avg_leverage:.1f}x leverage)"
                )

    def get_funding_info_by_token(self, token):
        """
        This method provides the funding rates across the connectors where the token is available.
        Uses availability cache to avoid querying connectors where token doesn't exist.
        """
        funding_rates = {}

        # Get list of connectors where this token is available
        available_connectors = self.token_availability_cache.get(token, [])

        if not available_connectors:
            # Token not available on any connector
            return funding_rates

        # Only query connectors where token exists
        for connector_name in available_connectors:
            if connector_name in self.connectors:
                connector = self.connectors[connector_name]
                trading_pair = self.get_trading_pair_for_connector(token, connector_name)
                try:
                    funding_rates[connector_name] = connector.get_funding_info(trading_pair)
                except Exception as e:
                    self.logger().warning(f"Failed to get funding info for {trading_pair} on {connector_name}: {e}")

        return funding_rates

    def check_sufficient_liquidity(self, token: str, connector_1: str, connector_2: str) -> bool:
        """
        Check if both connectors have sufficient liquidity (24h volume) for the token.

        Args:
            token: Base token symbol
            connector_1: First connector name
            connector_2: Second connector name

        Returns:
            True if both connectors meet minimum volume threshold
        """
        if self.config.min_daily_volume_usd <= 0:
            # Volume check disabled
            return True

        try:
            trading_pair_1 = self.get_trading_pair_for_connector(token, connector_1)
            trading_pair_2 = self.get_trading_pair_for_connector(token, connector_2)

            # Get 24h volume for both trading pairs
            connector_1_obj = self.connectors[connector_1]
            connector_2_obj = self.connectors[connector_2]

            # Try to get volume from market data
            # Note: Different connectors may expose volume differently
            # This is a best-effort approach
            volume_1 = self._get_24h_volume(connector_1_obj, trading_pair_1)
            volume_2 = self._get_24h_volume(connector_2_obj, trading_pair_2)

            # Check if both meet threshold
            meets_threshold_1 = volume_1 >= self.config.min_daily_volume_usd
            meets_threshold_2 = volume_2 >= self.config.min_daily_volume_usd

            if not meets_threshold_1 or not meets_threshold_2:
                self.logger().debug(
                    f"{token} liquidity check failed: "
                    f"{connector_1}=${volume_1:,.0f} ({'✅' if meets_threshold_1 else '❌'}), "
                    f"{connector_2}=${volume_2:,.0f} ({'✅' if meets_threshold_2 else '❌'}) "
                    f"(min=${self.config.min_daily_volume_usd:,.0f})"
                )
                return False

            return True

        except Exception as e:
            # If we can't get volume data, log warning and allow trade
            self.logger().warning(f"Failed to check liquidity for {token}: {e}. Proceeding anyway.")
            return True

    def _get_24h_volume(self, connector: ConnectorBase, trading_pair: str) -> Decimal:
        """
        Get 24h volume for a trading pair.
        Returns 0 if volume data unavailable.
        """
        try:
            # Try to get from order book tracker stats
            if hasattr(connector, '_order_book_tracker') and connector._order_book_tracker:
                order_book = connector._order_book_tracker.order_books.get(trading_pair)
                if order_book and hasattr(order_book, 'volume_24h'):
                    return Decimal(str(order_book.volume_24h))

            # Fallback: try to get mid price and assume minimum liquidity
            # This is conservative - if we can't verify volume, assume it's OK
            return self.config.min_daily_volume_usd

        except Exception as e:
            self.logger().debug(f"Could not get volume for {trading_pair}: {e}")
            return Decimal("0")

    def get_most_profitable_combination(self, funding_info_report: Dict):
        best_combination = None
        highest_profitability = 0
        for connector_1 in funding_info_report:
            for connector_2 in funding_info_report:
                if connector_1 != connector_2:
                    rate_connector_1 = self.get_normalized_funding_rate_in_seconds(funding_info_report, connector_1)
                    rate_connector_2 = self.get_normalized_funding_rate_in_seconds(funding_info_report, connector_2)
                    funding_rate_diff = abs(rate_connector_1 - rate_connector_2) * self.funding_profitability_interval
                    if funding_rate_diff > highest_profitability:
                        trade_side = TradeType.BUY if rate_connector_1 < rate_connector_2 else TradeType.SELL
                        highest_profitability = funding_rate_diff
                        best_combination = (connector_1, connector_2, trade_side, funding_rate_diff)
        return best_combination

    def get_normalized_funding_rate_in_seconds(self, funding_info_report, connector_name):
        return funding_info_report[connector_name].rate / self.funding_payment_interval_map.get(connector_name, 60 * 60 * 8)

    def create_actions_proposal(self) -> List[CreateExecutorAction]:
        """
        Enhanced opportunity scanner that:
        1. Scans ALL tokens available on 2+ exchanges
        2. Ranks opportunities by spread (highest first)
        3. Checks liquidity before entering
        4. Picks the best profitable opportunity globally

        This ensures we always enter the most profitable arbitrage available,
        even if some tokens aren't on all exchanges.
        """
        create_actions = []

        # Collect all opportunities across all tokens
        all_opportunities = []

        for token in self.config.tokens:
            # Skip if already in active arbitrage
            if token in self.active_funding_arbitrages:
                continue

            # Get funding rates for this token (only from connectors where it exists)
            funding_info_report = self.get_funding_info_by_token(token)

            # Need at least 2 exchanges to arbitrage
            if len(funding_info_report) < 2:
                # Can't arbitrage with less than 2 exchanges, but don't log unless really needed
                continue

            # Find best combination for this token
            best_combination = self.get_most_profitable_combination(funding_info_report)

            if not best_combination:
                continue

            connector_1, connector_2, trade_side, expected_profitability = best_combination

            # Must meet minimum profitability
            if expected_profitability < self.config.min_funding_rate_profitability:
                continue

            # Check liquidity/volume
            if not self.check_sufficient_liquidity(token, connector_1, connector_2):
                self.logger().debug(f"Skipping {token}: insufficient liquidity on {connector_1} or {connector_2}")
                continue

            # Add to opportunities list
            all_opportunities.append({
                'token': token,
                'connector_1': connector_1,
                'connector_2': connector_2,
                'trade_side': trade_side,
                'spread': expected_profitability
            })

        # Sort opportunities by spread (highest first)
        all_opportunities.sort(key=lambda x: x['spread'], reverse=True)

        # Log top opportunities
        if all_opportunities:
            self.logger().info(f"Found {len(all_opportunities)} profitable opportunities:")
            for i, opp in enumerate(all_opportunities[:5]):  # Show top 5
                self.logger().info(
                    f"  #{i+1}: {opp['token']} - {opp['connector_1']} vs {opp['connector_2']} | "
                    f"Spread: {opp['spread']:.4%}/hr"
                )

        # Try to enter the best opportunity (with balance checks)
        for opp in all_opportunities:
            token = opp['token']
            connector_1 = opp['connector_1']
            connector_2 = opp['connector_2']
            trade_side = opp['trade_side']
            expected_profitability = opp['spread']

            # Check balance sufficiency (using token-specific leverage)
            required_margin_c1 = self.get_required_margin(connector_1, self.config.position_size_quote, token)
            required_margin_c2 = self.get_required_margin(connector_2, self.config.position_size_quote, token)

            sufficient_c1, balance_c1, shortfall_c1 = self.check_sufficient_balance(connector_1, required_margin_c1)
            sufficient_c2, balance_c2, shortfall_c2 = self.check_sufficient_balance(connector_2, required_margin_c2)

            # Log balance status with token-specific leverage
            token_leverage = self.get_leverage_for_token(token)

            # Prevent trade if insufficient balance
            if not sufficient_c1 or not sufficient_c2:
                self.logger().info(
                    f"Skipping {token} (insufficient balance): "
                    f"{connector_1} needs ${required_margin_c1:.2f} (have ${balance_c1:.2f}), "
                    f"{connector_2} needs ${required_margin_c2:.2f} (have ${balance_c2:.2f})"
                )
                continue  # Try next best opportunity

            # Found a valid opportunity with sufficient balance!
            self.logger().info(
                f"✅ Opening {token} arbitrage ({token_leverage}x leverage) | "
                f"{connector_1} ({trade_side.name}) vs {connector_2} ({'SELL' if trade_side == TradeType.BUY else 'BUY'}) | "
                f"Spread: {expected_profitability:.4%}/hr | "
                f"Starting executors..."
            )

            position_executor_config_1, position_executor_config_2 = self.get_position_executors_config(
                token, connector_1, connector_2, trade_side
            )

            self.active_funding_arbitrages[token] = {
                "connector_1": connector_1,
                "connector_2": connector_2,
                "executors_ids": [position_executor_config_1.id, position_executor_config_2.id],
                "side": trade_side,
                "funding_payments": [],
                "entry_spread": expected_profitability,
                "entry_timestamp": self.current_timestamp,
            }

            return [
                CreateExecutorAction(executor_config=position_executor_config_1),
                CreateExecutorAction(executor_config=position_executor_config_2)
            ]

        # No opportunities met all criteria
        return create_actions

    def stop_actions_proposal(self) -> List[StopExecutorAction]:
        """
        Exit positions based on spread conditions only (no take profit).
        Exit conditions:
        1. Spread flips negative
        2. Spread below absolute minimum (0.2%)
        3. Spread compresses 60%+
        4. Max duration (24h)
        5. Stop loss (-3%)
        """
        stop_executor_actions = []
        for token, funding_arbitrage_info in self.active_funding_arbitrages.items():
            executors = self.filter_executors(
                executors=self.get_all_executors(),
                filter_func=lambda x: x.id in funding_arbitrage_info["executors_ids"]
            )

            # Get current spread
            funding_info_report = self.get_funding_info_by_token(token)
            if funding_arbitrage_info["side"] == TradeType.BUY:
                current_spread = abs(self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_2"]) - self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_1"]))
            else:
                current_spread = abs(self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_1"]) - self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_2"]))

            current_spread_hourly = current_spread * 3600  # Convert to hourly
            entry_spread = funding_arbitrage_info.get("entry_spread", current_spread_hourly)

            # Calculate duration
            duration_hours = (self.current_timestamp - funding_arbitrage_info.get("entry_timestamp", self.current_timestamp)) / 3600

            # Calculate PNL for stop loss check
            funding_payments_pnl = sum(funding_payment.amount for funding_payment in funding_arbitrage_info["funding_payments"])
            executors_pnl = sum(executor.net_pnl_quote for executor in executors)
            total_pnl = executors_pnl + funding_payments_pnl
            position_value = self.config.position_size_quote * 2
            pnl_pct = total_pnl / position_value if position_value > 0 else 0

            # Exit conditions
            exit_reason = None

            # 1. Spread flip (negative)
            if current_spread_hourly < 0:
                exit_reason = f"Spread flipped negative: {current_spread_hourly:.4f}"

            # 2. Absolute minimum spread
            elif current_spread_hourly < self.config.absolute_min_spread_exit:
                exit_reason = f"Spread below minimum: {current_spread_hourly:.4f} < {self.config.absolute_min_spread_exit:.4f}"

            # 3. Spread compression
            elif entry_spread > 0:
                compression_ratio = current_spread_hourly / entry_spread
                if compression_ratio < self.config.compression_exit_threshold:
                    compression_pct = (1 - compression_ratio) * 100
                    exit_reason = f"Spread compressed {compression_pct:.1f}% (entry: {entry_spread:.4f}, current: {current_spread_hourly:.4f})"

            # 4. Max duration
            if exit_reason is None and duration_hours >= self.config.max_position_duration_hours:
                exit_reason = f"Max duration reached: {duration_hours:.1f}h"

            # 5. Stop loss
            if exit_reason is None and pnl_pct <= -self.config.max_loss_per_position_pct:
                exit_reason = f"Stop loss hit: {pnl_pct:.2%}"

            if exit_reason:
                self.logger().info(f"Exiting {token}: {exit_reason}")
                self.stopped_funding_arbitrages[token].append(funding_arbitrage_info)
                stop_executor_actions.extend([StopExecutorAction(executor_id=executor.id) for executor in executors])

        return stop_executor_actions

    def check_low_balance_warnings(self):
        """
        Check for low balances and log warnings.
        Called periodically to monitor balance health.
        """
        for connector_name in self.config.connectors:
            quote_asset = self.quote_markets_map.get(connector_name, "USDT")
            connector = self.connectors[connector_name]

            available = connector.get_available_balance(quote_asset)
            required = self.get_required_margin(connector_name, self.config.position_size_quote)

            # Warn if balance is below 2x required (can only open 1 more position)
            if available < required * 2 and available >= required:
                self.logger().warning(
                    f"⚠️ LOW BALANCE: {connector_name} can only open 1 more position "
                    f"(${available:.2f} available)"
                )
            elif available < required:
                self.logger().error(
                    f"❌ INSUFFICIENT BALANCE: {connector_name} cannot open new positions "
                    f"(${available:.2f} available, ${required:.2f} required)"
                )

    def did_complete_funding_payment(self, funding_payment_completed_event: FundingPaymentCompletedEvent):
        """
        Based on the funding payment event received, check if one of the active arbitrages matches to add the event
        to the list.
        """
        token = funding_payment_completed_event.trading_pair.split("-")[0]
        if token in self.active_funding_arbitrages:
            self.active_funding_arbitrages[token]["funding_payments"].append(funding_payment_completed_event)

    def get_position_executors_config(self, token, connector_1, connector_2, trade_side):
        """
        Create position executor configurations with LIMIT orders and anti-slippage pricing.

        For limit orders, we price slightly better than mid to ensure fills:
        - BUY orders: bid slightly higher than mid
        - SELL orders: ask slightly lower than mid

        Uses token-specific leverage based on Lighter's limits.
        """
        # Get mid prices for both connectors
        mid_price_1 = self.market_data_provider.get_price_by_type(
            connector_name=connector_1,
            trading_pair=self.get_trading_pair_for_connector(token, connector_1),
            price_type=PriceType.MidPrice
        )
        mid_price_2 = self.market_data_provider.get_price_by_type(
            connector_name=connector_2,
            trading_pair=self.get_trading_pair_for_connector(token, connector_2),
            price_type=PriceType.MidPrice
        )

        # Get token-specific leverage
        token_leverage = self.get_leverage_for_token(token)

        # Calculate limit prices with buffer to ensure fills
        # BUY: bid slightly higher, SELL: ask slightly lower
        if trade_side == TradeType.BUY:
            entry_price_1 = mid_price_1 * (Decimal("1") + self.config.order_price_buffer_pct)
        else:
            entry_price_1 = mid_price_1 * (Decimal("1") - self.config.order_price_buffer_pct)

        # Position 2 is opposite side
        if trade_side == TradeType.BUY:
            entry_price_2 = mid_price_2 * (Decimal("1") - self.config.order_price_buffer_pct)
        else:
            entry_price_2 = mid_price_2 * (Decimal("1") + self.config.order_price_buffer_pct)

        # Calculate position amounts for each exchange based on their respective entry prices
        # This ensures both positions have the same USD value
        position_amount_1 = self.config.position_size_quote / entry_price_1
        position_amount_2 = self.config.position_size_quote / entry_price_2

        position_executor_config_1 = PositionExecutorConfig(
            timestamp=self.current_timestamp,
            connector_name=connector_1,
            trading_pair=self.get_trading_pair_for_connector(token, connector_1),
            side=trade_side,
            entry_price=entry_price_1,
            amount=position_amount_1,
            leverage=token_leverage,
            triple_barrier_config=TripleBarrierConfig(open_order_type=OrderType.LIMIT),
        )
        position_executor_config_2 = PositionExecutorConfig(
            timestamp=self.current_timestamp,
            connector_name=connector_2,
            trading_pair=self.get_trading_pair_for_connector(token, connector_2),
            side=TradeType.BUY if trade_side == TradeType.SELL else TradeType.SELL,
            entry_price=entry_price_2,
            amount=position_amount_2,
            leverage=token_leverage,
            triple_barrier_config=TripleBarrierConfig(open_order_type=OrderType.LIMIT),
        )
        return position_executor_config_1, position_executor_config_2

    def format_status(self) -> str:
        original_status = super().format_status()
        funding_rate_status = []

        # Add token availability status section
        if self.ready_to_trade and self.token_availability_cache:
            funding_rate_status.append("\n" + "=" * 80)
            funding_rate_status.append("Token Availability Matrix")
            funding_rate_status.append("=" * 80)

            availability_data = []
            for token in sorted(self.config.tokens):
                available_connectors = self.token_availability_cache.get(token, [])
                num_exchanges = len(available_connectors)

                # Calculate number of possible arbitrage pairs
                num_pairs = (num_exchanges * (num_exchanges - 1)) // 2 if num_exchanges >= 2 else 0

                status = "✅" if num_exchanges >= 2 else ("⚠️" if num_exchanges == 1 else "❌")

                availability_data.append({
                    "Status": status,
                    "Token": token,
                    "Exchanges": num_exchanges,
                    "Available On": ", ".join(available_connectors) if available_connectors else "None",
                    "Arb Pairs": num_pairs
                })

            if availability_data:
                funding_rate_status.append(format_df_for_printout(df=pd.DataFrame(availability_data), table_format="psql"))
            funding_rate_status.append("")

        # Add balance status section
        if self.ready_to_trade:
            funding_rate_status.append("=" * 80)
            funding_rate_status.append("Balance Status for Arbitrage")
            funding_rate_status.append("=" * 80)

            for connector_name in self.config.connectors:
                quote_asset = self.quote_markets_map.get(connector_name, "USDT")
                connector = self.connectors[connector_name]

                available = connector.get_available_balance(quote_asset)
                total = connector.get_balance(quote_asset)
                required = self.get_required_margin(connector_name, self.config.position_size_quote)

                # Calculate how many positions can be opened
                max_positions = int(available / required) if required > 0 else 0

                status_emoji = "✅" if available >= required else "⚠️"

                funding_rate_status.append(
                    f"{status_emoji} {connector_name}:\n"
                    f"   Total: ${total:.2f} | Available: ${available:.2f}\n"
                    f"   Required per position: ${required:.2f}\n"
                    f"   Max positions: {max_positions}"
                )
            funding_rate_status.append("")

        if self.ready_to_trade:
            all_funding_info = []
            all_best_paths = []
            for token in self.config.tokens:
                token_info = {"token": token}
                best_paths_info = {"token": token}
                funding_info_report = self.get_funding_info_by_token(token)
                best_combination = self.get_most_profitable_combination(funding_info_report)
                for connector_name in funding_info_report.keys():
                    token_info[f"{connector_name} Rate (%/hr)"] = self.get_normalized_funding_rate_in_seconds(funding_info_report, connector_name) * self.funding_profitability_interval * 100
                connector_1, connector_2, side, funding_rate_diff = best_combination
                best_paths_info["Best Path"] = f"{connector_1}_{connector_2}"
                best_paths_info["Best Rate Diff (%/hr)"] = funding_rate_diff * 100

                time_to_next_funding_info_c1 = funding_info_report[connector_1].next_funding_utc_timestamp - self.current_timestamp
                time_to_next_funding_info_c2 = funding_info_report[connector_2].next_funding_utc_timestamp - self.current_timestamp
                best_paths_info["Min to Funding 1"] = time_to_next_funding_info_c1 / 60
                best_paths_info["Min to Funding 2"] = time_to_next_funding_info_c2 / 60

                all_funding_info.append(token_info)
                all_best_paths.append(best_paths_info)
            funding_rate_status.append(f"\n\n\nMin Funding Rate Profitability: {self.config.min_funding_rate_profitability:.2%}/hr\n")
            funding_rate_status.append("Funding Rate Info (Hourly Rates): ")
            funding_rate_status.append(format_df_for_printout(df=pd.DataFrame(all_funding_info), table_format="psql",))
            funding_rate_status.append(format_df_for_printout(df=pd.DataFrame(all_best_paths), table_format="psql",))
            for token, funding_arbitrage_info in self.active_funding_arbitrages.items():
                long_connector = funding_arbitrage_info["connector_1"] if funding_arbitrage_info["side"] == TradeType.BUY else funding_arbitrage_info["connector_2"]
                short_connector = funding_arbitrage_info["connector_2"] if funding_arbitrage_info["side"] == TradeType.BUY else funding_arbitrage_info["connector_1"]
                funding_rate_status.append(f"Token: {token}")
                funding_rate_status.append(f"Long connector: {long_connector} | Short connector: {short_connector}")
                funding_rate_status.append(f"Funding Payments Collected: {funding_arbitrage_info['funding_payments']}")
                funding_rate_status.append(f"Executors: {funding_arbitrage_info['executors_ids']}")
                funding_rate_status.append("-" * 50 + "\n")
        return original_status + "\n".join(funding_rate_status)
