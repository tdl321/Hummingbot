import logging
from decimal import Decimal
from typing import Dict, Optional

import pandas as pd

from hummingbot.client.config.config_helpers import get_connector_class
from hummingbot.client.settings import AllConnectorSettings, ConnectorType
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import LazyDict, PriceType
from hummingbot.data_feed.candles_feed.candles_base import CandlesBase
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig, HistoricalCandlesConfig
from hummingbot.data_feed.market_data_provider import MarketDataProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestingDataProvider(MarketDataProvider):
    CONNECTOR_TYPES = [ConnectorType.CLOB_SPOT, ConnectorType.CLOB_PERP, ConnectorType.Exchange,
                       ConnectorType.Derivative]
    EXCLUDED_CONNECTORS = ["hyperliquid_perpetual", "dydx_perpetual", "cube", "vertex",
                           "coinbase_advanced_trade", "kraken", "dydx_v4_perpetual", "hitbtc",
                           "hyperliquid", "injective_v2_perpetual", "injective_v2"]

    def __init__(self, connectors: Dict[str, ConnectorBase]):
        super().__init__(connectors)
        self.start_time = None
        self.end_time = None
        self.prices = {}
        self._time = None
        self.trading_rules = {}
        self.funding_feeds = {}  # Add funding rate feeds storage
        self.conn_settings = AllConnectorSettings.get_connector_settings()
        self.connectors = LazyDict[str, Optional[ConnectorBase]](
            lambda name: self.get_connector(name) if (
                self.conn_settings[name].type in self.CONNECTOR_TYPES and
                name not in self.EXCLUDED_CONNECTORS and
                "testnet" not in name
            ) else None
        )

    def get_connector(self, connector_name: str):
        conn_setting = self.conn_settings.get(connector_name)
        if conn_setting is None:
            logger.error(f"Connector {connector_name} not found")
            raise ValueError(f"Connector {connector_name} not found")

        init_params = conn_setting.conn_init_parameters(
            trading_pairs=[],
            trading_required=False,
            api_keys=MarketDataProvider.get_connector_config_map(connector_name),
        )
        connector_class = get_connector_class(connector_name)
        connector = connector_class(**init_params)
        return connector

    def get_trading_rules(self, connector_name: str, trading_pair: str):
        """
        Retrieves the trading rules from the specified connector.
        :param connector_name: str
        :return: Trading rules.
        """
        return self.trading_rules[connector_name][trading_pair]

    def time(self):
        return self._time

    async def initialize_trading_rules(self, connector_name: str):
        if len(self.trading_rules.get(connector_name, {})) == 0:
            connector = self.connectors.get(connector_name)
            await connector._update_trading_rules()
            self.trading_rules[connector_name] = connector.trading_rules

    async def initialize_candles_feed(self, config: CandlesConfig):
        await self.get_candles_feed(config)

    def update_backtesting_time(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time
        self._time = start_time

    async def get_candles_feed(self, config: CandlesConfig):
        """
        Retrieves or creates and starts a candle feed based on the given configuration.
        If an existing feed has a higher or equal max_records, it is reused.
        :param config: CandlesConfig
        :return: Candle feed instance.
        """
        key = self._generate_candle_feed_key(config)
        existing_feed = self.candles_feeds.get(key, pd.DataFrame())
        # existing_feed = self.ensure_epoch_index(existing_feed)

        if not existing_feed.empty:
            existing_feed_start_time = existing_feed["timestamp"].min()
            existing_feed_end_time = existing_feed["timestamp"].max()
            if existing_feed_start_time <= self.start_time and existing_feed_end_time >= self.end_time:
                return existing_feed
        # Create a new feed or restart the existing one with updated max_records
        candle_feed = CandlesFactory.get_candle(config)
        candles_buffer = config.max_records * CandlesBase.interval_to_seconds[config.interval]
        candles_df = await candle_feed.get_historical_candles(config=HistoricalCandlesConfig(
            connector_name=config.connector,
            trading_pair=config.trading_pair,
            interval=config.interval,
            start_time=self.start_time - candles_buffer,
            end_time=self.end_time,
        ))
        # TODO: fix pandas-ta improper float index slicing to allow us to use float indexes
        # candles_df = self.ensure_epoch_index(candles_df)
        self.candles_feeds[key] = candles_df
        return candles_df

    def get_candles_df(self, connector_name: str, trading_pair: str, interval: str, max_records: int = 500):
        """
        Retrieves the candles for a trading pair from the specified connector.
        :param connector_name: str
        :param trading_pair: str
        :param interval: str
        :param max_records: int
        :return: Candles dataframe.
        """
        candles_df = self.candles_feeds.get(f"{connector_name}_{trading_pair}_{interval}")
        return candles_df[(candles_df["timestamp"] >= self.start_time) & (candles_df["timestamp"] <= self.end_time)]

    def get_price_by_type(self, connector_name: str, trading_pair: str, price_type: PriceType):
        """
        Retrieves the price for a trading pair from the specified connector based on the price type.
        :param connector_name: str
        :param trading_pair: str
        :param price_type: PriceType
        :return: Price.
        """
        return self.prices.get(f"{connector_name}_{trading_pair}", Decimal("1"))

    def quantize_order_amount(self, connector_name: str, trading_pair: str, amount: Decimal):
        """
        Quantizes the order amount based on the trading pair's minimum order size.
        :param connector_name: str
        :param trading_pair: str
        :param amount: Decimal
        :return: Quantized amount.
        """
        trading_rules = self.get_trading_rules(connector_name, trading_pair)
        order_size_quantum = trading_rules.min_base_amount_increment
        return (amount // order_size_quantum) * order_size_quantum

    def quantize_order_price(self, connector_name: str, trading_pair: str, price: Decimal):
        """
        Quantizes the order price based on the trading pair's minimum price increment.
        :param connector_name: str
        :param trading_pair: str
        :param price: Decimal
        :return: Quantized price.
        """
        trading_rules = self.get_trading_rules(connector_name, trading_pair)
        price_quantum = trading_rules.min_price_increment
        return (price // price_quantum) * price_quantum

    # TODO: enable copy-on-write and allow specification of inplace
    @staticmethod
    def ensure_epoch_index(df: pd.DataFrame, timestamp_column: str = "timestamp",
                           keep_original: bool = True, index_name: str = "epoch_seconds") -> pd.DataFrame:
        """Ensures DataFrame has numeric monotonic increasing timestamp index in seconds since epoch."""
        # Skip if already numeric index but not RangeIndex as that generally means the index was dropped
        if df.index.name == index_name or df.empty:
            return df

        # DatetimeIndex → convert to seconds
        if isinstance(df.index, pd.DatetimeIndex):
            df.index = df.index.map(pd.Timestamp.timestamp)
        # Has timestamp column → use as index
        elif timestamp_column in df.columns:
            df = df.set_index(timestamp_column, drop=not keep_original)
            # Convert non-numeric indices to seconds
            if not pd.api.types.is_numeric_dtype(df.index):
                df.index = pd.to_datetime(df.index).map(pd.Timestamp.timestamp)
        else:
            raise ValueError(f"Cannot create timestamp index: no '{timestamp_column}' column found and index isn't convertible")
        df.sort_index(inplace=True)
        df.index.name = index_name
        return df

    def load_funding_rate_data(self, funding_data_path):
        """
        Load historical funding rate data from parquet files.

        Args:
            funding_data_path: Path to directory containing funding rate parquet files
        """
        from pathlib import Path
        from hummingbot.core.data_type.funding_info import FundingInfo

        funding_path = Path(funding_data_path)

        if not funding_path.exists():
            logger.warning(f"Funding data directory {funding_path} does not exist")
            return

        parquet_files = list(funding_path.glob("*.parquet"))

        if not parquet_files:
            logger.warning(f"No parquet files found in {funding_path}")
            return

        logger.info(f"Loading funding rate data from {len(parquet_files)} file(s)...")

        for file in parquet_files:
            try:
                df = pd.read_parquet(file)

                # Group by exchange and token
                for exchange in df['exchange'].unique():
                    for base in df['base'].unique():
                        quote = df['quote'].iloc[0] if 'quote' in df.columns else 'USD'

                        # Filter data
                        pair_df = df[
                            (df['exchange'] == exchange) &
                            (df['base'] == base)
                        ].copy()

                        # Sort by timestamp
                        pair_df = pair_df.sort_values('timestamp').reset_index(drop=True)

                        # Create feed key
                        connector_name = f"{exchange}_perpetual"
                        trading_pair = f"{base}-{quote}"
                        feed_key = f"{connector_name}_{trading_pair}"

                        self.funding_feeds[feed_key] = pair_df

                        logger.info(f"  Loaded {len(pair_df)} funding records for {feed_key}")

            except Exception as e:
                logger.error(f"Error loading funding data from {file}: {e}")

        logger.info(f"✅ Loaded {len(self.funding_feeds)} funding rate feeds")

    def get_funding_info(self, connector_name: str, trading_pair: str) -> Optional['FundingInfo']:
        """
        Get funding info at the current backtest timestamp.

        Args:
            connector_name: e.g., "extended_perpetual"
            trading_pair: e.g., "KAITO-USD"

        Returns:
            FundingInfo object with historical data, or None if not available
        """
        from hummingbot.core.data_type.funding_info import FundingInfo

        # Get funding feed
        feed_key = f"{connector_name}_{trading_pair}"
        funding_df = self.funding_feeds.get(feed_key)

        if funding_df is None or funding_df.empty:
            logger.warning(f"No funding data for {feed_key}")
            return None

        # Get current backtest time
        current_time = self._time

        if current_time is None:
            logger.warning("Backtest time not set")
            return None

        # Find most recent funding rate at or before current time
        historical_data = funding_df[funding_df['timestamp'] <= current_time]

        if historical_data.empty:
            logger.warning(f"No funding data for {feed_key} at timestamp {current_time}")
            return None

        # Get most recent record
        latest = historical_data.iloc[-1]

        # Calculate next funding timestamp (assume hourly funding)
        funding_interval = 3600
        next_funding = int(latest['timestamp']) + funding_interval

        # Get mark/index price from current prices
        mark_price = self.get_price_by_type(connector_name, trading_pair, PriceType.MidPrice)
        index_price = mark_price

        # Create FundingInfo object
        funding_info = FundingInfo(
            trading_pair=trading_pair,
            index_price=Decimal(str(index_price)),
            mark_price=Decimal(str(mark_price)),
            next_funding_utc_timestamp=next_funding,
            rate=Decimal(str(latest['funding_rate']))
        )

        return funding_info
