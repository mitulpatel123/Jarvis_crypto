import sqlite3
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="data/jarvis.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def connect(self):
        """Connect to the database (SQLite doesn't need a pool, but we keep interface)."""
        logger.info(f"Using SQLite database at {self.db_path}")
        await self._init_tables()

    async def disconnect(self):
        """No-op for SQLite in this simple implementation."""
        pass

    async def _init_tables(self):
        """Initialize necessary tables."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS ohlc_data (
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (symbol, timestamp)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL,
                exit_price REAL,
                quantity REAL,
                profit_loss REAL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                status TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS agent_signals (
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL,
                confidence REAL,
                metadata TEXT,
                PRIMARY KEY (timestamp, agent_name, symbol)
            );
            """
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing tables: {e}")

    async def store_ohlc(self, symbol: str, candles: list):
        """Store OHLC candles."""
        query = """
        INSERT INTO ohlc_data (symbol, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, timestamp) DO UPDATE 
        SET open=excluded.open, high=excluded.high, low=excluded.low, 
            close=excluded.close, volume=excluded.volume;
        """
        data = []
        for c in candles:
            ts = c.get('timestamp').isoformat() if isinstance(c.get('timestamp'), datetime) else c.get('timestamp')
            data.append((
                symbol, ts, c.get('open'), c.get('high'), c.get('low'), c.get('close'), c.get('volume')
            ))

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(query, data)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store OHLC data: {e}")

    async def store_trade(self, trade_data: dict):
        query = """
        INSERT INTO trades (symbol, direction, entry_price, exit_price, quantity, profit_loss, entry_time, exit_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (
                    trade_data['symbol'], trade_data['direction'], trade_data['entry_price'],
                    trade_data.get('exit_price'), trade_data['quantity'], trade_data.get('profit_loss'),
                    str(trade_data['entry_time']), str(trade_data.get('exit_time')), trade_data['status']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store trade: {e}")

    async def store_agent_signals(self, signals: list):
        query = """
        INSERT INTO agent_signals (timestamp, agent_name, symbol, signal, confidence, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(timestamp, agent_name, symbol) DO NOTHING
        """
        data = []
        for s in signals:
            meta = json.dumps(s.get('metadata')) if s.get('metadata') else None
            data.append((
                str(s['timestamp']), s['agent_name'], s['symbol'], s['signal'], s['confidence'], meta
            ))
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(query, data)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store signals: {e}")

    async def get_recent_trades(self, limit=50):
        query = "SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY exit_time DESC LIMIT ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch trades: {e}")
            return []

    async def get_agent_signals_at_time(self, timestamp):
        # SQLite doesn't have INTERVAL syntax like Postgres easily, so we do range check in python or simple string compare if exact
        # Ideally store timestamps as ISO strings and compare
        # For now, let's try to match exact or use a range query with string comparison
        # Assuming timestamp is passed as ISO string or datetime
        ts_str = str(timestamp)
        # Simple range: +/- 1 minute logic would require parsing. 
        # For MVP, let's match exact or just return all for that minute if we truncate seconds?
        
        # Let's just fetch signals around that time.
        query = "SELECT agent_name, signal FROM agent_signals WHERE timestamp = ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (ts_str,))
                rows = cursor.fetchall()
                return {r['agent_name']: r['signal'] for r in rows}
        except Exception as e:
            logger.error(f"Failed to fetch signals: {e}")
            return {}

db_manager = DatabaseManager()
