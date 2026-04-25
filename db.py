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
                # Table for chat messages
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
                
                # Table for tracked channels
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT,
                        status TEXT DEFAULT 'pending', -- pending, approved, disabled
                        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_channel_status ON channels(status);
                """)

                # Table for users
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        role TEXT DEFAULT 'user', -- admin, user
                        google_id TEXT UNIQUE,
                        youtube_id TEXT, -- Added for YT channel association
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Seed admin user if not exists
                cursor.execute("SELECT 1 FROM users WHERE role = 'admin'")
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO users (email, name, role) VALUES (%s, %s, %s)",
                        ("admin@stats.com", "System Admin", "admin")
                    )
                
                conn.commit()
        finally:
            self.return_connection(conn)

db = Database()
