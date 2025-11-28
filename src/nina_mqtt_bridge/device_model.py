"""Definitions for NINA device sensors and helpers to extract values."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

from .config import DeviceInfo


def _normalize(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


@dataclasses.dataclass(frozen=True)
class SensorDef:
    name: Optional[str] = None
    unit: Optional[str] = None
    icon: Optional[str] = None
    device_class: Optional[str] = None
    state_class: Optional[str] = None
    source: Optional[List[str]] = None
    platform: str = "sensor"  # sensor or binary_sensor


DEVICE_SENSORS: Dict[str, Dict[str, SensorDef]] = {
    "application": {
        "nina_version": SensorDef(name="NINA Version", icon="mdi:alpha-n-box"),
        "api_version": SensorDef(name="API Version", icon="mdi:api"),
        "application_start": SensorDef(
            name="Application Start",
            device_class="timestamp",
            icon="mdi:clock-start",
        ),
    },
    "camera": {
        "target_temp": SensorDef(
            name="Target Temperature",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            source=["TargetTemp"],
            icon="mdi:thermometer",
        ),
        "temperature": SensorDef(
            name="Temperature",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            icon="mdi:thermometer",
        ),
        "gain": SensorDef(name="Gain", state_class="measurement", icon="mdi:signal"),
        "binx": SensorDef(name="Bin X", unit="px", icon="mdi:grid"),
        "biny": SensorDef(name="Bin Y", unit="px", icon="mdi:grid"),
        "bitdepth": SensorDef(name="Bit Depth", unit="bit", icon="mdi:binary"),
        "offset": SensorDef(name="Offset", icon="mdi:arrow-collapse-horizontal"),
        "cooler_on": SensorDef(
            name="Cooler On", icon="mdi:snowflake", platform="binary_sensor"
        ),
        "cooler_power": SensorDef(
            name="Cooler Power", unit="%", state_class="measurement", icon="mdi:gauge"
        ),
        "dewheater_on": SensorDef(
            name="Dew Heater On", icon="mdi:radiator", platform="binary_sensor"
        ),
        "is_exposing": SensorDef(
            name="Is Exposing", icon="mdi:camera-timer", platform="binary_sensor"
        ),
        "name": SensorDef(name="Camera Name", icon="mdi:camera"),
        "display_name": SensorDef(name="Camera Display Name", icon="mdi:label"),
        "connected": SensorDef(
            name="Camera Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
    },
    "dome": {
        "shutter_status": SensorDef(
            name="Shutter Status", icon="mdi:garage-open-variant"
        ),
        "at_park": SensorDef(
            name="At Park", icon="mdi:parking", platform="binary_sensor"
        ),
        "at_home": SensorDef(name="At Home", icon="mdi:home", platform="binary_sensor"),
        "driver_following": SensorDef(
            name="Driver Following", icon="mdi:link-variant", platform="binary_sensor"
        ),
        "slewing": SensorDef(
            name="Slewing", icon="mdi:rotate-3d-variant", platform="binary_sensor"
        ),
        "azimuth": SensorDef(
            name="Azimuth",
            unit="°",
            state_class="measurement",
            icon="mdi:compass-outline",
        ),
        "connected": SensorDef(
            name="Dome Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Dome Name", icon="mdi:home-circle"),
        "displayname": SensorDef(name="Dome Display Name", icon="mdi:label"),
        "is_following": SensorDef(
            name="Is Following", icon="mdi:orbit-variant", platform="binary_sensor"
        ),
        "is_synchronized": SensorDef(
            name="Is Synchronized", icon="mdi:sync", platform="binary_sensor"
        ),
    },
    "filterwheel": {
        "connected": SensorDef(
            name="Filter Wheel Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Filter Wheel Name", icon="mdi:filter-variant"),
        "displayname": SensorDef(name="Filter Wheel Display Name", icon="mdi:label"),
        "description": SensorDef(
            name="Filter Wheel Description", icon="mdi:text-box-outline"
        ),
        "is_moving": SensorDef(
            name="Filter Wheel Moving",
            icon="mdi:rotate-3d-variant",
            platform="binary_sensor",
        ),
        "selected_filter_name": SensorDef(name="Selected Filter", icon="mdi:filter"),
        "selected_filter_id": SensorDef(
            name="Selected Filter Id", state_class="measurement", icon="mdi:filter"
        ),
    },
    "flatdevice": {
        "cover_state": SensorDef(name="Cover State", icon="mdi:window-shutter"),
        "light_on": SensorDef(
            name="Light On", icon="mdi:lightbulb-on-outline", platform="binary_sensor"
        ),
        "brightness": SensorDef(
            name="Brightness",
            unit="%",
            state_class="measurement",
            icon="mdi:brightness-6",
        ),
        "connected": SensorDef(
            name="Flat Panel Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Flat Panel Name", icon="mdi:label"),
        "displayname": SensorDef(
            name="Flat Panel Display Name", icon="mdi:label-outline"
        ),
    },
    "focuser": {
        "position": SensorDef(
            name="Position",
            unit="step",
            state_class="measurement",
            icon="mdi:arrow-expand-vertical",
        ),
        "temperature": SensorDef(
            name="Temperature",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            icon="mdi:thermometer",
        ),
        "is_moving": SensorDef(
            name="Is Moving", icon="mdi:swap-vertical", platform="binary_sensor"
        ),
        "is_settling": SensorDef(
            name="Is Settling", icon="mdi:progress-clock", platform="binary_sensor"
        ),
        "temp_comp": SensorDef(
            name="Temperature Compensation",
            icon="mdi:thermometer-auto",
            platform="binary_sensor",
        ),
        "connected": SensorDef(
            name="Focuser Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Focuser Name", icon="mdi:label"),
        "displayname": SensorDef(name="Focuser Display Name", icon="mdi:label-outline"),
    },
    "guider": {
        "connected": SensorDef(
            name="Guider Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Guider Name", icon="mdi:telescope"),
        "displayname": SensorDef(name="Guider Display Name", icon="mdi:label"),
        "rmserror_ra_pixels": SensorDef(
            name="RMS Error RA (px)",
            unit="px",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_ra_arcsec": SensorDef(
            name="RMS Error RA (arcsec)",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_dec_pixels": SensorDef(
            name="RMS Error Dec (px)",
            unit="px",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_dec_arcsec": SensorDef(
            name="RMS Error Dec (arcsec)",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_total_pixels": SensorDef(
            name="RMS Error Total (px)",
            unit="px",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_total_arcsec": SensorDef(
            name="RMS Error Total (arcsec)",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_peak_ra_pixels": SensorDef(
            name="Peak RA Error (px)",
            unit="px",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_peak_ra_arcsec": SensorDef(
            name="Peak RA Error (arcsec)",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_peak_dec_pixels": SensorDef(
            name="Peak Dec Error (px)",
            unit="px",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "rmserror_peak_dec_arcsec": SensorDef(
            name="Peak Dec Error (arcsec)",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-line",
        ),
        "state": SensorDef(name="Guider State", icon="mdi:play-circle"),
    },
    "mount": {
        "tracking_mode": SensorDef(name="Tracking Mode", icon="mdi:orbit-variant"),
        "sidereal_time": SensorDef(
            name="Sidereal Time",
            unit="h",
            state_class="measurement",
            icon="mdi:clock-outline",
        ),
        "right_ascension": SensorDef(
            name="Right Ascension",
            unit="h",
            state_class="measurement",
            icon="mdi:alpha-r-circle",
        ),
        "declination": SensorDef(
            name="Declination",
            unit="°",
            state_class="measurement",
            icon="mdi:alpha-d-circle",
        ),
        "site_latitude": SensorDef(
            name="Site Latitude", unit="°", state_class="measurement", icon="mdi:earth"
        ),
        "site_longitude": SensorDef(
            name="Site Longitude", unit="°", state_class="measurement", icon="mdi:earth"
        ),
        "site_elevation": SensorDef(
            name="Site Elevation",
            unit="m",
            state_class="measurement",
            icon="mdi:image-filter-hdr",
        ),
        "right_ascension_string": SensorDef(name="RA String", icon="mdi:alpha-r-box"),
        "declination_string": SensorDef(name="Dec String", icon="mdi:alpha-d-box"),
        "time_to_flip": SensorDef(
            name="Time To Flip",
            unit="min",
            state_class="measurement",
            icon="mdi:timer-sand",
            source=["TimeToMeridianFlip"],
        ),
        "side_of_pier": SensorDef(name="Side of Pier", icon="mdi:swap-horizontal-bold"),
        "altitude": SensorDef(
            name="Altitude", unit="°", state_class="measurement", icon="mdi:altimeter"
        ),
        "azimuth": SensorDef(
            name="Azimuth",
            unit="°",
            state_class="measurement",
            icon="mdi:compass-outline",
        ),
        "sidereal_time_string": SensorDef(
            name="Sidereal Time String", icon="mdi:clock-outline"
        ),
        "hours_to_meridian": SensorDef(
            name="Hours To Meridian",
            icon="mdi:timer-outline",
            source=["HoursToMeridianString"],
        ),
        "at_park": SensorDef(
            name="At Park", icon="mdi:parking", platform="binary_sensor"
        ),
        "at_home": SensorDef(name="At Home", icon="mdi:home", platform="binary_sensor"),
        "tracking_enabled": SensorDef(
            name="Tracking Enabled", icon="mdi:orbit", platform="binary_sensor"
        ),
        "slewing": SensorDef(
            name="Mount Slewing", icon="mdi:rotate-3d-variant", platform="binary_sensor"
        ),
        "time_to_flip_string": SensorDef(
            name="Time To Flip String",
            icon="mdi:timer-outline",
            source=["TimeToMeridianFlipString"],
        ),
        "is_pulse_guiding": SensorDef(
            name="Pulse Guiding",
            icon="mdi:cursor-default-click-outline",
            platform="binary_sensor",
        ),
        "connected": SensorDef(
            name="Mount Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "utc_date": SensorDef(
            name="UTC Date", device_class="timestamp", icon="mdi:calendar-clock"
        ),
        "name": SensorDef(name="Mount Name", icon="mdi:telescope"),
        "displayname": SensorDef(name="Mount Display Name", icon="mdi:label"),
    },
    "rotator": {
        "mechanical_position": SensorDef(
            name="Mechanical Position",
            unit="°",
            state_class="measurement",
            icon="mdi:rotate-3d",
        ),
        "position": SensorDef(
            name="Position",
            unit="°",
            state_class="measurement",
            icon="mdi:rotate-orbit",
        ),
        "is_moving": SensorDef(
            name="Is Moving", icon="mdi:rotate-right", platform="binary_sensor"
        ),
        "connected": SensorDef(
            name="Rotator Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Rotator Name", icon="mdi:label"),
        "displayname": SensorDef(name="Rotator Display Name", icon="mdi:label-outline"),
    },
    "safetymonitor": {
        "is_safe": SensorDef(
            name="Is Safe",
            icon="mdi:shield-check",
            device_class="safety",
            platform="binary_sensor",
        ),
        "connected": SensorDef(
            name="Safety Monitor Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Safety Monitor Name", icon="mdi:shield"),
        "displayname": SensorDef(name="Safety Monitor Display Name", icon="mdi:label"),
    },
    "sequence": {
        "status": SensorDef(name="Sequence Status", icon="mdi:script-text"),
        "name": SensorDef(name="Sequence Name", icon="mdi:label"),
    },
    "switch": {
        "connected": SensorDef(
            name="Switch Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Switch Name", icon="mdi:toggle-switch"),
        "displayname": SensorDef(name="Switch Display Name", icon="mdi:label"),
        # Dynamic switch entries are appended at runtime.
    },
    "weather": {
        "cloudcover": SensorDef(
            name="Cloud Cover",
            unit="%",
            state_class="measurement",
            icon="mdi:weather-cloudy",
        ),
        "averageperiod": SensorDef(
            name="Average Period",
            unit="s",
            state_class="measurement",
            icon="mdi:timer-outline",
        ),
        "dewpoint": SensorDef(
            name="Dew Point",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            icon="mdi:thermometer-water",
        ),
        "humidity": SensorDef(
            name="Humidity",
            unit="%",
            device_class="humidity",
            state_class="measurement",
            icon="mdi:water-percent",
        ),
        "pressure": SensorDef(
            name="Pressure",
            unit="hPa",
            device_class="pressure",
            state_class="measurement",
            icon="mdi:gauge",
        ),
        "rain_rate": SensorDef(name="Rain Rate", icon="mdi:weather-pouring"),
        "sky_brightness": SensorDef(name="Sky Brightness", icon="mdi:weather-night"),
        "sky_quality": SensorDef(
            name="Sky Quality", icon="mdi:weather-night-partly-cloudy"
        ),
        "sky_temperature": SensorDef(
            name="Sky Temperature",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            icon="mdi:thermometer-chevron-down",
        ),
        "star_fwhm": SensorDef(
            name="Star FWHM",
            unit="arcsec",
            state_class="measurement",
            icon="mdi:chart-bell-curve",
        ),
        "temperature": SensorDef(
            name="Temperature",
            unit="°C",
            device_class="temperature",
            state_class="measurement",
            icon="mdi:thermometer",
        ),
        "wind_direction": SensorDef(
            name="Wind Direction",
            unit="°",
            state_class="measurement",
            icon="mdi:compass",
        ),
        "wind_gust": SensorDef(name="Wind Gust", icon="mdi:weather-windy"),
        "wind_speed": SensorDef(
            name="Wind Speed",
            unit="m/s",
            state_class="measurement",
            icon="mdi:weather-windy",
        ),
        "connected": SensorDef(
            name="Weather Connected",
            icon="mdi:lan-connect",
            device_class="connectivity",
            platform="binary_sensor",
        ),
        "name": SensorDef(name="Weather Name", icon="mdi:label"),
        "displayname": SensorDef(name="Weather Display Name", icon="mdi:label-outline"),
    },
}


def _build_lookup(status: Dict[str, Any]) -> Dict[str, Any]:
    lookup: Dict[str, Any] = {}
    for key, value in status.items():
        if key == "Response" and isinstance(value, dict):
            for inner_key, inner_val in value.items():
                lookup[_normalize(inner_key)] = inner_val
        elif isinstance(value, dict):
            for inner_key, inner_val in value.items():
                lookup[_normalize(f"{key}_{inner_key}")] = inner_val
        else:
            lookup[_normalize(key)] = value
    return lookup


def _append_switches(status: Dict[str, Any], values: Dict[str, Any]) -> None:
    resp = status.get("Response", {}) if isinstance(status, dict) else {}
    ro_list = resp.get("ReadonlySwitches", []) or []
    for idx, entry in enumerate(ro_list):
        if not isinstance(entry, dict):
            continue
        values[f"readonly_switch_{idx}_name"] = entry.get("Name")
        values[f"readonly_switch_{idx}_value"] = entry.get("Value")
        values[f"readonly_switch_{idx}_id"] = entry.get("Id")
        values[f"readonly_switch_{idx}_description"] = entry.get("Description")

    rw_list = resp.get("WriteableSwitches", []) or []
    for idx, entry in enumerate(rw_list):
        if not isinstance(entry, dict):
            continue
        values[f"writable_switch_{idx}_name"] = entry.get("Name")
        values[f"writable_switch_{idx}_id"] = entry.get("Id")
        values[f"writable_switch_{idx}_min"] = entry.get("Min")
        values[f"writable_switch_{idx}_max"] = entry.get("Max")
        values[f"writable_switch_{idx}_description"] = entry.get("Description")
        values[f"writable_switch_{idx}_stepsize"] = entry.get("StepSize")
        values[f"writable_switch_{idx}_targetvalue"] = entry.get("TargetValue")


def extract_state_values(device: str, status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten API responses into a dictionary of requested variables.
    """

    values: Dict[str, Any] = {}
    if device not in DEVICE_SENSORS:
        return values

    if device == "switch":
        _append_switches(status, values)

    lookup = _build_lookup(status or {})

    for var, definition in DEVICE_SENSORS.get(device, {}).items():
        for candidate in (definition.source or []) + [var]:
            norm = _normalize(candidate)
            if norm in lookup:
                values[var] = lookup.get(norm)
                break

    return values


def device_identifier(device_info: DeviceInfo, device: str) -> str:
    return f"{device_info.device_id}_{device}"


def device_payload(device_info: DeviceInfo, device: str) -> Dict[str, object]:
    return {
        "identifiers": [device_identifier(device_info, device)],
        "name": f"{device_info.name} {device.title()}",
        "manufacturer": device_info.manufacturer,
        "model": device_info.model,
    }
