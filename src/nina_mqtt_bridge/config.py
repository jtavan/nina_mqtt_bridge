"""Configuration loading and defaults for nina_mqtt_bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Defaults taken from PROJECT.md
DEFAULT_NINA_API_URI = "http://127.0.0.1:1888/v2/api"

DEFAULT_MQTT_HOST = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_USERNAME: Optional[str] = None
DEFAULT_MQTT_PASSWORD: Optional[str] = None
DEFAULT_MQTT_CLIENT_ID = "nina_mqtt_bridge"
DEFAULT_MQTT_KEEPALIVE = 60

DEFAULT_DISCOVERY_PREFIX = "homeassistant"
DEFAULT_BASE_TOPIC = "nina"
DEFAULT_AVAILABILITY_TOPIC_TEMPLATE = "{base}/{device}/availability"
DEFAULT_COMMAND_TOPIC_TEMPLATE = "{base}/{device}/command"
DEFAULT_COMMAND_ERROR_TOPIC_TEMPLATE = "{base}/{device}/command/error"
DEFAULT_COMMAND_RESPONSE_TIMEOUT = 10

# Home Assistant device info defaults
DEFAULT_DEVICE_ID = "nina_server"
DEFAULT_DEVICE_NAME = "NINA Advanced API"
DEFAULT_DEVICE_MANUFACTURER = "christian-photo"
DEFAULT_DEVICE_MODEL = "NINA Advanced API"

# Device refresh defaults
DEFAULT_REFRESH_SECONDS = 60
DEFAULT_DEVICE_TYPES = [
    "application",
    "camera",
    "mount",
    "dome",
    "filterwheel",
    "flatdevice",
    "focuser",
    "guider",
    "rotator",
    "safetymonitor",
    "sequence",
    "switch",
    "weather",
    "livestack",
    "most_recent_image",
    "screenshot",
]


@dataclass
class DeviceConfig:
    """Polling configuration for a given NINA device class."""

    enabled: bool = True
    refresh_every: int = DEFAULT_REFRESH_SECONDS


@dataclass
class NINAConfig:
    """Connection settings for the NINA Advanced API."""

    api_uri: str = DEFAULT_NINA_API_URI


@dataclass
class MQTTTopicConfig:
    """MQTT topic templates and timing."""

    discovery_prefix: str = DEFAULT_DISCOVERY_PREFIX
    base_topic: str = DEFAULT_BASE_TOPIC
    availability_topic: str = DEFAULT_AVAILABILITY_TOPIC_TEMPLATE
    command_topic: str = DEFAULT_COMMAND_TOPIC_TEMPLATE
    command_error_topic: str = DEFAULT_COMMAND_ERROR_TOPIC_TEMPLATE
    command_response_timeout: int = DEFAULT_COMMAND_RESPONSE_TIMEOUT

    def render_availability_topic(self, device: str | None = None) -> str:
        device_slug = device or "bridge"
        return self.availability_topic.format(base=self.base_topic, device=device_slug)

    def render_device_availability_topic(self, device: str) -> str:
        return self.render_availability_topic(device=device)

    def render_command_topic(self, device: str) -> str:
        return self.command_topic.format(base=self.base_topic, device=device)

    def render_command_error_topic(self, device: str) -> str:
        return self.command_error_topic.format(base=self.base_topic, device=device)


@dataclass
class MQTTConfig:
    """Connection settings for MQTT."""

    host: str = DEFAULT_MQTT_HOST
    port: int = DEFAULT_MQTT_PORT
    username: Optional[str] = DEFAULT_MQTT_USERNAME
    password: Optional[str] = DEFAULT_MQTT_PASSWORD
    client_id: str = DEFAULT_MQTT_CLIENT_ID
    keepalive: int = DEFAULT_MQTT_KEEPALIVE
    topics: MQTTTopicConfig = field(default_factory=MQTTTopicConfig)


@dataclass
class DeviceInfo:
    """Home Assistant device metadata."""

    device_id: str = DEFAULT_DEVICE_ID
    name: str = DEFAULT_DEVICE_NAME
    manufacturer: str = DEFAULT_DEVICE_MANUFACTURER
    model: str = DEFAULT_DEVICE_MODEL


@dataclass
class BridgeConfig:
    """Top-level configuration object."""

    nina: NINAConfig = field(default_factory=NINAConfig)
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    devices: Dict[str, DeviceConfig] = field(default_factory=dict)
    device_info: DeviceInfo = field(default_factory=DeviceInfo)


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _build_devices(config: Dict[str, Any]) -> Dict[str, DeviceConfig]:
    devices_section = config.get("devices", {}) or {}
    devices: Dict[str, DeviceConfig] = {}
    for device in DEFAULT_DEVICE_TYPES:
        raw = devices_section.get(device, {})
        enabled = raw.get("enabled", True)
        refresh_every = int(raw.get("refresh_every", DEFAULT_REFRESH_SECONDS))
        if refresh_every <= 0:
            raise ValueError(f"refresh_every must be positive for device '{device}'")
        devices[device] = DeviceConfig(enabled=enabled, refresh_every=refresh_every)
    return devices


def load_config(path: Path) -> BridgeConfig:
    """
    Load configuration from a YAML file, applying defaults from PROJECT.md.

    This is intentionally forgiving: missing sections are filled with defaults.
    """

    data = _load_yaml(path)

    nina_cfg = NINAConfig(
        api_uri=data.get("nina", {}).get("api_uri", DEFAULT_NINA_API_URI)
    )

    mqtt_section = data.get("mqtt", {}) or {}
    topics_section = mqtt_section.get("topics", {}) or {}
    topics_cfg = MQTTTopicConfig(
        discovery_prefix=topics_section.get(
            "discovery_prefix", DEFAULT_DISCOVERY_PREFIX
        ),
        base_topic=topics_section.get("base_topic", DEFAULT_BASE_TOPIC),
        availability_topic=topics_section.get(
            "availability_topic", DEFAULT_AVAILABILITY_TOPIC_TEMPLATE
        ),
        command_topic=topics_section.get(
            "command_topic", DEFAULT_COMMAND_TOPIC_TEMPLATE
        ),
        command_error_topic=topics_section.get(
            "command_error_topic", DEFAULT_COMMAND_ERROR_TOPIC_TEMPLATE
        ),
        command_response_timeout=int(
            topics_section.get(
                "command_response_timeout", DEFAULT_COMMAND_RESPONSE_TIMEOUT
            )
        ),
    )

    mqtt_cfg = MQTTConfig(
        host=mqtt_section.get("host", DEFAULT_MQTT_HOST),
        port=int(mqtt_section.get("port", DEFAULT_MQTT_PORT)),
        username=mqtt_section.get("username", DEFAULT_MQTT_USERNAME),
        password=mqtt_section.get("password", DEFAULT_MQTT_PASSWORD),
        client_id=mqtt_section.get("client_id", DEFAULT_MQTT_CLIENT_ID),
        keepalive=int(mqtt_section.get("keepalive", DEFAULT_MQTT_KEEPALIVE)),
        topics=topics_cfg,
    )

    device_info_section = data.get("device_info", {}) or {}
    device_info = DeviceInfo(
        device_id=device_info_section.get("device_id", DEFAULT_DEVICE_ID),
        name=device_info_section.get("name", DEFAULT_DEVICE_NAME),
        manufacturer=device_info_section.get(
            "manufacturer", DEFAULT_DEVICE_MANUFACTURER
        ),
        model=device_info_section.get("model", DEFAULT_DEVICE_MODEL),
    )

    devices = _build_devices(data)

    return BridgeConfig(
        nina=nina_cfg,
        mqtt=mqtt_cfg,
        devices=devices,
        device_info=device_info,
    )


def load_config_from_cli(path_str: str) -> BridgeConfig:
    """Helper for CLI usage."""

    config_path = Path(path_str).expanduser()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return load_config(config_path)
