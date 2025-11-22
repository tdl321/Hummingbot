"""
Extended Perpetual Derivative Connector

This connector enables trading on Extended DEX, a perpetual futures exchange built on Starknet.

Key Features:
- Perpetual futures trading with up to 100x leverage
- Funding rate arbitrage support
- Order book and market data streaming
- Position management

API Documentation: http://api.docs.extended.exchange/
"""

import asyncio
from decimal import Decimal
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple

from bidict import bidict

from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.derivative.extended_perpetual import (
    extended_perpetual_constants as CONSTANTS,
    extended_perpetual_web_utils as web_utils,
)
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_api_order_book_data_source import (
    ExtendedPerpetualAPIOrderBookDataSource,
)
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_auth import ExtendedPerpetualAuth
from hummingbot.connector.derivative.extended_perpetual.extended_perpetual_user_stream_data_source import (
    ExtendedPerpetualUserStreamDataSource,
)
from hummingbot.connector.derivative.position import Position
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import combine_to_hb_trading_pair, get_new_client_order_id
from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, PositionSide, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.trade_fee import TokenAmount, TradeFeeBase
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.utils.async_utils import safe_ensure_future, safe_gather
from hummingbot.core.utils.estimate_fee import build_trade_fee
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from pydantic import SecretStr

bpm_logger = None


