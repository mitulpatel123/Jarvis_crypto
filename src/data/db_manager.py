import asyncpg
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.db_url = settings.DATABASE_URL

    async def connect(self):
        """Establish a connection pool to the database."""
        if not self.db_url:
            logger.warning("DATABASE_URL not set. Database features will be disabled.")
            return

        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("Connected to database.")
            await self._init_tables()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            # Fallback or re-raise depending on strictness. 
            # For now, we log error but don't crash app if DB is optional for some parts.
            raise e

    async def disconnect(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database.")

    async def _init_tables(self):
        """Initialize necessary tables if they don't exist."""
        # TimescaleDB extension should be enabled manually or here if superuser.
        # We assume TimescaleDB extension is already created or we just use standard Postgres for now.
        
        queries = [
            """
            CREATE TABLE IF NOT EXISTS ohlc_data (
                symbol TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                PRIMARY KEY (symbol, timestamp)
            );
            """,
            # Add hypertable creation if TimescaleDB is available
            # "SELECT create_hypertable('ohlc_data', 'timestamp', if_not_exists => TRUE);" 
        ]
        
        async with self.pool.acquire() as conn:
            for query in queries:
                try:
                    await conn.execute(query)
                except Exception as e:
                    logger.error(f"Error initializing table: {e}")

    async def store_ohlc(self, symbol: str, candles: list):
        """
        Store OHLC candles in the database.
        candles: list of dicts or tuples matching the schema.
        """
        if not self.pool:
            return

        query = """
        INSERT INTO ohlc_data (symbol, timestamp, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, timestamp) DO UPDATE 
        SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, 
            close = EXCLUDED.close, volume = EXCLUDED.volume;
        """
        
        # Convert candles to list of tuples if they are dicts
        data = []
        for c in candles:
            # Assumes c is dict-like or object with attributes
            # Adjust based on actual candle structure from Delta API
            ts = c.get('timestamp') # Should be datetime object
            o = c.get('open')
            h = c.get('high')
            l = c.get('low')
            cl = c.get('close')
            v = c.get('volume')
            data.append((symbol, ts, o, h, l, cl, v))

        async with self.pool.acquire() as conn:
            try:
                await conn.executemany(query, data)
            except Exception as e:
                logger.error(f"Failed to store OHLC data: {e}")

db_manager = DatabaseManager()
