"""Bridge orchestration: polling NINA and publishing via MQTT."""

from __future__ import annotations

import json
import logging
import queue
import threading
from functools import partial
from typing import Optional

from .config import BridgeConfig
from .device_model import DEVICE_SENSORS, extract_state_values
from .discovery import (
    IMAGE_DEVICES,
    IMAGE_TOPIC_TEMPLATE,
    STATE_TOPIC_TEMPLATE,
    build_image_discovery_message,
    build_sensor_discovery_messages,
)
from .mqtt_client import MQTTClient, PublishMessage
from .nina_client import DEVICE_ENDPOINTS, IMAGE_ENDPOINTS, NINAClient
from .scheduler import ScheduledTask, Scheduler

logger = logging.getLogger(__name__)


class Bridge:
    """Coordinates NINA polling and MQTT publishing."""

    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self.nina = NINAClient(config.nina.api_uri)
        self.mqtt = MQTTClient(config.mqtt)
        self.scheduler = Scheduler()
        self._publish_queue: queue.Queue[PublishMessage] = queue.Queue()
        self._stop_event = threading.Event()
        self._publisher_thread: Optional[threading.Thread] = None
        self._published_discovery_topics: set[str] = set()

    def start(self) -> None:
        self._configure_mqtt()
        self._subscribe_commands()
        self._publish_discovery()
        self._start_publisher()
        self._schedule_polls()
        self.scheduler.start()

    def stop(self) -> None:
        logger.info("Stopping bridge")
        # Stop scheduling new work but allow publisher to drain queued messages.
        self.scheduler.stop()
        self._publish_all_device_availability("OFF")
        self._publish_availability("OFF")
        self._stop_event.set()
        if self._publisher_thread:
            self._publisher_thread.join(timeout=5)
        self.mqtt.disconnect()
        self.nina.close()

    def _configure_mqtt(self) -> None:
        availability_topic = self.config.mqtt.topics.render_availability_topic()
        self.mqtt.set_lwt(availability_topic, payload="OFF")
        self.mqtt.connect()
        self._publish_availability("ON")

    def _subscribe_commands(self) -> None:
        base = self.config.mqtt.topics.base_topic
        command_topic = self.config.mqtt.topics.command_topic.format(
            base=base, device="+"
        )
        logger.info("Subscribing to command topic %s", command_topic)
        self.mqtt.subscribe(command_topic, handler=self._handle_command)

    def _handle_command(self, _client, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            logger.warning("Invalid command payload on %s", msg.topic)
            return
        parts = msg.topic.split("/")
        device = parts[-2] if len(parts) >= 2 else "unknown"
        logger.info("Received command for %s: %s", device, payload)
        try:
            response = self.nina.send_command(device, payload)
            if response:
                state_topic = STATE_TOPIC_TEMPLATE.format(
                    base=self.config.mqtt.topics.base_topic,
                    device=device,
                    variable="command_response",
                )
                self._publish_queue.put(
                    PublishMessage(
                        topic=state_topic,
                        payload=json.dumps(response),
                        retain=False,
                        qos=0,
                    )
                )
        except Exception as exc:  # pragma: no cover - logs capture issue
            logger.exception("Command handling failed for %s", device)
            error_topic = self.config.mqtt.topics.render_command_error_topic(device)
            self._publish_queue.put(
                PublishMessage(
                    topic=error_topic,
                    payload=str(exc),
                    retain=False,
                    qos=0,
                )
            )

    def _start_publisher(self) -> None:
        self._publisher_thread = threading.Thread(
            target=self._publisher_loop, name="mqtt_publisher", daemon=True
        )
        self._publisher_thread.start()

    def _schedule_polls(self) -> None:
        for device_name, device_cfg in self.config.devices.items():
            if not device_cfg.enabled:
                logger.info("Device %s disabled; skipping", device_name)
                continue
            if device_name in IMAGE_ENDPOINTS or device_name in IMAGE_DEVICES:
                task_fn = partial(self._poll_image, device_name)
            else:
                task_fn = partial(self._poll_device, device_name)
            self.scheduler.add_task(
                ScheduledTask(
                    name=f"poll_{device_name}",
                    interval=float(device_cfg.refresh_every),
                    fn=task_fn,
                )
            )

    def _poll_device(self, device: str) -> None:
        if device not in DEVICE_ENDPOINTS:
            logger.debug("Skipping unsupported device %s", device)
            return

        availability_topic = self.config.mqtt.topics.render_device_availability_topic(
            device
        )
        try:
            logger.debug("Polling device status: %s", device)
            status = self.nina.fetch_device_status(device)
            values = extract_state_values(device, status)

            # Publish dynamic discovery (e.g., switch channels) when first seen.
            self._publish_device_discovery(device, extra_keys=values.keys())

            base_topic = self.config.mqtt.topics.base_topic
            for variable, value in values.items():
                if value is None:
                    continue
                topic = STATE_TOPIC_TEMPLATE.format(
                    base=base_topic, device=device, variable=variable
                )
                self._publish_queue.put(
                    PublishMessage(
                        topic=topic,
                        payload=self._format_value(value),
                        retain=True,
                        qos=0,
                    )
                )

            self._publish_queue.put(
                PublishMessage(
                    topic=availability_topic, payload="ON", retain=True, qos=1
                )
            )
        except Exception:
            logger.exception("Polling device %s failed", device)
            self._publish_queue.put(
                PublishMessage(
                    topic=availability_topic, payload="OFF", retain=True, qos=1
                )
            )

    def _poll_image(self, image_type: str) -> None:
        if image_type not in IMAGE_ENDPOINTS:
            logger.debug("Skipping unsupported image type %s", image_type)
            return
        logger.debug("Polling image: %s", image_type)
        image_bytes = self.nina.fetch_image(image_type)
        availability_topic = self.config.mqtt.topics.render_device_availability_topic(
            image_type
        )
        if image_bytes is None:
            self._publish_queue.put(
                PublishMessage(
                    topic=availability_topic, payload="OFF", retain=True, qos=1
                )
            )
            return

        topic = IMAGE_TOPIC_TEMPLATE.format(
            base=self.config.mqtt.topics.base_topic, device=image_type
        )
        self._publish_queue.put(
            PublishMessage(topic=topic, payload=image_bytes, retain=False, qos=0)
        )
        self._publish_queue.put(
            PublishMessage(topic=availability_topic, payload="ON", retain=True, qos=1)
        )

    def _publisher_loop(self) -> None:
        while not self._stop_event.is_set() or not self._publish_queue.empty():
            try:
                message = self._publish_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self.mqtt.publish(message)
            except Exception:
                logger.exception("MQTT publish failed for %s", message.topic)

    def _publish_availability(self, payload: str) -> None:
        topic = self.config.mqtt.topics.render_availability_topic()
        self._publish_queue.put(
            PublishMessage(topic=topic, payload=payload, retain=True, qos=1)
        )

    def _publish_discovery(self) -> None:
        for device_name, device_cfg in self.config.devices.items():
            if not device_cfg.enabled:
                continue
            self._publish_device_discovery(device_name)

    def _publish_device_discovery(self, device: str, extra_keys=None) -> None:
        extra_keys = list(extra_keys or [])
        messages = []
        if device in IMAGE_DEVICES:
            messages.append(build_image_discovery_message(self.config, device))
        elif device in DEVICE_SENSORS:
            refresh = (
                self.config.devices.get(device).refresh_every
                if device in self.config.devices
                else 60
            )
            messages.extend(
                build_sensor_discovery_messages(
                    self.config,
                    device,
                    refresh_every=refresh,
                    extra_keys=extra_keys,
                )
            )
        else:
            return

        for msg in messages:
            if msg.topic in self._published_discovery_topics:
                continue
            self._published_discovery_topics.add(msg.topic)
            self._publish_queue.put(msg)

    def _publish_all_device_availability(self, payload: str) -> None:
        for device_name, device_cfg in self.config.devices.items():
            if not device_cfg.enabled:
                continue
            topic = self.config.mqtt.topics.render_device_availability_topic(
                device_name
            )
            self._publish_queue.put(
                PublishMessage(topic=topic, payload=payload, retain=True, qos=1)
            )

    @staticmethod
    def _format_value(value: object) -> str | bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
