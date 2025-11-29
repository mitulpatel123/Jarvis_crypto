import asyncio
import asyncpg
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_db():
    dsn = os.getenv("DATABASE_URL", "postgresql://mitulpatel@localhost/jarvis_crypto")
    
    try:
        # Connect to the default 'postgres' database first to check if target db exists
        # We might need to adjust this if the user doesn't have a default postgres db
        # For now, let's try connecting directly to the target DB.
        # If it fails, the user might need to create it.
        
        logger.info(f"🔌 Connecting to database: {dsn}")
        conn = await asyncpg.connect(dsn)
        
        logger.info("✅ Connected successfully.")
        
        # Create Vector Extension
        logger.info("🛠  Creating 'vector' extension...")
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("✅ Extension 'vector' created/verified.")
        except Exception as e:
            logger.error(f"❌ Failed to create extension 'vector': {e}")
            logger.info("💡 Hint: You might need superuser privileges or install pgvector manually.")
            logger.info("   Mac: brew install postgresql")
            logger.info("        brew services start postgresql")
            logger.info("        git clone --branch v0.4.4 https://github.com/pgvector/pgvector.git")
            logger.info("        cd pgvector && make && make install")

        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.info("💡 Ensure PostgreSQL is running and the database 'jarvis_crypto' exists.")
        logger.info("   To create DB: createdb jarvis_crypto")

if __name__ == "__main__":
    asyncio.run(setup_db())
