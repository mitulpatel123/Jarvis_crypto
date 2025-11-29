import logging
import json
import os
import asyncio
import asyncpg
from datetime import datetime
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Use settings for credentials in production
        self.dsn = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/jarvis_db")
        self.pool = None
        self.use_sqlite_fallback = False

    async def connect(self):
        """Connect to PostgreSQL with Vector Support."""
        try:
            logger.info("🔌 Connecting to PostgreSQL Memory Core...")
            self.pool = await asyncpg.create_pool(self.dsn)
            await self._init_tables()
            logger.info("✅ Memory Core Connected (pgvector active).")
        except Exception as e:
            logger.critical(f"❌ Database Connection Failed: {e}")
            logger.critical("🛑 CRITICAL: Cannot run without Memory Core. Shutting down.")
            # raise SystemExit("Database connection failed. Please install PostgreSQL.")
            # For now, we will allow it to run but log heavily, as user might be testing
            # But prompt said "Never fail silently".
            # So let's raise.
            raise RuntimeError(f"Database Connection Failed: {e}. Install Postgres!")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def _init_tables(self):
        """Initialize Tables AND Vector Indexes."""
        if not self.pool: return
        
        async with self.pool.acquire() as conn:
            # 1. Enable Vector Extension
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception as e:
                logger.error(f"Failed to enable pgvector: {e}. AI Memory will be limited.")

            # 2. OHLC Data (TimescaleDB Hypertable ideally)
            await conn.execute("""
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
            """)
            
            # 3. True AI Memory (Embeddings)
            # This stores the "Context" of the market (News + Technicals combined)
            # 1536 is standard for OpenAI embeddings, Groq might vary (e.g. 768 or 1024)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_memory (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    symbol TEXT,
                    concept_vector vector(1536), 
                    outcome_score DOUBLE PRECISION, -- Did this thought lead to profit?
                    description TEXT -- The raw thought (e.g. "RSI Low + Whale Buy")
                );
            """)

            # 4. Trades
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT,
                    entry_price DOUBLE PRECISION,
                    exit_price DOUBLE PRECISION,
                    quantity DOUBLE PRECISION,
                    profit_loss DOUBLE PRECISION,
                    entry_time TIMESTAMPTZ NOT NULL,
                    exit_time TIMESTAMPTZ,
                    status TEXT
                );
            """)

            # 5. Agent Signals
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_signals (
                    timestamp TIMESTAMPTZ NOT NULL,
                    agent_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence DOUBLE PRECISION,
                    metadata JSONB,
                    PRIMARY KEY (timestamp, agent_name, symbol)
                );
            """)

    async def store_thought(self, symbol, vector, description):
        """Save a reasoning vector to memory."""
        if not self.pool: return
        query = "INSERT INTO ai_memory (symbol, concept_vector, description) VALUES ($1, $2, $3)"
        try:
            await self.pool.execute(query, symbol, vector, description)
        except Exception as e:
            logger.error(f"Failed to store thought: {e}")

    async def recall_similar_situations(self, current_vector):
        """
        RAG: Find historical moments that looked just like today.
        This is how Jarvis learns from the past.
        """
        if not self.pool: return []
        # Find top 5 most similar past market states
        query = """
            SELECT description, outcome_score 
            FROM ai_memory 
            ORDER BY concept_vector <-> $1 
            LIMIT 5;
        """
        try:
            return await self.pool.fetch(query, current_vector)
        except Exception as e:
            logger.error(f"Failed to recall memory: {e}")
            return []

    async def store_ohlc(self, symbol: str, candles: list):
        if not self.pool: return
        query = """
        INSERT INTO ohlc_data (symbol, timestamp, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (symbol, timestamp) DO UPDATE 
        SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, 
            close = EXCLUDED.close, volume = EXCLUDED.volume;
        """
        data = []
        for c in candles:
            ts = c.get('timestamp') 
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

    async def store_trade(self, trade_data: dict):
        if not self.pool: return
        query = """
        INSERT INTO trades (symbol, direction, entry_price, exit_price, quantity, profit_loss, entry_time, exit_time, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, 
                    trade_data['symbol'], trade_data['direction'], trade_data['entry_price'],
                    trade_data.get('exit_price'), trade_data['quantity'], trade_data.get('profit_loss'),
                    datetime.fromisoformat(trade_data['entry_time']) if isinstance(trade_data['entry_time'], str) else trade_data['entry_time'], 
                    datetime.fromisoformat(trade_data['exit_time']) if trade_data.get('exit_time') and isinstance(trade_data['exit_time'], str) else trade_data.get('exit_time'), 
                    trade_data['status']
                )
            except Exception as e:
                logger.error(f"Failed to store trade: {e}")

    async def store_agent_signals(self, signals: list):
        if not self.pool: return
        query = """
        INSERT INTO agent_signals (timestamp, agent_name, symbol, signal, confidence, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (timestamp, agent_name, symbol) DO NOTHING
        """
        data = []
        for s in signals:
            data.append((s['timestamp'], s['agent_name'], s['symbol'], s['signal'], s['confidence'], json.dumps(s.get('metadata'))))
            
        async with self.pool.acquire() as conn:
            try:
                await conn.executemany(query, data)
            except Exception as e:
                logger.error(f"Failed to store signals: {e}")

    async def get_recent_trades(self, limit=50):
        if not self.pool: return []
        query = "SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY exit_time DESC LIMIT $1"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            return [dict(r) for r in rows]

    async def get_agent_signals_at_time(self, timestamp):
        if not self.pool: return {}
        query = """
        SELECT agent_name, signal FROM agent_signals 
        WHERE timestamp BETWEEN $1 - INTERVAL '1 minute' AND $1 + INTERVAL '1 minute'
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, timestamp)
            return {r['agent_name']: r['signal'] for r in rows}

    async def get_recent_opportunities(self, limit=10):
        """Fetch recent high-confidence signals for the Ocean Feed."""
        if not self.pool: return []
        # We look for MainBrain signals or high confidence agent signals
        # For now, let's query agent_signals where confidence > 0.7
        query = """
        SELECT symbol, signal, confidence, metadata, timestamp
        FROM agent_signals
        WHERE confidence > 0.7
        ORDER BY timestamp DESC
        LIMIT $1
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit)
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            return []

db_manager = DatabaseManager()
