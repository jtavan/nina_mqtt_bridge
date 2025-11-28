# nina_mqtt_bridge

A lightweight Python bridge that polls the NINA Advanced API and exposes device state, images, and control endpoints to Home Assistant over MQTT. It publishes Home Assistant–compatible discovery messages, per-device availability, and per-variable sensors with sensible units/icons. Images (livestack, most recent prepared image, and screenshots) are exposed as MQTT cameras.

## What it does
- Polls NINA Advanced API endpoints on a configurable cadence for each device class (camera, mount, focuser, filter wheel, weather, sequence, etc.).
- Publishes per-variable sensor states under `{base}/{device}/{variable}` with retained payloads and per-device availability topics `{base}/{device}/availability` (LWT aware). Sensors include `expire_after` set to ~2.2× the configured refresh interval.
- Exposes image endpoints (`livestack`, `most_recent_image`, `screenshot`) as MQTT cameras carrying JPEG binary payloads; image entities do **not** expire.
- (Not yet implemented) Listens for MQTT commands on `{base}/{device}/command` for supported write actions (sequence start/stop/reset, mount home/park/unpark/tracking mode, screenshots).
- Publishes Home Assistant discovery messages under the configured discovery prefix.

## Requirements
- Python 3.11+
- MQTT broker reachable by the bridge
- NINA with the Advanced API plugin enabled and reachable via HTTP

Python dependencies are listed in `requirements.txt` (paho-mqtt, requests, PyYAML).

## Configuration
Provide a YAML config (see `config.example.yaml`) and point the bridge to it with `-c`:

```yaml
nina:
  api_uri: "http://127.0.0.1:1888/v2/api"

mqtt:
  host: "127.0.0.1"
  port: 1883
  topics:
    discovery_prefix: "homeassistant"
    base_topic: "nina"

devices:
  camera:
    enabled: true
    refresh_every: 30   # seconds
  mount:
    enabled: true
    refresh_every: 30
  # ...other devices...
  livestack:
    enabled: true
    refresh_every: 60
  most_recent_image:
    enabled: true
    refresh_every: 300
  screenshot:
    enabled: true
    refresh_every: 600
```

Defaults (from `config.py` and `PROJECT.md`):
- Base topics: discovery `homeassistant`, base `nina`, command `{base}/{device}/command`, availability `{base}/{device}/availability`
- MQTT: host `127.0.0.1`, port `1883`, client id `nina_mqtt_bridge`, keepalive `60`
- NINA API: `http://127.0.0.1:1888/v2/api`
- Per-device polling defaults to 60s unless specified.

### Topics & discovery
- State sensors: `{base}/{device}/{variable}` (retained). Availability per device: `{base}/{device}/availability` (`ON`/`OFF`).
- Commands: `{base}/{device}/command` (JSON payloads; supported for `sequence`, `mount`, `screenshot`).
- Images: `{base}/{device}/image` (binary JPEG payload). Cameras registered under `homeassistant/camera/<device_id>/.../config`.
- Discovery is published at startup (and when new switch channels are detected) and retained.

### Supported devices & key variables
See `PROJECT.md` for the full list of exposed variables per device. Highlights:
- Application: NINA/API version, start time
- Camera: temp, target temp, gain, binning, cooler/dew heater, exposure state, connected
- Mount: RA/Dec, alt/az, tracking mode/enabled, meridian flip timing, park/home, pier side, site info
- Weather: temp, humidity, dew point, wind, pressure, cloud cover, sky metrics
- Sequence: status, name
- Switch: readonly/writable switch entries expanded to individual sensors
- Images: `livestack`, `most_recent_image`, `screenshot`

## Running

### Local
```bash
pip install -r requirements.txt
python -m nina_mqtt_bridge -c /path/to/config.yaml
```

### Docker
```bash
docker build -t nina_mqtt_bridge .
docker run --rm -v $PWD/config.yaml:/config/config.yaml:ro nina_mqtt_bridge
```

`docker-compose.yml` is included for convenience; mount your config at `/config/config.yaml`.

## Command support
- Sequence: `action` one of `start` (optional `skipValidation`), `stop`, `reset`/`restart`
- Mount: `action` one of `home`, `park`, `unpark`, `tracking` with `mode` (0–4 or sidereal/lunar/solar/king/stopped)
- Screenshot: `action: screenshot` (optional `resize`, `quality`, `size`, `scale`)

Publish a JSON payload to `{base}/{device}/command`; command results are emitted on `{base}/{device}/command_response`.

## Notes & limitations
- The Advanced API supports a single connected device per class; multiple instances require multiple containers/configs.
- Image payloads are binary JPEG; ensure your broker/topic ACLs permit binary messages.
- No tests are shipped; run in a test environment before production use.
