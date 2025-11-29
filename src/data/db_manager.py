import logging
import json
import os
import asyncpg
from datetime import datetime
from src.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Default to local if not set
        self.dsn = os.getenv("DATABASE_URL", "postgresql://mitulpatel@localhost/jarvis_crypto")
        self.pool = None
        self.use_sqlite_fallback = False
        self.has_vector = False

    async def connect(self):
        try:
            logger.info("🔌 Connecting to PostgreSQL Memory Core...")
            self.pool = await asyncpg.create_pool(self.dsn)
            await self._init_tables()
            logger.info(f"✅ Memory Core Connected (Vector Support: {self.has_vector}).")
        except Exception as e:
            logger.critical(f"❌ Database Connection Failed: {e}")
            raise RuntimeError(f"Database Connection Failed: {e}. Install Postgres!")

    async def _init_tables(self):
        async with self.pool.acquire() as conn:
            # 1. Enable Vector Extension (Graceful Fallback)
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.has_vector = True
            except Exception as e:
                logger.warning(f"⚠️ pgvector extension missing: {e}. AI Memory will be limited (No Semantic Search).")
                self.has_vector = False
            
            # 2. Trades Table (Added 'mode' column)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT,
                    mode TEXT DEFAULT 'PAPER', -- 'PAPER' or 'LIVE'
                    entry_price DOUBLE PRECISION,
                    exit_price DOUBLE PRECISION,
                    quantity DOUBLE PRECISION,
                    profit_loss DOUBLE PRECISION,
                    entry_time TIMESTAMPTZ NOT NULL,
                    exit_time TIMESTAMPTZ,
                    status TEXT
                );
            """)
            
            # 3. Signals and OHLC (Standard)
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
            
            # 4. AI Memory (Thoughts) - Conditional Schema
            if self.has_vector:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ai_memory (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        symbol TEXT,
                        description TEXT,
                        vector vector(1536) -- OpenAI embedding size
                    );
                """)
            else:
                # Fallback schema without vector type
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ai_memory (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        symbol TEXT,
                        description TEXT,
                        vector TEXT -- Fallback to text storage
                    );
                """)

    async def store_trade(self, trade_data: dict):
        if not self.pool: return
        query = """
        INSERT INTO trades (symbol, direction, mode, entry_price, exit_price, quantity, profit_loss, entry_time, exit_time, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, 
                trade_data['symbol'], 
                trade_data['direction'], 
                trade_data.get('mode', 'PAPER'), # Default to PAPER
                trade_data['entry_price'],
                trade_data.get('exit_price'), 
                trade_data['quantity'], 
                trade_data.get('profit_loss'),
                trade_data['entry_time'], 
                trade_data.get('exit_time'), 
                trade_data['status']
            )

    async def get_trades_by_mode(self, mode: str, limit=50):
        if not self.pool: return []
        query = "SELECT * FROM trades WHERE mode = $1 ORDER BY entry_time DESC LIMIT $2"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, mode, limit)
            return [dict(r) for r in rows]

    async def store_thought(self, symbol: str, vector: list, description: str):
        if not self.pool: return
        
        # Handle missing vector gracefully
        if vector is None:
             query = "INSERT INTO ai_memory (symbol, description) VALUES ($1, $2)"
             async with self.pool.acquire() as conn:
                await conn.execute(query, symbol, description)
        else:
            if self.has_vector:
                query = "INSERT INTO ai_memory (symbol, vector, description) VALUES ($1, $2, $3)"
                async with self.pool.acquire() as conn:
                    await conn.execute(query, symbol, vector, description)
            else:
                # Store vector as string representation if possible, or just skip it
                query = "INSERT INTO ai_memory (symbol, vector, description) VALUES ($1, $2, $3)"
                async with self.pool.acquire() as conn:
                    await conn.execute(query, symbol, str(vector), description)

    async def recall_similar_situations(self, vector: list, limit=3):
        if not self.pool or vector is None: return []
        
        if not self.has_vector:
            # Fallback: Simple keyword search or return empty
            # For now, return empty to avoid errors
            return []

        # Requires vector extension
        query = "SELECT description FROM ai_memory ORDER BY vector <-> $1 LIMIT $2"
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, vector, limit)
                return [r['description'] for r in rows]
        except Exception as e:
            logger.error(f"Recall failed: {e}")
            return []
            
    async def get_recent_opportunities(self, limit=10):
        # Placeholder for Ocean Feed UI if needed, but UI uses JSON file now.
        return []

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db_manager = DatabaseManager()
