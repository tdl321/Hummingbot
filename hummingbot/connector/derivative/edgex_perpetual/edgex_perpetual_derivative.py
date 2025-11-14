"""
EdgeX Perpetual Derivative Connector

Main connector implementation for EdgeX perpetual futures trading.
Inherits from PerpetualDerivativePyBase and implements all required methods.

CRITICAL: This file implements the core trading logic. ALL methods marked with
@abstractmethod in the base class MUST be fully implemented before deployment.
NO placeholder 'pass' statements allowed in production code.

Reference: Lessons Learned Section 1.1 (Empty Placeholder Implementations)
"""

import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from hummingbot.connector.derivative.edgex_perpetual import (
    edgex_perpetual_constants as CONSTANTS,
    edgex_perpetual_utils as utils,
    edgex_perpetual_web_utils as web_utils,
)
from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_auth import EdgexPerpetualAuth
from hummingbot.connector.derivative.position import Position
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, PositionSide, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.trade_fee import TokenAmount, TradeFeeBase
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.utils.async_utils import safe_gather
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

if TYPE_CHECKING:
    from hummingbot.client.config.config_helpers import ClientConfigAdapter


class EdgexPerpetualDerivative(PerpetualDerivativePyBase):
    """
    EdgeX Perpetual Derivative connector.

    Implements perpetual futures trading on EdgeX DEX (StarkEx Layer 2).
    Follows the same architectural pattern as Paradex connector but with
    EdgeX-specific authentication and API integration.

    Key differences from Paradex:
    - ECDSA signature authentication (not JWT)
    - RPC-style API endpoints
    - L2 StarkEx order fields required
    - No official Python SDK
    """

    web_utils = web_utils

    # Polling intervals
    SHORT_POLL_INTERVAL = 5.0  # 5 seconds for frequent updates
    LONG_POLL_INTERVAL = 120.0  # 2 minutes for less frequent updates
    UPDATE_ORDER_STATUS_MIN_INTERVAL = 10.0  # Minimum 10 seconds between order status updates
    FUNDING_FEE_POLL_INTERVAL = 120  # 2 minutes

    def __init__(
        self,
        client_config_map: "ClientConfigAdapter",
        edgex_perpetual_api_secret: str,
        edgex_perpetual_account_id: str,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DOMAIN,
    ):
        """
        Initialize EdgeX Perpetual connector.

        Args:
            client_config_map: Client configuration
            edgex_perpetual_api_secret: Private key for signing requests
            edgex_perpetual_account_id: EdgeX account ID
            trading_pairs: List of trading pairs to track
            trading_required: Whether trading is required
            domain: Domain (mainnet or testnet)
        """
        self._edgex_perpetual_api_secret = edgex_perpetual_api_secret
        self._edgex_perpetual_account_id = edgex_perpetual_account_id
        self._trading_pairs = trading_pairs or []
        self._trading_required = trading_required
        self._domain = domain

        # Position mode (default to ONE_WAY, verify if EdgeX supports HEDGE)
        self._position_mode = PositionMode.ONEWAY

        # Trading rules cache
        self._trading_rules: Dict[str, TradingRule] = {}

        # Contract metadata cache
        self._contract_metadata: Dict[str, Dict[str, Any]] = {}

        # Last update timestamps
        self._last_trading_rules_update_ts = 0
        self._last_funding_fee_payment_ts: Dict[str, float] = {}

        super().__init__(client_config_map)

    # ===============================
    # Properties
    # ===============================

    @property
    def name(self) -> str:
        """Connector name."""
        return self._domain

    @property
    def authenticator(self) -> EdgexPerpetualAuth:
        """Get authentication handler."""
        return self._auth

    @property
    def funding_fee_poll_interval(self) -> int:
        """Funding fee polling interval in seconds."""
        return self.FUNDING_FEE_POLL_INTERVAL

    @property
    def rate_limits_rules(self):
        """Rate limit rules."""
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self) -> str:
        """Domain identifier."""
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
        return CONSTANTS.METADATA_URL

    @property
    def trading_pairs_request_path(self) -> str:
        """Path for trading pairs request."""
        return CONSTANTS.METADATA_URL

    @property
    def check_network_request_path(self) -> str:
        """Path for network check request."""
        return CONSTANTS.SERVER_TIME_URL

    @property
    def trading_pairs(self) -> List[str]:
        """List of trading pairs."""
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        """Whether cancel requests are synchronous."""
        return True

    @property
    def is_trading_required(self) -> bool:
        """Whether trading is required."""
        return self._trading_required

    # ===============================
    # Required Abstract Methods
    # ===============================

    def supported_order_types(self) -> List[OrderType]:
        """
        Supported order types.

        Returns:
            List of supported OrderType enum values
        """
        return [OrderType.LIMIT, OrderType.MARKET]

    def supported_position_modes(self) -> List[PositionMode]:
        """
        Supported position modes.

        EdgeX position mode support needs verification.
        TODO: Verify if EdgeX supports HEDGE mode or only ONEWAY

        Returns:
            List of supported PositionMode enum values
        """
        return [PositionMode.ONEWAY]  # TODO: Verify if HEDGE mode supported

    def get_buy_collateral_token(self, trading_pair: str) -> str:
        """
        Get collateral token for buy orders.

        Args:
            trading_pair: Trading pair (e.g., "BTC-USD-PERP")

        Returns:
            Collateral token symbol (typically "USD" or "USDC")
        """
        return CONSTANTS.CURRENCY  # TODO: Verify from metadata API

    def get_sell_collateral_token(self, trading_pair: str) -> str:
        """
        Get collateral token for sell orders.

        Args:
            trading_pair: Trading pair (e.g., "BTC-USD-PERP")

        Returns:
            Collateral token symbol (typically "USD" or "USDC")
        """
        return CONSTANTS.CURRENCY  # TODO: Verify from metadata API

    # ===============================
    # Authentication & Initialization
    # ===============================

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        """
        Create web assistants factory with authentication.

        Returns:
            WebAssistantsFactory instance
        """
        return web_utils.build_api_factory(
            throttler=self._throttler,
            auth=self._auth
        )

    def _create_order_book_data_source(self) -> OrderBookTrackerDataSource:
        """
        Create order book data source for market data streaming.

        Returns:
            OrderBookTrackerDataSource instance

        TODO: Implement EdgexPerpetualAPIOrderBookDataSource
        """
        # Will be implemented in Phase 4
        from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_api_order_book_data_source import (
            EdgexPerpetualAPIOrderBookDataSource
        )
        return EdgexPerpetualAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory,
            domain=self._domain
        )

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        """
        Create user stream data source for private data streaming.

        Returns:
            UserStreamTrackerDataSource instance

        TODO: Implement EdgexPerpetualUserStreamDataSource
        """
        # Will be implemented in Phase 4
        from hummingbot.connector.derivative.edgex_perpetual.edgex_perpetual_user_stream_data_source import (
            EdgexPerpetualUserStreamDataSource
        )
        return EdgexPerpetualUserStreamDataSource(
            auth=self._auth,
            api_factory=self._web_assistants_factory,
            domain=self._domain
        )

    def _get_fee(
        self,
        base_currency: str,
        quote_currency: str,
        order_type: OrderType,
        order_side: TradeType,
        amount: Decimal,
        price: Decimal = Decimal("NaN"),
        is_maker: Optional[bool] = None,
    ) -> TradeFeeBase:
        """
        Calculate trading fee.

        Args:
            base_currency: Base currency
            quote_currency: Quote currency
            order_type: Order type
            order_side: Order side (buy/sell)
            amount: Order amount
            price: Order price
            is_maker: Whether order is maker (None if unknown)

        Returns:
            TradeFeeBase with fee calculation
        """
        is_maker = is_maker or (order_type is OrderType.LIMIT_MAKER)
        fee_schema = utils.DEFAULT_FEES  # TODO: Get from metadata API
        return TradeFeeBase.new_perpetual_fee(
            fee_schema=fee_schema,
            position_action=PositionAction.OPEN,  # Simplified
            percent_token=quote_currency,
            flat_fees=[],
        )

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict[str, Any]):
        """
        Initialize trading pair symbol mappings from exchange metadata.

        Args:
            exchange_info: Exchange metadata from /api/v1/public/meta/getMetaData

        TODO: Implement proper mapping from contractList in metadata
        """
        # TODO: Parse contractList from metadata API
        # Build mappings: contractId <-> trading_pair symbol
        pass

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception) -> bool:
        """
        Check if exception is related to time synchronization.

        Args:
            request_exception: Exception from API request

        Returns:
            True if time sync related, False otherwise
        """
        # EdgeX uses timestamp in signature, check for timestamp-related errors
        error_message = str(request_exception).lower()
        return "timestamp" in error_message or "time" in error_message

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        """
        Check if exception indicates order not found.

        Args:
            status_update_exception: Exception from order status update

        Returns:
            True if order not found, False otherwise
        """
        error_message = str(status_update_exception).lower()
        return "not found" in error_message or "does not exist" in error_message

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        """
        Check if exception indicates order not found during cancellation.

        Args:
            cancelation_exception: Exception from order cancellation

        Returns:
            True if order not found, False otherwise
        """
        error_message = str(cancelation_exception).lower()
        return "not found" in error_message or "does not exist" in error_message

    # ===============================
    # Core Trading Methods
    # ===============================

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
        Place order on EdgeX.

        CRITICAL: This method MUST be fully implemented before deployment.
        NO placeholder 'pass' statement allowed.

        Args:
            order_id: Client order ID
            trading_pair: Trading pair
            amount: Order amount
            trade_type: BUY or SELL
            order_type: LIMIT or MARKET
            price: Order price (ignored for MARKET orders)
            position_action: Position action
            **kwargs: Additional parameters

        Returns:
            Tuple of (exchange_order_id, created_timestamp)

        Reference: Lessons Learned Section 1.1, 1.2
        """
        try:
            # Get contract ID from trading pair
            # TODO: Implement proper mapping after metadata integration
            contract_id = trading_pair  # Using trading_pair as contractId for now

            # Map order parameters to EdgeX format
            side = CONSTANTS.SIDE_BUY if trade_type == TradeType.BUY else CONSTANTS.SIDE_SELL

            # Determine order type
            if order_type == OrderType.LIMIT or order_type == OrderType.LIMIT_MAKER:
                edgex_order_type = CONSTANTS.ORDER_TYPE_LIMIT
            else:
                edgex_order_type = CONSTANTS.ORDER_TYPE_MARKET

            # Time in force
            time_in_force = kwargs.get("time_in_force", CONSTANTS.TIME_IN_FORCE_GTC)

            # Reduce only flag
            reduce_only = position_action == PositionAction.CLOSE

            # TODO: Implement L2 signature generation for orders
            # For now, raise NotImplementedError to prevent order placement without L2 signing
            # This is CRITICAL - orders require L2 StarkEx signatures
            raise NotImplementedError(
                "Order placement requires L2 StarkEx signature implementation. "
                "This involves:\n"
                "1. Calculating l2Nonce (order nonce)\n"
                "2. Calculating l2Value (notional value)\n"
                "3. Calculating l2Size (order size in contract units)\n"
                "4. Calculating l2LimitFee (max fee)\n"
                "5. Calculating l2ExpireTime (expiration timestamp)\n"
                "6. Generating l2Signature (Pedersen hash + STARK signature)\n"
                "See EdgeX documentation: https://edgex-1.gitbook.io/edgex-documentation/api/l2-signature"
            )

            # This code will be enabled after L2 signing is implemented:
            """
            # Build order request with L2 fields
            order_data = {
                "accountId": self._edgex_perpetual_account_id,
                "contractId": contract_id,
                "side": side,
                "size": str(amount),
                "price": str(price),
                "clientOrderId": order_id,
                "type": edgex_order_type,
                "timeInForce": time_in_force,
                "reduceOnly": reduce_only,
                # L2 StarkEx fields (requires order signer)
                "l2Nonce": l2_nonce,
                "l2Value": l2_value,
                "l2Size": l2_size,
                "l2LimitFee": l2_limit_fee,
                "l2ExpireTime": l2_expire_time,
                "l2Signature": l2_signature,
            }

            # Submit order to EdgeX
            response = await self._api_post(
                path_url=CONSTANTS.CREATE_ORDER_URL,
                data=order_data,
                is_auth_required=True,
                limit_id=CONSTANTS.CREATE_ORDER_URL
            )

            # Parse response
            if not isinstance(response, dict) or response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                error_msg = response.get(CONSTANTS.RESPONSE_MSG, "Unknown error")
                raise IOError(f"Order placement failed: {error_msg}")

            order_result = response.get(CONSTANTS.RESPONSE_DATA, {})
            exchange_order_id = str(order_result.get("orderId"))
            created_timestamp = float(order_result.get("createTime", self.current_timestamp * 1000)) / 1000

            self.logger().info(
                f"✅ Order placed successfully: {order_id} -> {exchange_order_id} "
                f"({side} {amount} {trading_pair} @ {price})"
            )

            return exchange_order_id, created_timestamp
            """

        except NotImplementedError:
            # Re-raise NotImplementedError for L2 signing
            raise
        except Exception as e:
            self.logger().error(
                f"❌ Error placing order {order_id}: {str(e)}",
                exc_info=True
            )
            raise

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        """
        Cancel order on EdgeX.

        CRITICAL: This method MUST be fully implemented before deployment.

        Args:
            order_id: Client order ID
            tracked_order: Tracked order object

        Reference: Lessons Learned Section 1.2
        """
        try:
            # Get exchange order ID from tracked order
            exchange_order_id = tracked_order.exchange_order_id

            if not exchange_order_id:
                # If no exchange order ID, cannot cancel
                raise ValueError(f"Cannot cancel order {order_id}: no exchange_order_id found")

            # Build cancel request
            cancel_data = {
                "accountId": self._edgex_perpetual_account_id,
                "orderIdList": [exchange_order_id]  # EdgeX expects a list of order IDs
            }

            # Submit cancel request to EdgeX
            response = await self._api_post(
                path_url=CONSTANTS.CANCEL_ORDER_BY_ID_URL,
                data=cancel_data,
                is_auth_required=True,
                limit_id=CONSTANTS.CANCEL_ORDER_BY_ID_URL
            )

            # Parse response
            if not isinstance(response, dict):
                raise IOError(f"Invalid cancel response format: {response}")

            if response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                error_msg = response.get(CONSTANTS.RESPONSE_MSG, "Unknown error")

                # Check if order was already cancelled or filled
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    self.logger().warning(
                        f"Order {order_id} ({exchange_order_id}) not found on exchange - may already be filled/cancelled"
                    )
                    return  # Don't raise error for already-cancelled orders

                raise IOError(f"Order cancellation failed: {error_msg}")

            self.logger().info(
                f"✅ Order cancelled successfully: {order_id} ({exchange_order_id})"
            )

        except Exception as e:
            self.logger().error(
                f"❌ Error cancelling order {order_id}: {str(e)}",
                exc_info=True
            )
            raise

    # ===============================
    # Account Data Methods
    # ===============================

    async def _update_balances(self):
        """
        Update account balances from EdgeX API.

        CRITICAL: This method MUST be fully implemented before deployment.
        Empty implementation causes balance to show $0, blocking trading.

        Fetches from: /api/v1/private/account/getCollateralByCoinId

        Reference: Lessons Learned Section 1.1 (CRITICAL MISTAKE #1)
        """
        try:
            # Fetch collateral/balance data from EdgeX
            response = await self._api_get(
                path_url=CONSTANTS.GET_COLLATERAL_BY_COIN_URL,
                params={"accountId": self._edgex_perpetual_account_id},
                is_auth_required=True,
                limit_id=CONSTANTS.GET_COLLATERAL_BY_COIN_URL
            )

            # EdgeX API response format: {"code": "SUCCESS", "data": {...}}
            if not isinstance(response, dict):
                self.logger().warning(f"Invalid balance response format: {response}")
                return

            if response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                error_msg = response.get(CONSTANTS.RESPONSE_MSG, "Unknown error")
                self.logger().error(f"Balance fetch failed: {error_msg}")
                return

            data = response.get(CONSTANTS.RESPONSE_DATA, {})

            # EdgeX returns collateral data with coin information
            # Expected structure: {"data": [{"coinId": "USD", "amount": "1000.50", ...}, ...]}
            if isinstance(data, list):
                balances_list = data
            elif isinstance(data, dict) and "collateralList" in data:
                balances_list = data["collateralList"]
            else:
                self.logger().warning(f"Unexpected balance data structure: {data}")
                return

            # Parse balance data
            for balance_entry in balances_list:
                # Get asset/coin identifier
                asset = balance_entry.get("coinId") or balance_entry.get("coin") or balance_entry.get("asset")
                if not asset:
                    continue

                # EdgeX balance fields (amount is total balance)
                total_balance_str = balance_entry.get("amount", "0")
                total_balance = Decimal(str(total_balance_str))

                # Available balance (may need to calculate: total - frozen/locked)
                frozen_balance_str = balance_entry.get("frozenAmount", "0")
                frozen_balance = Decimal(str(frozen_balance_str))
                available_balance = total_balance - frozen_balance

                # Update Hummingbot's internal balance tracking
                self._account_balances[asset] = total_balance
                self._account_available_balances[asset] = available_balance

                self.logger().debug(
                    f"Updated {asset} balance: total={total_balance}, available={available_balance}"
                )

        except Exception as e:
            self.logger().error(
                f"❌ CRITICAL ERROR updating EdgeX balances: {str(e)}\n"
                f"This will cause trading to fail. Verify:\n"
                f"1. API credentials are valid\n"
                f"2. Account has been funded\n"
                f"3. Account is whitelisted\n"
                f"4. API endpoint is correct",
                exc_info=True
            )
            # Re-raise to signal failure to framework
            raise

    async def _update_positions(self):
        """
        Update positions from EdgeX API.

        CRITICAL: This method MUST be fully implemented before deployment.
        Empty implementation breaks position tracking.

        Fetches from: /api/v1/private/account/getPositionByContractId

        Reference: Lessons Learned Section 1.1 (CRITICAL MISTAKE #1)
        """
        try:
            # Fetch position data from EdgeX
            response = await self._api_get(
                path_url=CONSTANTS.GET_POSITION_BY_CONTRACT_URL,
                params={"accountId": self._edgex_perpetual_account_id},
                is_auth_required=True,
                limit_id=CONSTANTS.GET_POSITION_BY_CONTRACT_URL
            )

            # EdgeX API response format: {"code": "SUCCESS", "data": {...}}
            if not isinstance(response, dict):
                self.logger().warning(f"Invalid positions response format: {response}")
                return

            if response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                error_msg = response.get(CONSTANTS.RESPONSE_MSG, "Unknown error")
                self.logger().error(f"Positions fetch failed: {error_msg}")
                return

            data = response.get(CONSTANTS.RESPONSE_DATA, {})

            # Clear existing positions
            self._account_positions.clear()

            # EdgeX returns position data per contract
            # Expected structure: {"data": [{"contractId": "BTC-USD-PERP", "openSize": "0.5", ...}, ...]}
            if isinstance(data, list):
                positions_list = data
            elif isinstance(data, dict) and "positionList" in data:
                positions_list = data["positionList"]
            else:
                self.logger().warning(f"Unexpected positions data structure: {data}")
                return

            for position_data in positions_list:
                # Get contract ID and convert to trading pair
                contract_id = position_data.get("contractId") or position_data.get("contract")
                if not contract_id:
                    continue

                # Convert EdgeX contractId to Hummingbot trading pair
                # TODO: Implement proper mapping after metadata integration
                try:
                    trading_pair = self._get_trading_pair(contract_id)
                except NotImplementedError:
                    # Skip until mapping is implemented
                    trading_pair = contract_id  # Use contractId as fallback

                # Parse position size and determine side
                open_size_str = position_data.get("openSize", "0")
                open_size = Decimal(str(open_size_str))

                if open_size == 0:
                    continue  # No position

                # Determine position side from sign of open_size
                if open_size > 0:
                    position_side = PositionSide.LONG
                    amount = open_size
                elif open_size < 0:
                    position_side = PositionSide.SHORT
                    amount = abs(open_size)
                else:
                    continue

                # Extract position details
                entry_price_str = position_data.get("avgEntryPrice") or position_data.get("openPrice", "0")
                entry_price = Decimal(str(entry_price_str))

                unrealized_pnl_str = position_data.get("unrealizedPnl", "0")
                unrealized_pnl = Decimal(str(unrealized_pnl_str))

                leverage_str = position_data.get("leverage", "1")
                leverage = Decimal(str(leverage_str))

                # Create Position object
                position = Position(
                    trading_pair=trading_pair,
                    position_side=position_side,
                    unrealized_pnl=unrealized_pnl,
                    entry_price=entry_price,
                    amount=amount,
                    leverage=leverage,
                )

                self._account_positions[trading_pair] = position

                self.logger().debug(
                    f"Updated position for {trading_pair}: "
                    f"{position_side.name} {amount} @ {entry_price} (PnL: {unrealized_pnl})"
                )

        except Exception as e:
            self.logger().error(
                f"❌ CRITICAL ERROR updating EdgeX positions: {str(e)}\n"
                f"This will cause position tracking to fail.",
                exc_info=True
            )
            # Re-raise to signal failure
            raise

    async def _update_trading_rules(self):
        """
        Update trading rules from EdgeX API.

        CRITICAL: This method MUST be fully implemented before deployment.

        Fetches from: /api/v1/public/meta/getMetaData
        """
        try:
            # Fetch metadata from EdgeX (contains contract information)
            response = await self._api_get(
                path_url=CONSTANTS.METADATA_URL,
                is_auth_required=False,
                limit_id=CONSTANTS.METADATA_URL
            )

            if not isinstance(response, dict):
                self.logger().warning(f"Invalid metadata response format: {response}")
                return

            if response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                error_msg = response.get(CONSTANTS.RESPONSE_MSG, "Unknown error")
                self.logger().error(f"Metadata fetch failed: {error_msg}")
                return

            data = response.get(CONSTANTS.RESPONSE_DATA, {})

            # Extract contract list from metadata
            contract_list = data.get("contractList", [])

            if not contract_list:
                self.logger().warning("No contracts found in metadata response")
                return

            # Clear existing trading rules
            self._trading_rules.clear()

            # Parse contract information into trading rules
            for contract_info in contract_list:
                try:
                    # Get contract ID (e.g., "BTC-USD-PERP")
                    contract_id = contract_info.get("contractId")
                    if not contract_id:
                        continue

                    # Convert to Hummingbot trading pair format
                    # TODO: Implement proper mapping
                    trading_pair = contract_id  # Use contractId as trading pair for now

                    # Extract trading rules parameters
                    min_order_size = Decimal(str(contract_info.get("minOrderSize", "0.001")))
                    max_order_size = Decimal(str(contract_info.get("maxOrderSize", "1000000")))
                    min_price_increment = Decimal(str(contract_info.get("tickSize", "0.01")))
                    min_base_amount_increment = Decimal(str(contract_info.get("stepSize", "0.001")))

                    # Create TradingRule object
                    trading_rule = TradingRule(
                        trading_pair=trading_pair,
                        min_order_size=min_order_size,
                        max_order_size=max_order_size,
                        min_price_increment=min_price_increment,
                        min_base_amount_increment=min_base_amount_increment,
                        min_notional_size=Decimal("1"),  # Default minimum notional
                    )

                    self._trading_rules[trading_pair] = trading_rule

                    # Cache contract metadata for later use
                    self._contract_metadata[contract_id] = contract_info

                    self.logger().debug(
                        f"Updated trading rule for {trading_pair}: "
                        f"min={min_order_size}, max={max_order_size}, "
                        f"tick={min_price_increment}, step={min_base_amount_increment}"
                    )

                except Exception as e:
                    self.logger().error(f"Error parsing contract info for {contract_info.get('contractId')}: {e}")
                    continue

            # Update timestamp
            self._last_trading_rules_update_ts = self.current_timestamp

            self.logger().info(f"Successfully updated {len(self._trading_rules)} trading rules from EdgeX metadata")

        except Exception as e:
            self.logger().error(
                f"❌ ERROR updating EdgeX trading rules: {str(e)}",
                exc_info=True
            )
            # Do not re-raise - trading rules update failure shouldn't stop the bot
            # But log prominently
            self.logger().warning("Trading rules update failed - using cached rules if available")

    async def _update_funding_rates(self):
        """
        Update funding rates for all trading pairs.

        CRITICAL: This method MUST be fully implemented before deployment.

        NOTE: EdgeX funding rate endpoint may vary. Try metadata first, then dedicated endpoint.
        """
        if not self._trading_pairs:
            return

        try:
            # Try to fetch funding rates from metadata (may include funding rate info)
            response = await self._api_get(
                path_url=CONSTANTS.METADATA_URL,
                is_auth_required=False,
                limit_id=CONSTANTS.METADATA_URL
            )

            if not isinstance(response, dict) or response.get(CONSTANTS.RESPONSE_CODE) != CONSTANTS.RESPONSE_CODE_SUCCESS:
                self.logger().debug("Could not fetch funding rates from metadata")
                return

            data = response.get(CONSTANTS.RESPONSE_DATA, {})
            contract_list = data.get("contractList", [])

            for contract_info in contract_list:
                try:
                    contract_id = contract_info.get("contractId")
                    if not contract_id:
                        continue

                    # Convert to trading pair
                    trading_pair = contract_id  # Use contractId as trading pair for now

                    # Extract funding rate (field name may vary - try multiple)
                    funding_rate_str = (
                        contract_info.get("fundingRate") or
                        contract_info.get("currentFundingRate") or
                        contract_info.get("funding_rate")
                    )

                    if funding_rate_str is not None:
                        funding_rate = Decimal(str(funding_rate_str))

                        # Update internal tracking
                        self._funding_rates[trading_pair] = funding_rate

                        self.logger().debug(
                            f"Updated funding rate for {trading_pair}: {funding_rate:.6f}"
                        )

                except Exception as e:
                    self.logger().error(
                        f"Error extracting funding rate for {contract_info.get('contractId')}: {str(e)}"
                    )
                    continue

        except Exception as e:
            self.logger().error(
                f"Error in _update_funding_rates: {str(e)}",
                exc_info=True
            )
            # Do not re-raise - funding rate updates are not critical for basic trading

    # ===============================
    # Position & Leverage Methods
    # ===============================

    async def _trading_pair_position_mode_set(
        self, mode: PositionMode, trading_pair: str
    ) -> Tuple[bool, str]:
        """
        Set position mode for trading pair.

        Args:
            mode: Position mode (ONEWAY or HEDGE)
            trading_pair: Trading pair

        Returns:
            Tuple of (success: bool, error_message: str)

        TODO: Verify if EdgeX supports position mode switching
        TODO: Implement in Phase 3 if supported
        """
        # EdgeX position mode support unclear
        # Return failure for now
        return False, "Position mode switching not yet implemented"

    async def _set_trading_pair_leverage(
        self, trading_pair: str, leverage: int
    ) -> Tuple[bool, str]:
        """
        Set leverage for trading pair.

        Args:
            trading_pair: Trading pair
            leverage: Leverage value

        Returns:
            Tuple of (success: bool, error_message: str)

        TODO: Determine how EdgeX handles leverage setting
        TODO: Implement in Phase 3
        """
        # EdgeX leverage setting method unclear
        # Return success for now (may be per-order or account-level)
        return True, ""

    async def _fetch_last_fee_payment(self, trading_pair: str) -> Tuple[float, Decimal, Decimal]:
        """
        Fetch last funding fee payment.

        Args:
            trading_pair: Trading pair

        Returns:
            Tuple of (timestamp, funding_rate, payment_amount)
            Returns (0, -1, -1) if no payment exists

        TODO: Implement in Phase 3
        - Determine endpoint for funding payment history
        - Parse response
        """
        # Placeholder: no payment
        return 0, Decimal("-1"), Decimal("-1")

    # ===============================
    # Helper Methods
    # ===============================

    def _get_contract_id(self, trading_pair: str) -> str:
        """
        Get EdgeX contractId from Hummingbot trading pair.

        Args:
            trading_pair: Trading pair in Hummingbot format (e.g., "BTC-USD-PERP")

        Returns:
            EdgeX contractId

        TODO: Implement after metadata API integration
        """
        # TODO: Lookup from cached metadata
        raise NotImplementedError("Contract ID mapping not yet implemented")

    def _get_trading_pair(self, contract_id: str) -> str:
        """
        Get Hummingbot trading pair from EdgeX contractId.

        Args:
            contract_id: EdgeX contractId

        Returns:
            Trading pair in Hummingbot format

        TODO: Implement after metadata API integration
        """
        # TODO: Lookup from cached metadata
        raise NotImplementedError("Trading pair mapping not yet implemented")
