"""
Configuration Management for MCP Accurate Click Server

Provides centralized configuration with environment variable support,
validation, and type safety.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class ServerConfig:
    """Main server configuration"""

    # Server identification
    name: str = "accurate-click-server"
    version: str = "1.0.0"

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None

    # Server behavior
    max_concurrent_requests: int = 10
    request_timeout_seconds: float = 30.0
    enable_debug: bool = False

    # Browser configuration
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    browser_timeout: int = 30000  # milliseconds

    # Click accuracy settings
    click_accuracy_threshold: float = 2.0  # pixels
    enable_adaptive_correction: bool = True
    max_correction_history: int = 100

    # Validation settings
    enable_click_validation: bool = True
    validation_screenshot: bool = True
    validation_timeout: float = 5.0

    # Coordinate transformation
    calibration_points_required: int = 3
    use_ransac: bool = True
    ransac_inlier_threshold: float = 2.0
    ransac_max_iterations: int = 1000

    # Performance
    cache_dom_structure: bool = True
    dom_cache_ttl_seconds: float = 60.0
    enable_batch_processing: bool = True

    # Error handling
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    fallback_to_javascript_click: bool = True

    # Paths
    data_dir: Path = field(default_factory=lambda: Path.home() / ".mcp-accurate-click")
    calibration_dir: Path = field(default_factory=lambda: Path.home() / ".mcp-accurate-click" / "calibrations")
    screenshot_dir: Path = field(default_factory=lambda: Path.home() / ".mcp-accurate-click" / "screenshots")

    def __post_init__(self):
        """Validate and normalize configuration"""
        # Convert string paths to Path objects
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.calibration_dir, str):
            self.calibration_dir = Path(self.calibration_dir)
        if isinstance(self.screenshot_dir, str):
            self.screenshot_dir = Path(self.screenshot_dir)

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")

        self.log_level = self.log_level.upper()

        # Validate browser type
        valid_browsers = ["chromium", "firefox", "webkit"]
        if self.browser_type.lower() not in valid_browsers:
            raise ValueError(f"Invalid browser type: {self.browser_type}. Must be one of {valid_browsers}")

        self.browser_type = self.browser_type.lower()

        # Validate numeric ranges
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least 1")

        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")

        if self.click_accuracy_threshold <= 0:
            raise ValueError("click_accuracy_threshold must be positive")

        if self.calibration_points_required < 3:
            raise ValueError("calibration_points_required must be at least 3")

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables"""
        return cls(
            name=os.getenv("MCP_SERVER_NAME", "accurate-click-server"),
            version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            log_file=os.getenv("MCP_LOG_FILE"),
            max_concurrent_requests=int(os.getenv("MCP_MAX_CONCURRENT", "10")),
            request_timeout_seconds=float(os.getenv("MCP_REQUEST_TIMEOUT", "30.0")),
            enable_debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
            browser_type=os.getenv("MCP_BROWSER_TYPE", "chromium"),
            headless=os.getenv("MCP_HEADLESS", "true").lower() == "true",
            browser_timeout=int(os.getenv("MCP_BROWSER_TIMEOUT", "30000")),
            click_accuracy_threshold=float(os.getenv("MCP_CLICK_ACCURACY", "2.0")),
            enable_adaptive_correction=os.getenv("MCP_ADAPTIVE_CORRECTION", "true").lower() == "true",
            max_correction_history=int(os.getenv("MCP_MAX_CORRECTION_HISTORY", "100")),
            enable_click_validation=os.getenv("MCP_VALIDATION", "true").lower() == "true",
            validation_screenshot=os.getenv("MCP_VALIDATION_SCREENSHOT", "true").lower() == "true",
            validation_timeout=float(os.getenv("MCP_VALIDATION_TIMEOUT", "5.0")),
            calibration_points_required=int(os.getenv("MCP_CALIBRATION_POINTS", "3")),
            use_ransac=os.getenv("MCP_USE_RANSAC", "true").lower() == "true",
            cache_dom_structure=os.getenv("MCP_CACHE_DOM", "true").lower() == "true",
            dom_cache_ttl_seconds=float(os.getenv("MCP_DOM_CACHE_TTL", "60.0")),
            enable_batch_processing=os.getenv("MCP_BATCH_PROCESSING", "true").lower() == "true",
            max_retry_attempts=int(os.getenv("MCP_MAX_RETRIES", "3")),
            retry_delay_seconds=float(os.getenv("MCP_RETRY_DELAY", "1.0")),
            fallback_to_javascript_click=os.getenv("MCP_JS_FALLBACK", "true").lower() == "true",
            data_dir=Path(os.getenv("MCP_DATA_DIR", str(Path.home() / ".mcp-accurate-click"))),
        )

    @classmethod
    def from_file(cls, filepath: str) -> "ServerConfig":
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, filepath: str):
        """Save configuration to JSON file"""
        data = {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
        }

    def setup_logging(self) -> logging.Logger:
        """Configure logging based on settings"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level))

        # Remove existing handlers
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))
        formatter = logging.Formatter(self.log_format)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(getattr(logging, self.log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger


@dataclass
class ToolConfig:
    """Configuration for individual tools"""

    # Tool identification
    name: str
    enabled: bool = True

    # Tool-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)

    # Rate limiting
    rate_limit_requests: Optional[int] = None
    rate_limit_window_seconds: Optional[float] = None

    # Timeouts
    execution_timeout: Optional[float] = None

    # Validation
    require_validation: bool = False

    def __post_init__(self):
        """Validate configuration"""
        if self.rate_limit_requests is not None and self.rate_limit_requests < 1:
            raise ValueError("rate_limit_requests must be at least 1")

        if self.rate_limit_window_seconds is not None and self.rate_limit_window_seconds <= 0:
            raise ValueError("rate_limit_window_seconds must be positive")

        if self.execution_timeout is not None and self.execution_timeout <= 0:
            raise ValueError("execution_timeout must be positive")


class ConfigManager:
    """Centralized configuration manager"""

    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize configuration manager"""
        self.config = config or ServerConfig.from_env()
        self.logger = self.config.setup_logging()
        self.tool_configs: Dict[str, ToolConfig] = {}

    def register_tool_config(self, tool_config: ToolConfig):
        """Register configuration for a tool"""
        self.tool_configs[tool_config.name] = tool_config
        self.logger.info(f"Registered tool configuration: {tool_config.name}")

    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get configuration for a specific tool"""
        return self.tool_configs.get(tool_name)

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled"""
        tool_config = self.get_tool_config(tool_name)
        return tool_config.enabled if tool_config else True

    def reload_config(self, config: ServerConfig):
        """Reload server configuration"""
        self.config = config
        self.logger = self.config.setup_logging()
        self.logger.info("Configuration reloaded")

    def get_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return {
            "server": self.config.to_dict(),
            "tools": {
                name: {
                    "enabled": tc.enabled,
                    "settings": tc.settings,
                    "rate_limit": tc.rate_limit_requests,
                }
                for name, tc in self.tool_configs.items()
            }
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager (singleton)"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config: Optional[ServerConfig] = None) -> ConfigManager:
    """Initialize global configuration"""
    global _config_manager
    _config_manager = ConfigManager(config)
    return _config_manager
