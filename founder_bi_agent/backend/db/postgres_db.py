import psycopg2
from psycopg2 import pool
from founder_bi_agent.backend.core.config import AgentSettings
import logging

logger = logging.getLogger(__name__)

class PostgresManager:
    _instance = None
    _pool = None

    def __new__(cls, settings: AgentSettings):
        if cls._instance is None:
            cls._instance = super(PostgresManager, cls).__new__(cls)
            cls._instance._init_pool(settings)
        return cls._instance

    def _init_pool(self, settings: AgentSettings):
        try:
            # Use the provided URL or construct one
            dsn = settings.postgres_url
            self._pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, dsn=dsn
            )
            logger.info("PostgreSQL connection pool initialized.")
            self._init_schema()
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    def _init_schema(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_history_session ON conversation_history(session_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_errors_session ON error_logs(session_id);")
                conn.commit()
                logger.info("PostgreSQL schema initialized.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
        finally:
            self.release_connection(conn)

    def get_connection(self):
        return self._pool.getconn()

    def release_connection(self, conn):
        self._pool.putconn(conn)

    def close(self):
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL connection pool closed.")
