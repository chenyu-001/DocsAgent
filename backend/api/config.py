"""
Configuration Module
Uses pydantic-settings for configuration management
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application Configuration"""

    # ========== Application Base Configuration ==========
    APP_NAME: str = "DocsAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # ========== Database Configuration ==========
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="docsagent", description="Database name")
    POSTGRES_USER: str = Field(default="docsagent", description="Database user")
    POSTGRES_PASSWORD: str = Field(default="docsagent_password", description="Database password")

    @property
    def database_url(self) -> str:
        """Database connection URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ========== Qdrant Vector Database Configuration ==========
    QDRANT_HOST: str = Field(default="localhost", description="Qdrant host")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant port")
    QDRANT_COLLECTION: str = Field(default="documents", description="Qdrant collection name")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant API Key (optional)")

    @property
    def qdrant_url(self) -> str:
        """Qdrant connection URL"""
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

    # ========== JWT Authentication Configuration ==========
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-please-change-this",
        description="JWT secret key - MUST CHANGE IN PRODUCTION"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=1440, description="Token expiration time in minutes")

    # ========== Embedding Model Configuration ==========
    EMBEDDING_MODEL_TYPE: str = Field(
        default="bge",
        description="Embedding model type: bge | openai | custom"
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-large-zh-v1.5",
        description="Embedding model name"
    )
    EMBEDDING_DIMENSION: int = Field(default=1024, description="Vector dimension")
    EMBEDDING_BATCH_SIZE: int = Field(default=32, description="Batch size")
    EMBEDDING_DEVICE: str = Field(default="cpu", description="Device: cpu | cuda")
    HF_ENDPOINT: Optional[str] = Field(
        default=None,
        description="Optional Hugging Face endpoint override (e.g. https://hf-mirror.com)",
    )

    @field_validator('HF_ENDPOINT', mode='before')
    @classmethod
    def validate_hf_endpoint(cls, v):
        """Convert empty string to None to avoid URL construction issues"""
        if isinstance(v, str) and not v.strip():
            return None
        return v

    # OpenAI Embeddings Configuration (optional)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_API_BASE: Optional[str] = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )

    # ========== LLM Configuration ==========
    LLM_TYPE: str = Field(
        default="qwen",
        description="LLM type: qwen | openai | claude | custom"
    )
    LLM_API_BASE: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="LLM API base URL"
    )
    LLM_API_KEY: Optional[str] = Field(default=None, description="LLM API Key")
    LLM_MODEL_NAME: str = Field(default="qwen-plus", description="LLM model name")
    LLM_TEMPERATURE: float = Field(default=0.7, description="Temperature")
    LLM_MAX_TOKENS: int = Field(default=2000, description="Max output tokens")
    LLM_TIMEOUT: int = Field(default=60, description="API timeout in seconds")

    # ========== Reranker Configuration ==========
    ENABLE_RERANKER: bool = Field(default=True, description="Enable reranker")
    RERANKER_MODEL_NAME: str = Field(
        default="BAAI/bge-reranker-large",
        description="Reranker model name"
    )
    RERANKER_TOP_K: int = Field(default=10, description="Reranker top K results")

    # ========== File Storage Configuration ==========
    STORAGE_PATH: str = Field(default="./storage", description="File storage root directory")
    MAX_FILE_SIZE: int = Field(default=100, description="Max file size in MB")
    ALLOWED_EXTENSIONS: list[str] = Field(
        default=[".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".html"],
        description="Allowed file extensions"
    )

    @property
    def upload_path(self) -> str:
        """Upload file storage path"""
        return f"{self.STORAGE_PATH}/uploads"

    @property
    def parsed_path(self) -> str:
        """Parsed file storage path"""
        return f"{self.STORAGE_PATH}/parsed"

    @property
    def preview_path(self) -> str:
        """Preview file storage path"""
        return f"{self.STORAGE_PATH}/previews"

    # ========== Text Chunking Configuration ==========
    CHUNK_SIZE: int = Field(default=500, description="Chunk size in characters")
    CHUNK_OVERLAP: int = Field(default=50, description="Chunk overlap size")

    # ========== Search Configuration ==========
    RETRIEVAL_TOP_K: int = Field(default=20, description="Initial retrieval top K")
    FINAL_TOP_K: int = Field(default=5, description="Final top K results")
    MIN_SCORE: float = Field(default=0.3, description="Minimum similarity score")

    # ========== Logging Configuration ==========
    LOG_PATH: str = Field(default="./logs", description="Log file storage path")
    LOG_ROTATION: str = Field(default="1 day", description="Log rotation period")
    LOG_RETENTION: str = Field(default="30 days", description="Log retention period")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Print configuration information (for debugging)
def print_settings():
    """Print main configuration information"""
    print(f"=== {settings.APP_NAME} v{settings.APP_VERSION} ===")
    print(f"Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"Qdrant: {settings.qdrant_url}")
    print(f"Embedding: {settings.EMBEDDING_MODEL_TYPE} - {settings.EMBEDDING_MODEL_NAME}")
    print(f"LLM: {settings.LLM_TYPE} - {settings.LLM_MODEL_NAME}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")


if __name__ == "__main__":
    print_settings()
