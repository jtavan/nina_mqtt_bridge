"""Home Assistant MQTT discovery helpers."""

from __future__ import annotations

import json
from typing import Iterable, List, Tuple

from .config import BridgeConfig
from .device_model import (
    DEVICE_SENSORS,
    SensorDef,
    device_identifier,
    device_payload,
)
from .mqtt_client import PublishMessage

STATE_TOPIC_TEMPLATE = "{base}/{device}/{variable}"
IMAGE_TOPIC_TEMPLATE = "{base}/{device}/image"

IMAGE_DEVICES = {"livestack", "most_recent_image", "screenshot"}


def _iter_sensor_definitions(
    device: str, extra_keys: Iterable[str] | None = None
) -> Iterable[Tuple[str, SensorDef]]:
    base_defs = DEVICE_SENSORS.get(device, {})
    for key, definition in base_defs.items():
        yield key, definition

    for key in extra_keys or []:
        if key in base_defs:
            continue
        # Generic definition for dynamic switch fields.
        if device == "switch":
            yield (
                key,
                SensorDef(name=key.replace("_", " ").title(), icon="mdi:toggle-switch"),
            )


def build_sensor_discovery_messages(
    config: BridgeConfig,
    device: str,
    refresh_every: int,
    extra_keys: Iterable[str] | None = None,
) -> List[PublishMessage]:
    messages: List[PublishMessage] = []
    topics = config.mqtt.topics
    base = topics.base_topic
    discovery_prefix = topics.discovery_prefix.rstrip("/")
    device_id = device_identifier(config.device_info, device)
    device_info_payload = device_payload(config.device_info, device)
    availability_topic = topics.render_device_availability_topic(device)

    for variable, definition in _iter_sensor_definitions(device, extra_keys):
        platform = (
            "binary_sensor" if definition.platform == "binary_sensor" else "sensor"
        )
        discovery_topic = f"{discovery_prefix}/{platform}/{device_id}/{variable}/config"
        state_topic = STATE_TOPIC_TEMPLATE.format(
            base=base, device=device, variable=variable
        )

        payload = {
            "name": definition.name
            or f"{device.title()} {variable.replace('_', ' ').title()}",
            "state_topic": state_topic,
            "unique_id": f"{device_id}_{variable}",
            "availability_topic": availability_topic,
            "payload_available": "ON",
            "payload_not_available": "OFF",
            "device": device_info_payload,
        }

        if platform == "binary_sensor":
            payload["payload_on"] = "true"
            payload["payload_off"] = "false"

        if definition.unit:
            payload["unit_of_measurement"] = definition.unit
        if definition.device_class:
            payload["device_class"] = definition.device_class
        if definition.state_class:
            payload["state_class"] = definition.state_class
        if definition.icon:
            payload["icon"] = definition.icon
        if refresh_every > 0:
            payload["expire_after"] = int(refresh_every * 2.2)

        messages.append(
            PublishMessage(
                topic=discovery_topic, payload=json.dumps(payload), retain=True, qos=1
            )
        )

    return messages


def build_image_discovery_message(config: BridgeConfig, device: str) -> PublishMessage:
    topics = config.mqtt.topics
    base = topics.base_topic
    discovery_prefix = topics.discovery_prefix.rstrip("/")
    device_id = device_identifier(config.device_info, device)
    device_info_payload = device_payload(config.device_info, device)
    availability_topic = topics.render_device_availability_topic(device)

    object_id = device_id
    discovery_topic = f"{discovery_prefix}/camera/{object_id}/config"
    payload = {
        "name": f"NINA {device.replace('_', ' ').title()}",
        "unique_id": device_id,
        "topic": IMAGE_TOPIC_TEMPLATE.format(base=base, device=device),
        "content_type": "image/jpeg",
        "availability_topic": availability_topic,
        "payload_available": "ON",
        "payload_not_available": "OFF",
        "device": device_info_payload,
    }

    return PublishMessage(
        topic=discovery_topic, payload=json.dumps(payload), retain=True, qos=1
    )
