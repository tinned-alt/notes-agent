"""Configuration management for the notes agent."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    # Mark as optional to avoid static analyzers requiring constructor args.
    # We still validate at runtime in get_settings().
    anthropic_api_key: Optional[str] = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY"
    )

    # Paths
    # Make optional for construction-time compatibility with static analysis
    # (validate at runtime in get_settings()).
    obsidian_vault_path: Optional[Path] = Field(
        default=None, validation_alias="OBSIDIAN_VAULT_PATH"
    )
    vector_store_path: Path = Field(
        default=Path("./data/chroma_db"),
        validation_alias="VECTOR_STORE_PATH"
    )

    # Model configuration
    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        validation_alias="CLAUDE_MODEL"
    )

    # Agent configuration
    max_iterations: int = Field(default=10, validation_alias="MAX_ITERATIONS")
    temperature: float = Field(default=0.7, validation_alias="TEMPERATURE")

    class Config:
        env_file = [
            ".env",  # Local directory
            str(Path.home() / ".config" / "obsidian-notes-agent" / "config.env"),  # User config
        ]
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    """Get application settings."""
    settings = Settings()

    # Runtime validation: ensure required settings are present and valid.
    missing = []
    if not settings.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY (anthropic_api_key)")
    if not settings.obsidian_vault_path:
        missing.append("OBSIDIAN_VAULT_PATH (obsidian_vault_path)")

    if missing:
        raise RuntimeError(
            "Missing required configuration: " + ", ".join(missing)
        )

    # Ensure obsidian_vault_path is a Path instance (pydantic may have left it as str)
    if isinstance(settings.obsidian_vault_path, str):
        settings.obsidian_vault_path = Path(settings.obsidian_vault_path)

    return settings