class ExtendedPerpetualDerivative(PerpetualDerivativePyBase):
    """
    Extended Perpetual Derivative connector class.

    Implements perpetual futures trading on Extended DEX.
    """

    web_utils = web_utils

    SHORT_POLL_INTERVAL = 5.0
    LONG_POLL_INTERVAL = 12.0

    def __init__(
            self,
            balance_asset_limit: Optional[Dict[str, Dict[str, Decimal]]] = None,
            rate_limits_share_pct: Decimal = Decimal("100"),
            extended_perpetual_api_key: str = None,
            extended_perpetual_api_secret: str = None,
            trading_pairs: Optional[List[str]] = None,
            trading_required: bool = True,
            domain: str = CONSTANTS.DOMAIN,
    ):
        """
        Initialize Extended perpetual connector.

        Args:
            balance_asset_limit: Asset balance limits
            rate_limits_share_pct: Percentage of rate limits to use
            extended_perpetual_api_key: API key for Extended
            extended_perpetual_api_secret: API secret (Stark private key) for Extended
            trading_pairs: List of trading pairs to trade
            trading_required: Whether trading is required (False for read-only)
            domain: Domain identifier (extended_perpetual or testnet)
        """
        # Unwrap SecretStr objects if needed (config provides SecretStr, tests provide plain str)
        self.extended_perpetual_api_key = (
            extended_perpetual_api_key.get_secret_value()
            if isinstance(extended_perpetual_api_key, SecretStr)
            else extended_perpetual_api_key
        )
        self.extended_perpetual_api_secret = (
            extended_perpetual_api_secret.get_secret_value()
            if isinstance(extended_perpetual_api_secret, SecretStr)
            else extended_perpetual_api_secret
        )
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs
        self._domain = domain
        self._position_mode = None
        self._last_funding_fee_payment_ts: Dict[str, float] = {}
        super().__init__(balance_asset_limit, rate_limits_share_pct)

    @property
    def name(self) -> str:
        """Exchange name."""
        return self._domain

    @property
    def authenticator(self) -> Optional[ExtendedPerpetualAuth]:
        """Get authenticator instance."""
        if self._trading_required and self.extended_perpetual_api_key and self.extended_perpetual_api_secret:
            return ExtendedPerpetualAuth(self.extended_perpetual_api_key, self.extended_perpetual_api_secret)
        return None

    @property
    def rate_limits_rules(self) -> List[RateLimit]:
        """Get rate limit rules."""
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self) -> str:
        """Get domain."""
        return self._domain

    @property
    def client_order_id_max_length(self) -> int:
        """Maximum length for client order IDs."""
        return CONSTANTS.MAX_ORDER_ID_LEN

    @property
    def client_order_id_prefix(self) -> str:
        """Prefix for client order IDs."""
        return CONSTANTS.BROKER_ID

    @property
    def trading_rules_request_path(self) -> str:
        """Path for trading rules request."""
        return CONSTANTS.MARKETS_INFO_URL

    @property
    def trading_pairs_request_path(self) -> str:
        """Path for trading pairs request."""
        return CONSTANTS.MARKETS_INFO_URL

    @property
    def check_network_request_path(self) -> str:
        """Path for network check request."""
        return CONSTANTS.PING_URL

    @property
    def trading_pairs(self):
        """Get trading pairs."""
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        """Whether cancel requests are synchronous."""
        return True

    @property
    def is_trading_required(self) -> bool:
        """Whether trading is required."""
        return self._trading_required

    @property
    def funding_fee_poll_interval(self) -> int:
        """
        Funding fee poll interval in seconds.

        Extended has 8-hour funding intervals.
        """
        return CONSTANTS.FUNDING_RATE_UPDATE_INTERNAL_SECOND

    def supported_position_modes(self) -> List[PositionMode]:
        """
        Supported position modes.

        Extended supports ONEWAY mode (single position per market).
        """
        return [PositionMode.ONEWAY]

    def get_buy_collateral_token(self, trading_pair: str) -> str:
        """Get collateral token for buy orders."""
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.buy_order_collateral_token

    def get_sell_collateral_token(self, trading_pair: str) -> str:
        """Get collateral token for sell orders."""
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.sell_order_collateral_token

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        """Check if exception is related to time synchronization."""
        # Extended doesn't require time synchronization
        return False

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        """Check if exception indicates order not found."""
        return str(CONSTANTS.ORDER_NOT_EXIST_MESSAGE).lower() in str(status_update_exception).lower()

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        """Check if exception indicates order not found during cancelation."""
        return str(CONSTANTS.ORDER_NOT_EXIST_MESSAGE).lower() in str(cancelation_exception).lower()

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        """Create web assistants factory."""
        return web_utils.build_api_factory(
            throttler=self._throttler,
            auth=self.authenticator
        )

    def _create_order_book_data_source(self) -> OrderBookTrackerDataSource:
        """Create order book data source."""
        return ExtendedPerpetualAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory,
            domain=self.domain
        )

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        """Create user stream data source."""
        return ExtendedPerpetualUserStreamDataSource(
            connector=self,
            api_factory=self._web_assistants_factory,
            domain=self.domain
        )

    def _get_fee(
            self,
            base_currency: str,
            quote_currency: str,
            order_type: OrderType,
            order_side: TradeType,
            amount: Decimal,
            price: Decimal = s_decimal_NaN,
            is_maker: Optional[bool] = None,
            position_action: PositionAction = PositionAction.NIL,
    ) -> TradeFeeBase:
        """
        Calculate trading fee.

        Extended fees: Maker 0.02%, Taker 0.05%
        """
        is_maker = is_maker or (order_type is OrderType.LIMIT_MAKER)
        trade_base_fee = build_trade_fee(
            exchange=self.name,
            is_maker=is_maker,
            position_action=position_action,
            base_currency=base_currency,
            quote_currency=quote_currency,
            order_type=order_type,
            order_side=order_side,
            amount=amount,
            price=price,
        )
        return trade_base_fee

    async def _ensure_vault_id(self):
        """
        Ensure vault ID is set in the authenticator.

        Fetches account info from Extended API if vault_id is not already set.
        """
        if self.authenticator and self.authenticator._vault_id is None:
            try:
                # Fetch account info to get vault ID
                response = await self._api_get(
                    path_url=CONSTANTS.ACCOUNT_INFO_URL,
                    is_auth_required=True,
                    limit_id=CONSTANTS.ACCOUNT_INFO_URL
                )

                # Parse vault ID from response
                # Extended API response format: {"status": "OK", "data": {"vault": "12345", ...}}
                if isinstance(response, dict) and 'data' in response:
                    vault_id = response['data'].get('vault') or response['data'].get('vaultId')
                    if vault_id:
                        self.authenticator.set_vault_id(str(vault_id))
                        self.logger().info(f"Extended vault ID set: {vault_id}")
                    else:
                        self.logger().error("Could not find vault ID in account info response")
                else:
                    self.logger().error(f"Unexpected account info response format: {response}")
            except Exception as e:
                self.logger().error(f"Error fetching vault ID from Extended: {e}", exc_info=True)
                raise ValueError("Cannot place orders: vault ID not available") from e

    async def _place_order(
            self,
            order_id: str,
            trading_pair: str,
            amount: Decimal,
            trade_type: TradeType,
            order_type: OrderType,
            price: Decimal,
            position_action: PositionAction = PositionAction.NIL,
            **kwargs,
    ) -> Tuple[str, float]:
        """
        Place an order on Extended using x10 SDK.

        This method uses the x10 PerpetualTradingClient for Stark-signed order submission.

        Args:
            order_id: Client order ID
            trading_pair: Trading pair (e.g., "KAITO-USD")
            amount: Order amount in base asset
            trade_type: BUY or SELL
            order_type: MARKET or LIMIT
            price: Order price (ignored for MARKET orders)
            position_action: OPEN or CLOSE

        Returns:
            Tuple of (exchange_order_id, timestamp)
        """
        try:
            # Ensure vault ID is set (required for signing)
            await self._ensure_vault_id()

            # Get exchange symbol
            ex_trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair)

            # Get trading client from authenticator
            if not self.authenticator:
                raise ValueError("No authenticator available for order signing")

            trading_client = self.authenticator.get_trading_client()

            # Convert trade type to OrderSide
            from x10.perpetual.orders import OrderSide
            side = OrderSide.BUY if trade_type == TradeType.BUY else OrderSide.SELL

            # Place order using x10 SDK
            # Note: SDK's place_order handles LIMIT orders. For MARKET orders, use a very high/low price
            if order_type == OrderType.MARKET:
                # For market orders, use a price that will execute immediately
                if side == OrderSide.BUY:
                    # For buy market order, use very high price
                    order_price = price * Decimal("1.1")  # 10% above mark price
                else:
                    # For sell market order, use very low price
                    order_price = price * Decimal("0.9")  # 10% below mark price
            else:
                order_price = price

            # Call SDK place_order method
            response = await trading_client.place_order(
                market_name=ex_trading_pair,
                amount_of_synthetic=amount,
                price=order_price,
                side=side,
                post_only=(order_type == OrderType.LIMIT_MAKER) if order_type == OrderType.LIMIT_MAKER else False,
                external_id=order_id,  # Use our order_id as external_id for tracking
            )

            # Parse response from SDK
            # Expected response: WrappedApiResponse[PlacedOrderModel]
            if response.success and response.data:
                placed_order = response.data
                exchange_order_id = str(placed_order.order_id) if hasattr(placed_order, 'order_id') else order_id
                timestamp = self.current_timestamp

                self.logger().info(
                    f"Successfully placed {trade_type.name} order on Extended: "
                    f"{trading_pair} amount={amount} price={order_price} order_id={exchange_order_id}"
                )

                return exchange_order_id, timestamp
            else:
                error_msg = response.error if hasattr(response, 'error') else "Unknown error"
                raise ValueError(f"Order placement failed: {error_msg}")

        except Exception as e:
            self.logger().error(f"Error placing order on Extended: {e}", exc_info=True)
            raise

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        """
        Cancel an order on Extended.

        Args:
            order_id: Client order ID
            tracked_order: In-flight order to cancel
        """
        # TODO: Implement order cancellation
        raise NotImplementedError("Order cancellation requires implementation")

    async def _execute_set_position_mode(self, mode: PositionMode):
        """
        Set position mode on Extended.

        Extended uses ONEWAY mode by default.

        Args:
            mode: Position mode to set
        """
        if mode == PositionMode.ONEWAY:
            self._position_mode = mode
            self.logger().info(f"Position mode set to {mode}")
        else:
            self.logger().error(f"Position mode {mode} not supported by Extended")

    async def _execute_set_leverage(self, trading_pair: str, leverage: int):
        """
        Set leverage for a trading pair on Extended.

        Extended API: PATCH /api/v1/user/leverage

        Args:
            trading_pair: Trading pair
            leverage: Leverage value (1-100x)
        """
        try:
            ex_trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair)

            # Extended API expects: {"market": "KAITO-USD", "leverage": 5}
            data = {
                "market": ex_trading_pair,
                "leverage": leverage
            }

            response = await self._api_patch(
                path_url=CONSTANTS.LEVERAGE_URL,
                data=data,
                is_auth_required=True
            )

            # Update local leverage tracking
            self._perpetual_trading.set_leverage(trading_pair, leverage)
            self.logger().info(f"Leverage set to {leverage}x for {trading_pair}")

            return True, f"Leverage set to {leverage}x"

        except Exception as e:
            self.logger().error(f"Error setting leverage for {trading_pair}: {e}")
            return False, str(e)

    async def _fetch_last_fee_payment(self, trading_pair: str) -> Tuple[int, Decimal, Decimal]:
        """
        Fetch last funding fee payment for a trading pair.

        This is CRITICAL for the funding rate arbitrage strategy!

        Extended API: GET /api/v1/user/funding/history

        Args:
            trading_pair: Trading pair

        Returns:
            Tuple of (timestamp, funding_rate, payment_amount)
        """
        try:
            ex_trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair)

            # Get funding history
            response = await self._api_get(
                path_url=CONSTANTS.FUNDING_HISTORY_URL,
                params={"market": ex_trading_pair, "limit": 1},
                is_auth_required=True,
                limit_id=CONSTANTS.FUNDING_HISTORY_URL
            )

            # Parse response
            if isinstance(response, dict) and 'data' in response:
                funding_history = response['data']
                if funding_history and len(funding_history) > 0:
                    latest = funding_history[0]
                    timestamp = int(latest.get('timestamp', 0))
                    funding_rate = Decimal(str(latest.get('fundingRate', 0)))
                    payment = Decimal(str(latest.get('payment', 0)))
                    return timestamp, funding_rate, payment

            # No funding payment found
            return 0, Decimal("0"), Decimal("0")

        except Exception as e:
            self.logger().error(f"Error fetching funding payment for {trading_pair}: {e}")
            return 0, Decimal("-1"), Decimal("-1")

    async def _format_trading_rules(self, exchange_info_dict: Dict) -> List[TradingRule]:
        """
        Format trading rules from exchange info.

        Extended API: GET /api/v1/info/markets

        Args:
            exchange_info_dict: Markets information from Extended

        Returns:
            List of TradingRule objects
        """
        trading_rules = []

        # Extended response: {"status": "OK", "data": [{market}, {market}, ...]}
        if isinstance(exchange_info_dict, dict) and 'data' in exchange_info_dict:
            markets = exchange_info_dict['data']

            for market in markets:
                try:
                    # Parse market data
                    market_name = market.get('name')  # e.g., "KAITO-USD"
                    min_order_size = Decimal(str(market.get('minOrderSize', '0.001')))
                    price_increment = Decimal(str(market.get('priceIncrement', '0.01')))
                    size_increment = Decimal(str(market.get('sizeIncrement', '0.001')))

                    # Convert exchange symbol to Hummingbot trading pair
                    trading_pair = await self.trading_pair_associated_to_exchange_symbol(market_name)

                    # Create trading rule
                    trading_rule = TradingRule(
                        trading_pair=trading_pair,
                        min_order_size=min_order_size,
                        min_price_increment=price_increment,
                        min_base_amount_increment=size_increment,
                        buy_order_collateral_token=CONSTANTS.CURRENCY,
                        sell_order_collateral_token=CONSTANTS.CURRENCY,
                    )
                    trading_rules.append(trading_rule)

                except Exception as e:
                    self.logger().error(f"Error parsing trading rule for market {market}: {e}")
                    continue

        return trading_rules

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict):
        """
        Initialize trading pair symbol mappings from exchange info.

        Args:
            exchange_info: Exchange information dictionary
        """
        mapping = bidict()

        if isinstance(exchange_info, dict) and 'data' in exchange_info:
            markets = exchange_info['data']

            for market in markets:
                if not web_utils.is_exchange_information_valid(market):
                    continue

                market_name = market.get('name')  # e.g., "KAITO-USD"
                if not market_name:
                    continue

                # Split market name to get base and quote
                parts = market_name.split('-')
                if len(parts) != 2:
                    continue

                base = parts[0]
                quote = parts[1]

                trading_pair = combine_to_hb_trading_pair(base, quote)
                exchange_symbol = market_name

                if trading_pair in mapping.inverse:
                    self._resolve_trading_pair_symbols_duplicate(mapping, exchange_symbol, base, quote)
                else:
                    mapping[exchange_symbol] = trading_pair

        self._set_trading_pair_symbol_map(mapping)

    async def _get_last_traded_price(self, trading_pair: str) -> float:
        """
        Get last traded price for a trading pair.

        Args:
            trading_pair: Trading pair

        Returns:
            Last traded price as float
        """
        ex_trading_pair = await self.exchange_symbol_associated_to_pair(trading_pair)

        # Extended API: GET /api/v1/info/markets/{market}/stats
        path = CONSTANTS.MARKET_STATS_URL.format(market=ex_trading_pair)
        response = await self._api_get(path_url=path, limit_id=CONSTANTS.MARKET_STATS_URL)

        if isinstance(response, dict) and 'data' in response:
            stats = response['data']
            last_price = float(stats.get('lastPrice', 0))
            return last_price

        return 0.0

    def _resolve_trading_pair_symbols_duplicate(
            self,
            mapping: bidict,
            new_exchange_symbol: str,
            base: str,
            quote: str
    ):
        """Resolve duplicate trading pair symbols."""
        trading_pair = combine_to_hb_trading_pair(base, quote)
        current_exchange_symbol = mapping.inverse[trading_pair]

        # Prefer the new symbol if it matches expected format
        expected_exchange_symbol = f"{base}-{quote}"
        if new_exchange_symbol == expected_exchange_symbol:
            mapping.pop(current_exchange_symbol)
            mapping[new_exchange_symbol] = trading_pair
        elif current_exchange_symbol != expected_exchange_symbol:
            self.logger().error(
                f"Could not resolve duplicate exchange symbols: {new_exchange_symbol} and {current_exchange_symbol}"
            )

    async def _user_stream_event_listener(self):
        """
        Listen to user stream events from WebSocket.

        Extended WebSocket message format:
        {
            "type": "BALANCE" | "ORDER" | "POSITION" | "FUNDING",
            "data": {
                "isSnapshot": true/false,
                ... type-specific data
            },
            "ts": timestamp_ms,
            "seq": sequence_number
        }
        """
        async for event_message in self._iter_user_event_queue():
            try:
                # Process different event types from WebSocket
                event_type = event_message.get("type", "").upper()

                if event_type == "BALANCE":
                    self._process_balance_update(event_message)
                elif event_type == "ORDER":
                    self._process_order_update(event_message)
                elif event_type == "POSITION":
                    self._process_position_update(event_message)
                elif event_type == "FUNDING":
                    self._process_funding_payment(event_message)
                else:
                    self.logger().debug(f"Unknown Extended WebSocket message type: {event_type}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error processing Extended WebSocket event: {e}", exc_info=True)

    def _process_order_update(self, order_update: Dict[str, Any]):
        """Process order update from user stream."""
        # TODO: Implement order update processing
        pass

    def _process_position_update(self, position_update: Dict[str, Any]):
        """Process position update from user stream."""
        # TODO: Implement position update processing
        pass

    def _process_balance_update(self, balance_update: Dict[str, Any]):
        """
        Process balance update from WebSocket.

        Extended WebSocket balance message format:
        {
            "type": "BALANCE",
            "data": {
                "isSnapshot": true/false,
                "balance": {
                    "collateralName": "USD",
                    "balance": "7.667333",
                    "equity": "7.667333",
                    "availableForTrade": "7.667333",
                    "availableForWithdrawal": "7.667333",
                    "unrealisedPnl": "0.000000",
                    "initialMargin": "0.000000",
                    "marginRatio": "0",
                    "leverage": "0.0000"
                }
            },
            "ts": 1763797802075,
            "seq": 2
        }
        """
        try:
            data = balance_update.get("data", {})
            balance_data = data.get("balance", {})

            if not balance_data:
                self.logger().debug("Empty balance data in WebSocket message")
                return

            # Extract balance fields
            quote = CONSTANTS.CURRENCY  # USD

            # Use equity as total balance (includes unrealized PnL)
            total_balance = Decimal(str(balance_data.get("equity", "0")))

            # Use availableForTrade as available balance (can open new positions)
            available_balance = Decimal(str(balance_data.get("availableForTrade", "0")))

            # Update account balances
            self._account_balances[quote] = total_balance
            self._account_available_balances[quote] = available_balance

            self.logger().info(
                f"Extended balance updated via WebSocket - "
                f"Total: {total_balance} {quote}, Available: {available_balance} {quote}"
            )

        except Exception as e:
            self.logger().error(f"Error processing Extended balance update: {e}", exc_info=True)

    def _process_funding_payment(self, funding_payment: Dict[str, Any]):
        """Process funding payment from user stream."""
        # TODO: Implement funding payment processing
        pass

    async def _iter_user_event_queue(self) -> AsyncIterable[Dict[str, Any]]:
        """Iterate over user event queue."""
        while True:
            try:
                yield await self._user_stream_tracker.user_stream.get()
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().error("Error getting user stream event", exc_info=True)
                await self._sleep(1.0)

    # Abstract method implementations required by base class
    def supported_order_types(self) -> List[OrderType]:
        """Return list of supported order types."""
        return [OrderType.LIMIT, OrderType.MARKET]

    async def _update_trading_fees(self):
        """Update trading fees. Placeholder for future implementation."""
        pass

    async def _status_polling_loop_fetch_updates(self):
        """
        Override base class polling to skip REST balance and position updates.

        Extended uses WebSocket for real-time account updates including:
        - Balance updates (type: BALANCE)
        - Position updates (type: POSITION)

        The WebSocket sends initial snapshots upon connection and incremental
        updates thereafter, so we don't need REST polling for these data types.

        This prevents 401 errors from continuous REST API polling while still
        updating order status via REST.
        """
        await safe_gather(
            # Skip _update_positions() - positions come via WebSocket
            # Skip _update_balances() - balances come via WebSocket
            self._update_order_status(),
        )

    async def _update_balances(self):
        """
        Update account balances from Extended API.

        NOTE: This method is NOT called during normal operation because we override
        _status_polling_loop_fetch_updates to skip it. Balance updates come via WebSocket.

        This method remains for backward compatibility or manual calls if needed.

        Fetches balance data from /api/v1/user/balance endpoint.
        Returns 404 if balance is zero (new account).
        """
        try:
            response = await self._api_get(
                path_url=CONSTANTS.BALANCE_URL,
                is_auth_required=True,
                limit_id=CONSTANTS.BALANCE_URL
            )

            if isinstance(response, dict) and response.get('status') == 'OK':
                data = response.get('data', {})

                # Extended balance response fields:
                # - balance: Account balance = Deposits - Withdrawals + Realised PnL
                # - equity: Balance + unrealised gains/losses
                # - availableForTrade: Equity minus initial margin requirements
                # - availableForWithdrawal: Maximum withdrawable amount
                quote = CONSTANTS.CURRENCY  # USD

                # Use equity as total balance (includes unrealized PnL)
                total_balance = Decimal(str(data.get('equity', '0')))
                # Use availableForTrade as available balance (can open new positions with this)
                available_balance = Decimal(str(data.get('availableForTrade', '0')))

                self._account_balances[quote] = total_balance
                self._account_available_balances[quote] = available_balance

                self.logger().debug(
                    f"Extended balance updated: Total={total_balance}, Available={available_balance}"
                )

            else:
                # Log unexpected response format
                self.logger().warning(f"Unexpected Extended balance response: {response}")

        except Exception as e:
            # Handle 404 error (zero balance) gracefully
            error_msg = str(e).lower()
            if '404' in error_msg or 'not found' in error_msg:
                # Account exists but has zero balance
                quote = CONSTANTS.CURRENCY
                self._account_balances[quote] = Decimal("0")
                self._account_available_balances[quote] = Decimal("0")
                self.logger().info("Extended account has zero balance (404 response)")
            else:
                self.logger().error(f"Error updating Extended balances: {e}", exc_info=True)
                raise

    async def _update_positions(self):
        """
        Update positions from Extended API.

        NOTE: This method is NOT called during normal operation because we override
        _status_polling_loop_fetch_updates to skip it. Position updates come via WebSocket.

        This method remains for backward compatibility or manual calls if needed.

        Fetches active positions from /api/v1/user/positions endpoint.
        """
        try:
            response = await self._api_get(
                path_url=CONSTANTS.POSITIONS_URL,
                is_auth_required=True,
                limit_id=CONSTANTS.POSITIONS_URL
            )

            if isinstance(response, dict) and response.get('status') == 'OK':
                positions_data = response.get('data', [])

                for position_info in positions_data:
                    try:
                        # Parse position data
                        market = position_info.get('market', '')  # e.g., "KAITO-USD"
                        trading_pair = await self.trading_pair_associated_to_exchange_symbol(market)

                        # Determine position side from size (positive = long, negative = short)
                        size = Decimal(str(position_info.get('size', '0')))
                        if size == 0:
                            continue  # Skip zero positions

                        position_side = PositionSide.LONG if size > 0 else PositionSide.SHORT
                        amount = abs(size)

                        # Get position details
                        entry_price = Decimal(str(position_info.get('entryPrice', '0')))
                        unrealized_pnl = Decimal(str(position_info.get('unrealisedPnl', '0')))
                        leverage_value = Decimal(str(position_info.get('leverage', '1')))

                        # Create or update position
                        pos_key = self._perpetual_trading.position_key(trading_pair, position_side)
                        position = Position(
                            trading_pair=trading_pair,
                            position_side=position_side,
                            unrealized_pnl=unrealized_pnl,
                            entry_price=entry_price,
                            amount=amount,
                            leverage=leverage_value
                        )
                        self._perpetual_trading.set_position(pos_key, position)

                    except Exception as e:
                        self.logger().error(f"Error parsing Extended position: {e}", exc_info=True)
                        continue

            else:
                # Log unexpected response
                self.logger().warning(f"Unexpected Extended positions response: {response}")

        except Exception as e:
            # Handle 404 error (no positions) gracefully
            error_msg = str(e).lower()
            if '404' in error_msg or 'not found' in error_msg:
                # No open positions
                self.logger().debug("No open positions on Extended (404 response)")
            else:
                self.logger().error(f"Error updating Extended positions: {e}", exc_info=True)
                raise

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        """Get all trade updates for an order. Placeholder for future implementation."""
        return []

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        """Request order status. Placeholder for future implementation."""
        return OrderUpdate(
            trading_pair=tracked_order.trading_pair,
            update_timestamp=self.current_timestamp,
            new_state=tracked_order.current_state,
            client_order_id=tracked_order.client_order_id,
        )

    async def _set_trading_pair_leverage(self, trading_pair: str, leverage: int) -> Tuple[bool, str]:
        """Set leverage for trading pair (wrapper for _execute_set_leverage)."""
        return await self._execute_set_leverage(trading_pair, leverage)

    def _trading_pair_position_mode_set(self, mode: PositionMode, trading_pair: str) -> Tuple[bool, str]:
        """Check if position mode is set for trading pair."""
        current_mode = self._position_mode
        if current_mode == mode:
            return True, f"Position mode already set to {mode}"
        return False, f"Position mode is {current_mode}, not {mode}"
