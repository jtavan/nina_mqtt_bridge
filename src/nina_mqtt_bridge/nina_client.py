"""HTTP client wrapper around the NINA Advanced API."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# Mappings derived from the published Advanced API OpenAPI spec.
DEVICE_ENDPOINTS = {
    "application": "/version",
    "camera": "/equipment/camera/info",
    "mount": "/equipment/mount/info",
    "dome": "/equipment/dome/info",
    "filterwheel": "/equipment/filterwheel/info",
    "flatdevice": "/equipment/flatdevice/info",
    "focuser": "/equipment/focuser/info",
    "guider": "/equipment/guider/info",
    "rotator": "/equipment/rotator/info",
    "safetymonitor": "/equipment/safetymonitor/info",
    "sequence": "/sequence/json",
    "switch": "/equipment/switch/info",
    "weather": "/equipment/weather/info",
}

# Images use dedicated helper methods.
IMAGE_ENDPOINTS = {
    "most_recent_image": "/prepared-image",
    "livestack": "/livestack/image/{target}/{filter}",
    "screenshot": "/application/screenshot",
}


class NINAClient:
    """Lightweight client for interacting with the NINA Advanced API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def close(self) -> None:
        self._session.close()

    def fetch_device_status(self, device: str) -> Dict[str, Any]:
        """Pull the status block for a specific device type."""
        if device == "application":
            version = self._get_json("/version")
            app_start = self._get_json("/application-start")
            response = version.get("Response") if isinstance(version, dict) else version
            start_time = (
                app_start.get("Response") if isinstance(app_start, dict) else app_start
            )
            return {
                "nina_version": response,
                "api_version": response,
                "application_start": start_time,
            }

        if device not in DEVICE_ENDPOINTS:
            raise ValueError(f"Unsupported device type: {device}")
        return self._get_json(DEVICE_ENDPOINTS[device])

    def fetch_image(self, image_type: str) -> Optional[bytes]:
        """
        Retrieve the latest prepared image or livestack image.

        Prepared images come from /prepared-image with autoPrepare enabled.
        Livestack images are fetched by first discovering available stacks and
        then streaming the most recent target/filter combination.
        """

        try:
            if image_type == "most_recent_image":
                return self._get_bytes(
                    IMAGE_ENDPOINTS["most_recent_image"],
                    params={"autoPrepare": "true", "stream": "true"},
                )
            if image_type == "livestack":
                return self._fetch_livestack_image()
            if image_type == "screenshot":
                return self._get_bytes(
                    "/application/screenshot",
                    params={"stream": "true"},
                )
        except requests.HTTPError:
            logger.exception("Image fetch failed for %s", image_type)
            return None

        raise ValueError(f"Unsupported image type: {image_type}")

    def send_command(self, device: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch control commands to NINA.

        Supported:
          - sequence: action=start|stop|reset (restart) with optional skipValidation
          - mount: action=home|park|unpark|tracking (mode required)
          - application/screenshot: action=screenshot (returns base64 image)
        """

        action = (payload.get("action") or "").lower()
        if device == "sequence":
            return self._handle_sequence_command(action, payload)
        if device == "mount":
            return self._handle_mount_command(action, payload)
        if device in ("application", "screenshot"):
            return self._handle_screenshot_command(payload)

        raise ValueError(f"Unsupported command target: {device}")

    def _handle_sequence_command(
        self, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if action == "start":
            params = {"skipValidation": payload.get("skipValidation", False)}
            return self._get_json("/sequence/start", params=params)
        if action == "stop":
            return self._get_json("/sequence/stop")
        if action in ("reset", "restart"):
            return self._get_json("/sequence/reset")
        raise ValueError(f"Unsupported sequence action: {action}")

    def _handle_mount_command(
        self, action: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if action == "home":
            return self._get_json("/equipment/mount/home")
        if action == "park":
            return self._get_json("/equipment/mount/park")
        if action == "unpark":
            return self._get_json("/equipment/mount/unpark")
        if action in ("tracking", "track", "set_tracking"):
            mode_value = self._parse_tracking_mode(payload.get("mode"))
            return self._get_json(
                "/equipment/mount/tracking", params={"mode": mode_value}
            )
        raise ValueError(f"Unsupported mount action: {action}")

    def _handle_screenshot_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Default to streaming binary back, encoded as base64 so it is JSON serializable.
        params: Dict[str, Any] = {"stream": "true"}
        for key in ("resize", "quality", "size", "scale"):
            if key in payload:
                params[key] = payload[key]
        image_bytes = self._get_bytes("/application/screenshot", params=params)
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return {"image_base64": encoded}

    def _parse_tracking_mode(self, mode: Any) -> int:
        if isinstance(mode, int):
            if 0 <= mode <= 4:
                return mode
        if isinstance(mode, str):
            normalized = mode.strip().lower()
            mapping = {
                "sidereal": 0,
                "siderial": 0,
                "lunar": 1,
                "moon": 1,
                "solar": 2,
                "sun": 2,
                "king": 3,
                "stop": 4,
                "stopped": 4,
                "off": 4,
            }
            if normalized in mapping:
                return mapping[normalized]
            if normalized.isdigit():
                numeric = int(normalized)
                if 0 <= numeric <= 4:
                    return numeric
        raise ValueError(
            "Invalid tracking mode; expected 0-4 or sidereal/lunar/solar/king/stopped"
        )

    def _fetch_livestack_image(self) -> Optional[bytes]:
        available = self._get_json("/livestack/image/available")
        stacks = available.get("Response") if isinstance(available, dict) else None
        stacks = stacks or []
        if not stacks:
            logger.debug("No livestack images available")
            return None

        latest = stacks[0]
        target = latest.get("Target") or latest.get("target")
        filter_name = latest.get("Filter") or latest.get("filter")
        if not target or not filter_name:
            logger.debug("Livestack entry missing target or filter: %s", latest)
            return None

        path = f"/livestack/image/{quote(str(target))}/{quote(str(filter_name))}"
        return self._get_bytes(path, params={"stream": "true"})

    def _get_json(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response = self._session.get(
            f"{self._base_url}{path}", params=params, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _get_bytes(self, path: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        response = self._session.get(
            f"{self._base_url}{path}", params=params, timeout=10
        )
        response.raise_for_status()
        return response.content

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._session.post(
            f"{self._base_url}{path}",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return {}
