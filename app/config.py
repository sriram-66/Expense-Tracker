import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expenses.db")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))
