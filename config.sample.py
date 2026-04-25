import os

class Config:
    # YouTube Configuration
    # (Any YouTube API keys or other settings could go here)
    
    # PostgreSQL Configuration
    DB_NAME = os.getenv("DB_NAME", "yt_stats")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "admin123")
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me")
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Admin Credentials
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123") # For form login

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

config = Config()
