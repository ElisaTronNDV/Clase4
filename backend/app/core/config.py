import os


class Settings:
    def __init__(self) -> None:
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            raise RuntimeError(
                "SECRET_KEY no está configurada. Definila como variable de entorno "
                "(ver backend/.env.example) antes de iniciar la aplicación."
            )
        self.secret_key: str = secret_key
        self.database_url: str = os.environ.get(
            "DATABASE_URL", "sqlite:///./dyp_lasercore.db"
        )
        self.cors_origins: list[str] = [
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",")
            if origin.strip()
        ]
        self.algorithm: str = "HS256"
        self.access_token_expire_minutes: int = 24 * 60


settings = Settings()
