"""
Lighter Perpetual Derivative Connector

This connector enables trading on Lighter DEX, a zero-fee perpetual futures exchange.

Key Features:
- Perpetual futures trading with 0% trading fees
- 1-hour funding rate intervals
- Order book and market data streaming
- Position management

API Documentation: https://apidocs.lighter.xyz/
"""

import asyncio
from decimal import Decimal
from typing import Any, AsyncIterable, Dict, List, Optional, Tuple

from bidict import bidict

from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.derivative.lighter_perpetual import (
    lighter_perpetual_constants as CONSTANTS,
    lighter_perpetual_web_utils as web_utils,
)
from hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_api_order_book_data_source import (
    LighterPerpetualAPIOrderBookDataSource,
)
from hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_auth import LighterPerpetualAuth
from hummingbot.connector.derivative.lighter_perpetual.lighter_perpetual_user_stream_data_source import (
    LighterPerpetualUserStreamDataSource,
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

bpm_logger = None


class LighterPerpetualDerivative(PerpetualDerivativePyBase):
    """
    Lighter Perpetual Derivative connector class.

    Implements perpetual futures trading on Lighter DEX.
    """

    web_utils = web_utils

    SHORT_POLL_INTERVAL = 5.0
    LONG_POLL_INTERVAL = 12.0

    def __init__(
            self,
            balance_asset_limit: Optional[Dict[str, Dict[str, Decimal]]] = None,
            rate_limits_share_pct: Decimal = Decimal("100"),
            lighter_perpetual_api_key: str = None,
            lighter_perpetual_api_secret: str = None,
            trading_pairs: Optional[List[str]] = None,
            trading_required: bool = True,
            domain: str = CONSTANTS.DOMAIN,
    ):
        """
        Initialize Lighter perpetual connector.

        Args:
            balance_asset_limit: Asset balance limits
            rate_limits_share_pct: Percentage of rate limits to use
            lighter_perpetual_api_key: API key for Lighter
            lighter_perpetual_api_secret: API secret for Lighter
            trading_pairs: List of trading pairs to trade
            trading_required: Whether trading is required (False for read-only)
            domain: Domain identifier (lighter_perpetual or testnet)
        """
        self.lighter_perpetual_api_key = lighter_perpetual_api_key
        self.lighter_perpetual_api_secret = lighter_perpetual_api_secret
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs
        self._domain = domain
        self._position_mode = None
        self._last_funding_fee_payment_ts: Dict[str, float] = {}
        self._market_id_map: Dict[str, int] = {}  # trading_pair -> market_id
        super().__init__(balance_asset_limit, rate_limits_share_pct)

    @property
    def name(self) -> str:
        """Exchange name."""
        return self._domain

    @property
    def authenticator(self) -> Optional[LighterPerpetualAuth]:
        """Get authenticator instance."""
        if self._trading_required and self.lighter_perpetual_api_key and self.lighter_perpetual_api_secret:
            return LighterPerpetualAuth(self.lighter_perpetual_api_key, self.lighter_perpetual_api_secret)
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
        return CONSTANTS.ORDER_BOOKS_URL

    @property
    def trading_pairs_request_path(self) -> str:
        """Path for trading pairs request."""
        return CONSTANTS.ORDER_BOOKS_URL

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

        Lighter has 1-hour funding intervals.
        """
        return CONSTANTS.FUNDING_RATE_UPDATE_INTERNAL_SECOND

    def supported_position_modes(self) -> List[PositionMode]:
        """
        Supported position modes.

        Lighter supports ONEWAY mode (single position per market).
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
        # Lighter doesn't require time synchronization
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
        return LighterPerpetualAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory,
            domain=self.domain
        )

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        """Create user stream data source."""
        return LighterPerpetualUserStreamDataSource(
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

        Lighter has 0% trading fees!
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
        Place an order on Lighter using lighter SDK.

        This method uses the lighter SignerClient for transaction-signed order submission.

        Args:
            order_id: Client order ID
            trading_pair: Trading pair (e.g., "KAITO-USD")
            amount: Order amount in base asset
            trade_type: BUY or SELL
            order_type: MARKET or LIMIT
            price: Order price (mark price reference for market orders)
            position_action: OPEN or CLOSE

        Returns:
            Tuple of (exchange_order_id, timestamp)
        """
        try:
            # Ensure market mappings are loaded
            if not self._market_id_map:
                await self._initialize_market_mappings()

            # Get market ID for this trading pair
            market_id = self._market_id_map.get(trading_pair)
            if market_id is None:
                raise ValueError(f"Market ID not found for {trading_pair}")

            # Get SignerClient from authenticator
            if not self.authenticator:
                raise ValueError("No authenticator available for transaction signing")

            signer_client = self.authenticator.get_signer_client()

            # Convert trade type: is_ask = True for SELL, False for BUY
            is_ask = (trade_type == TradeType.SELL)

            # Generate client order index from order_id (use hash to get unique int)
            client_order_index = abs(hash(order_id)) % (10 ** 8)

            # Place order based on type
            if order_type == OrderType.MARKET:
                # For market orders, use create_market_order
                # avg_execution_price is a reference price
                order_tx, tx_hash, signature = signer_client.create_market_order(
                    market_index=market_id,
                    client_order_index=client_order_index,
                    base_amount=str(amount),
                    avg_execution_price=str(price),  # Reference price
                    is_ask=is_ask,
                    reduce_only=(position_action == PositionAction.CLOSE)
                )
            else:
                # For limit orders, use create_order
                order_tx, tx_hash, signature = signer_client.create_order(
                    market_index=market_id,
                    client_order_index=client_order_index,
                    base_amount=str(amount),
                    price=str(price),
                    is_ask=is_ask,
                    order_type=0,  # 0 for LIMIT
                    time_in_force=0,  # 0 for GTC (Good Till Cancel)
                    reduce_only=(position_action == PositionAction.CLOSE)
                )

            # Parse response
            # tx_hash is a TxHash object with a 'hash' attribute
            exchange_order_id = tx_hash.hash if hasattr(tx_hash, 'hash') else str(tx_hash)
            timestamp = self.current_timestamp

            self.logger().info(
                f"Successfully placed {trade_type.name} {order_type.name} order on Lighter: "
                f"{trading_pair} market_id={market_id} amount={amount} price={price} "
                f"tx_hash={exchange_order_id}"
            )

            return exchange_order_id, timestamp

        except Exception as e:
            self.logger().error(f"Error placing order on Lighter: {e}", exc_info=True)
            raise

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        """
        Cancel an order on Lighter.

        Args:
            order_id: Client order ID
            tracked_order: In-flight order to cancel
        """
        # TODO: Implement order cancellation
        raise NotImplementedError("Order cancellation requires implementation")

    async def _execute_set_position_mode(self, mode: PositionMode):
        """
        Set position mode on Lighter.

        Lighter uses ONEWAY mode by default.

        Args:
            mode: Position mode to set
        """
        if mode == PositionMode.ONEWAY:
            self._position_mode = mode
            self.logger().info(f"Position mode set to {mode}")
        else:
            self.logger().error(f"Position mode {mode} not supported by Lighter")

    async def _execute_set_leverage(self, trading_pair: str, leverage: int):
        """
        Set leverage for a trading pair on Lighter.

        Lighter API endpoint TBD.

        Args:
            trading_pair: Trading pair
            leverage: Leverage value
        """
        try:
            # TODO: Implement leverage setting via Lighter API
            # The endpoint and format need to be determined from Lighter docs

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

        Lighter API: GET /api/v1/funding

        Args:
            trading_pair: Trading pair

        Returns:
            Tuple of (timestamp, funding_rate, payment_amount)
        """
        try:
            # Get market ID for this trading pair
            if not self._market_id_map:
                await self._initialize_market_mappings()

            market_id = self._market_id_map.get(trading_pair)
            if market_id is None:
                self.logger().warning(f"Market ID not found for {trading_pair}")
                return 0, Decimal("0"), Decimal("0")

            # Get funding history
            # Lighter API: GET /api/v1/funding?market_id={id}&limit=1
            params = {"market_id": market_id, "limit": 1}
            response = await self._api_get(
                path_url=CONSTANTS.ACCOUNT_FUNDING_URL,
                params=params,
                is_auth_required=True
            )

            # Parse response
            if isinstance(response, dict):
                funding_history = response.get('fundings', [])
                if funding_history and len(funding_history) > 0:
                    latest = funding_history[0]
                    timestamp = int(latest.get('timestamp', 0))
                    funding_rate = Decimal(str(latest.get('rate', 0)))
                    payment = Decimal(str(latest.get('payment', 0)))
                    return timestamp, funding_rate, payment

            # No funding payment found
            return 0, Decimal("0"), Decimal("0")

        except Exception as e:
            self.logger().error(f"Error fetching funding payment for {trading_pair}: {e}")
            return 0, Decimal("-1"), Decimal("-1")

    async def _initialize_market_mappings(self):
        """Initialize trading pair to market ID mappings."""
        if self._market_id_map:
            return  # Already initialized

        # GET /api/v1/orderBooks
        response = await self._api_get(path_url=CONSTANTS.ORDER_BOOKS_URL)

        if isinstance(response, dict) and 'order_books' in response:
            order_books = response['order_books']
            for book in order_books:
                symbol = book.get('symbol', '').upper()
                market_id = book.get('market_id')
                if symbol and market_id is not None:
                    trading_pair = f"{symbol}-{CONSTANTS.CURRENCY}"
                    self._market_id_map[trading_pair] = market_id

        self.logger().info(f"Initialized {len(self._market_id_map)} Lighter market mappings")

    async def _format_trading_rules(self, exchange_info_dict: Dict) -> List[TradingRule]:
        """
        Format trading rules from exchange info.

        Lighter API: GET /api/v1/orderBooks

        Args:
            exchange_info_dict: Order books information from Lighter

        Returns:
            List of TradingRule objects
        """
        trading_rules = []

        # Lighter response: {"code": 200, "order_books": [{...}, {...}, ...]}
        if isinstance(exchange_info_dict, dict) and 'order_books' in exchange_info_dict:
            order_books = exchange_info_dict['order_books']

            for book in order_books:
                try:
                    # Parse order book data
                    symbol = book.get('symbol', '').upper()
                    market_id = book.get('market_id')
                    min_order_size = Decimal(str(book.get('min_order_size', '0.001')))
                    price_increment = Decimal(str(book.get('price_increment', '0.01')))
                    size_increment = Decimal(str(book.get('size_increment', '0.001')))

                    if not symbol or market_id is None:
                        continue

                    # Create trading pair
                    trading_pair = f"{symbol}-{CONSTANTS.CURRENCY}"

                    # Store market ID mapping
                    self._market_id_map[trading_pair] = market_id

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
                    self.logger().error(f"Error parsing trading rule for order book {book}: {e}")
                    continue

        return trading_rules

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict):
        """
        Initialize trading pair symbol mappings from exchange info.

        Args:
            exchange_info: Exchange information dictionary
        """
        mapping = bidict()

        if isinstance(exchange_info, dict) and 'order_books' in exchange_info:
            order_books = exchange_info['order_books']

            for book in order_books:
                if not web_utils.is_exchange_information_valid(book):
                    continue

                symbol = book.get('symbol', '').upper()
                market_id = book.get('market_id')

                if not symbol or market_id is None:
                    continue

                # Lighter uses integer market IDs, but we need string exchange symbols
                # Use the format: "SYMBOL-USD"
                exchange_symbol = f"{symbol}-{CONSTANTS.CURRENCY}"
                trading_pair = exchange_symbol  # Same format

                # Store market ID mapping
                self._market_id_map[trading_pair] = market_id

                if trading_pair in mapping.inverse:
                    self._resolve_trading_pair_symbols_duplicate(mapping, exchange_symbol, symbol, CONSTANTS.CURRENCY)
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
        # Get market ID
        if not self._market_id_map:
            await self._initialize_market_mappings()

        market_id = self._market_id_map.get(trading_pair)
        if market_id is None:
            self.logger().warning(f"Market ID not found for {trading_pair}")
            return 0.0

        # Get recent trades
        # Lighter API: GET /api/v1/trades?market_id={id}&limit=1
        params = {"market_id": market_id, "limit": 1}
        response = await self._api_get(path_url=CONSTANTS.RECENT_TRADES_URL, params=params)

        if isinstance(response, dict):
            trades = response.get('trades', [])
            if trades and len(trades) > 0:
                latest_trade = trades[0]
                last_price = float(latest_trade.get('price', 0))
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
        """Listen to user stream events."""
        # This will process events from the user stream data source
        async for event_message in self._iter_user_event_queue():
            try:
                # Process different event types
                event_type = event_message.get("type", "")

                if event_type == "order_update":
                    self._process_order_update(event_message)
                elif event_type == "position_update":
                    self._process_position_update(event_message)
                elif event_type == "balance_update":
                    self._process_balance_update(event_message)
                elif event_type == "funding_payment":
                    self._process_funding_payment(event_message)
                else:
                    self.logger().debug(f"Unknown user stream event type: {event_type}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Error processing user stream event: {e}", exc_info=True)

    def _process_order_update(self, order_update: Dict[str, Any]):
        """Process order update from user stream."""
        # TODO: Implement order update processing
        pass

    def _process_position_update(self, position_update: Dict[str, Any]):
        """Process position update from user stream."""
        # TODO: Implement position update processing
        pass

    def _process_balance_update(self, balance_update: Dict[str, Any]):
        """Process balance update from user stream."""
        # TODO: Implement balance update processing
        pass

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

    async def _update_balances(self):
        """
        Update account balances using Lighter API.

        Fetches account data using AccountApi.account() method.
        Response includes collateral and position details.
        """
        try:
            # Import Lighter SDK components
            from lighter import AccountApi, ApiClient, Configuration

            # Get wallet address from auth (stored as api_key)
            if not self.lighter_perpetual_api_key:
                self.logger().warning("Lighter wallet address not configured, skipping balance update")
                return

            wallet_address = self.lighter_perpetual_api_key

            # Create API client
            config = Configuration(host=web_utils.rest_url("", self._domain))
            api_client = ApiClient(configuration=config)
            account_api = AccountApi(api_client)

            # Fetch account info by wallet address
            try:
                accounts_response = await account_api.account(by="address", value=wallet_address)

                if accounts_response and hasattr(accounts_response, 'accounts'):
                    # Get first account (usually only one per address)
                    if len(accounts_response.accounts) > 0:
                        account = accounts_response.accounts[0]

                        # Extract balance information
                        # collateral: The amount of collateral in the account
                        collateral = Decimal(str(getattr(account, 'collateral', '0')))

                        # Calculate total from collateral + unrealized PnL from positions
                        total_unrealized_pnl = Decimal("0")
                        if hasattr(account, 'position_details') and account.position_details:
                            for position in account.position_details:
                                unrealized = Decimal(str(getattr(position, 'unrealized_pnl', '0')))
                                total_unrealized_pnl += unrealized

                        quote = CONSTANTS.CURRENCY  # USD
                        total_balance = collateral + total_unrealized_pnl
                        available_balance = collateral  # Simplified: collateral is available for trading

                        self._account_balances[quote] = total_balance
                        self._account_available_balances[quote] = available_balance

                        self.logger().debug(
                            f"Lighter balance updated: Total={total_balance}, Available={available_balance}"
                        )
                    else:
                        # No accounts found for this address (new account)
                        quote = CONSTANTS.CURRENCY
                        self._account_balances[quote] = Decimal("0")
                        self._account_available_balances[quote] = Decimal("0")
                        self.logger().info(f"Lighter account not found for address {wallet_address}")
                else:
                    self.logger().warning(f"Unexpected Lighter account response format")

            finally:
                # Close API client
                await api_client.close()

        except Exception as e:
            self.logger().error(f"Error updating Lighter balances: {e}", exc_info=True)
            # Don't raise - allow strategy to continue even if balance update fails
            # Set to zero as fallback
            quote = CONSTANTS.CURRENCY
            self._account_balances[quote] = Decimal("0")
            self._account_available_balances[quote] = Decimal("0")

    async def _update_positions(self):
        """
        Update positions using Lighter API.

        Fetches position data from account details.
        Position details include: OOC, sign, position, avg entry price, etc.
        """
        try:
            # Import Lighter SDK components
            from lighter import AccountApi, ApiClient, Configuration

            # Get wallet address from auth
            if not self.lighter_perpetual_api_key:
                self.logger().warning("Lighter wallet address not configured, skipping position update")
                return

            wallet_address = self.lighter_perpetual_api_key

            # Create API client
            config = Configuration(host=web_utils.rest_url("", self._domain))
            api_client = ApiClient(configuration=config)
            account_api = AccountApi(api_client)

            # Fetch account info with positions
            try:
                accounts_response = await account_api.account(by="address", value=wallet_address)

                if accounts_response and hasattr(accounts_response, 'accounts'):
                    if len(accounts_response.accounts) > 0:
                        account = accounts_response.accounts[0]

                        # Process position details
                        if hasattr(account, 'position_details') and account.position_details:
                            for position_info in account.position_details:
                                try:
                                    # Position details from API:
                                    # - sign: 1 for Long, -1 for Short
                                    # - position: The amount of position
                                    # - avg_entry_price: Average entry price
                                    # - unrealized_pnl: Unrealized profit/loss
                                    # - realized_pnl: Realized profit/loss

                                    sign = int(getattr(position_info, 'sign', 0))
                                    position_amount = Decimal(str(getattr(position_info, 'position', '0')))

                                    if position_amount == 0:
                                        continue  # Skip zero positions

                                    # Determine position side
                                    position_side = PositionSide.LONG if sign > 0 else PositionSide.SHORT

                                    # Get market symbol and convert to trading pair
                                    market_symbol = getattr(position_info, 'symbol', '')
                                    if not market_symbol:
                                        continue

                                    # Convert to Hummingbot trading pair format
                                    trading_pair = await self.trading_pair_associated_to_exchange_symbol(
                                        f"{market_symbol}-{CONSTANTS.CURRENCY}"
                                    )

                                    # Extract position details
                                    entry_price = Decimal(str(getattr(position_info, 'avg_entry_price', '0')))
                                    unrealized_pnl = Decimal(str(getattr(position_info, 'unrealized_pnl', '0')))

                                    # Get leverage from position value / margin (if available)
                                    # Otherwise use default leverage
                                    leverage_value = Decimal("1")  # Default if not available

                                    # Create or update position
                                    pos_key = self._perpetual_trading.position_key(trading_pair, position_side)
                                    position = Position(
                                        trading_pair=trading_pair,
                                        position_side=position_side,
                                        unrealized_pnl=unrealized_pnl,
                                        entry_price=entry_price,
                                        amount=abs(position_amount),
                                        leverage=leverage_value
                                    )
                                    self._perpetual_trading.set_position(pos_key, position)

                                except Exception as e:
                                    self.logger().error(f"Error parsing Lighter position: {e}", exc_info=True)
                                    continue

            finally:
                # Close API client
                await api_client.close()

        except Exception as e:
            self.logger().error(f"Error updating Lighter positions: {e}", exc_info=True)
            # Don't raise - allow strategy to continue

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
