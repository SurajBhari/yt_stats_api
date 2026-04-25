import psycopg2
from psycopg2 import pool
from config import config

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 20,
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT
            )
            print("PostgreSQL connection pool created successfully")
        except Exception as e:
            print(f"Error creating PostgreSQL connection pool: {e}")
            raise

    def get_connection(self):
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        self.connection_pool.putconn(conn)

    def init_db(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chats (
                        id SERIAL PRIMARY KEY,
                        channel_id TEXT NOT NULL,
                        stream_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        user_avatar TEXT,
                        message_timestamp FLOAT,
                        message_origin_time FLOAT,
                        message_content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_channel_id ON chats(channel_id);
                    CREATE INDEX IF NOT EXISTS idx_stream_id ON chats(stream_id);
                    CREATE INDEX IF NOT EXISTS idx_user_id ON chats(user_id);
                """)
                conn.commit()
        finally:
            self.return_connection(conn)

db = Database()
