"""MQTT client helper using paho-mqtt."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from .config import MQTTConfig

logger = logging.getLogger(__name__)


@dataclass
class PublishMessage:
    """Container for outbound MQTT messages."""

    topic: str
    payload: bytes | str
    retain: bool = False
    qos: int = 0


class MQTTClient:
    """Lightweight wrapper around paho-mqtt."""

    def __init__(self, config: MQTTConfig) -> None:
        self._config = config
        self._client = mqtt.Client(client_id=config.client_id)
        if config.username:
            self._client.username_pw_set(config.username, config.password)
        self._connected = False

    def set_lwt(self, availability_topic: str, payload: str) -> None:
        self._client.will_set(availability_topic, payload=payload, qos=1, retain=True)

    def connect(self) -> None:
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        logger.info(
            "Connecting to MQTT broker %s:%s", self._config.host, self._config.port
        )
        self._client.connect(
            self._config.host, self._config.port, keepalive=self._config.keepalive
        )
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, message: PublishMessage) -> None:
        logger.debug(
            "Publishing to %s retain=%s qos=%s",
            message.topic,
            message.retain,
            message.qos,
        )
        result = self._client.publish(
            message.topic,
            payload=message.payload,
            qos=message.qos,
            retain=message.retain,
        )
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.warning(
                "MQTT publish failed for %s: rc=%s", message.topic, result.rc
            )

    def publish_json(
        self, topic: str, payload: dict, retain: bool = False, qos: int = 0
    ) -> None:
        self.publish(
            PublishMessage(
                topic=topic, payload=json.dumps(payload), retain=retain, qos=qos
            )
        )

    def subscribe(
        self, topic: str, handler: Callable[[mqtt.Client, mqtt.MQTTMessage], None]
    ) -> None:
        self._client.subscribe(topic)

        def on_message(
            client: mqtt.Client, _userdata: object, msg: mqtt.MQTTMessage
        ) -> None:
            handler(client, msg)

        self._client.message_callback_add(topic, on_message)

    def _on_connect(
        self, _client: mqtt.Client, _userdata: object, _flags: dict, rc: int
    ) -> None:
        self._connected = rc == 0
        if rc == 0:
            logger.info("Connected to MQTT broker")
        else:
            logger.error("MQTT connection failed: rc=%s", rc)

    def _on_disconnect(self, _client: mqtt.Client, _userdata: object, rc: int) -> None:
        self._connected = False
        logger.info("Disconnected from MQTT broker rc=%s", rc)
