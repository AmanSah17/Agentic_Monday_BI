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
            cls._instance.settings = settings
            cls._instance._pool = None
        return cls._instance

    def _init_pool(self):
        """Lazy initialization of the connection pool"""
        if self._pool is not None:
            return
            
        # Quick socket check to avoid long hung TCP connect
        import socket
        try:
            from urllib.parse import urlparse
            url = urlparse(self.settings.postgres_url)
            host = url.hostname or "127.0.0.1"
            port = url.port or 5432
            with socket.create_connection((host, port), timeout=1.0):
                pass
        except Exception as e:
            logger.error(f"PostgreSQL port check failed: {e}")
            self._pool = None
            raise RuntimeError(f"PostgreSQL server not reachable at {host}:{port}")

        try:
            dsn = self.settings.postgres_url
            self._pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, dsn=dsn, connect_timeout=3
            )
            logger.info("PostgreSQL connection pool initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            self._pool = None
            raise # Re-raise to let the caller handle it

    def _init_schema(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # User table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Conversation history with user_id
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id INTEGER REFERENCES users(id),
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Add user_id column if it doesn't exist (for migration)
                cur.execute("ALTER TABLE conversation_history ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);")

                # Error logs with user_id
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id INTEGER REFERENCES users(id),
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Add user_id column if it doesn't exist (for migration)
                cur.execute("ALTER TABLE error_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);")

                cur.execute("CREATE INDEX IF NOT EXISTS idx_history_session ON conversation_history(session_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_errors_session ON error_logs(session_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_errors_user ON error_logs(user_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
                
                conn.commit()
                logger.info("PostgreSQL schema updated with user support.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
        finally:
            self.release_connection(conn)

    def get_connection(self):
        """Get a connection from the pool, with fallback to Mock if pool init failed."""
        if self._pool is None:
            try:
                self._init_pool()
            except Exception as e:
                logger.error(f"PostgreSQL unreachable, using MockConnection fallback: {e}")
                return MockConnection()

        try:
            return self._pool.getconn()
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            return MockConnection()

    def release_connection(self, conn):
        if isinstance(conn, MockConnection):
            return
        if self._pool:
            self._pool.putconn(conn)

class MockConnection:
    """A mock connection that prevents crashes if DB is down."""
    _users = {} # Shared across instances for consistency in a session

    def cursor(self): return MockCursor(self._users)
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

class MockCursor:
    def __init__(self, users_ref):
        self.users = users_ref
        self.last_query = None
        self.last_params = None
        self.current_result = None

    def execute(self, query, params=None): 
        self.last_query = query
        self.last_params = params
        
        q = query.lower()
        if "select" in q and "users" in q:
            username = params[0] if params else None
            if username in self.users:
                u = self.users[username]
                # Return (id, username, password_hash, email) or subsets
                self.current_result = (1, u['username'], u['password_hash'], u.get('email', ''))
            else:
                self.current_result = None
        elif "insert" in q and "users" in q:
            username, pw_hash, email = params
            self.users[username] = {"username": username, "password_hash": pw_hash, "email": email}
            self.current_result = (1, username, email)
        else:
            self.current_result = None

    def fetchone(self): 
        return self.current_result
        
    def fetchall(self): 
        return [self.current_result] if self.current_result else []

    def get(self, name, default=None):
        """Diagnostic method to find who is calling .get() on a cursor"""
        logger.error(f"DIAGNOSTIC: .get('{name}') called on MockCursor! Query: {self.last_query}")
        if isinstance(self.current_result, dict):
            return self.current_result.get(name, default)
        return default

    def __enter__(self): return self
    def __exit__(self, *args): pass
    def close(self): pass

# Move this to PostgresManager
def close_all_pools():
    if PostgresManager._instance and PostgresManager._instance._pool:
        PostgresManager._instance._pool.closeall()
        logger.info("PostgreSQL connection pool closed.")
