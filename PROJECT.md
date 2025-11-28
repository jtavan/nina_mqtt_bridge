# Project Overview

nina_mqtt_bridge is a simple python bridge to pull data from the NINA advanced API documented at https://bump.sh/christian-photo/doc/advanced-api/ and send it to HomeAssistant via MQTT messages. It supports HomeAssistant formatted MQTT device discovery and publishes availability LWT events as well as data events. It will continue running until stopped. When stopped, it will publish LWT messages to the MQTT broker setting the availability of all created devices to OFF. It uses the paho-mqtt library for MQTT support. The NINA API allows for only a single connected device of each category, so it is not necessary to implement support for multiple concurrent devices of a given type. 

# MQTT Configuration

MQTT is used as the connection between this tool and HomeAssistant. All MQTT broker configuration options may be specified in the configuration yaml file, with reasonable defaults (no broker security, no credentials) used if not otherwise specified. All devices are passed to the same broker instance on individual topics per device.

# NINA Devices Supported

This bridge pulls status information for all of the device types supported in the Advanced API. It can read all status information, but has a limited number of writable controls. Write capability includes:
* Starting, stopping, and restarting the loaded sequence
* Setting tracking state of the mount (tracking, stopped, adjusting tracking rate)
* Instructing the mount to find home or park/unpark
* Instructing the API to capture and send a NINA screenshot

The nina_mqtt_bridge tool understands images, and is able to use the Livestack and Get Prepared Image endpoints of the Advanced API to pull the most recent subframe and Livestack, if available. 

# Configuration

nina_mqtt_bridge is configured using a yaml-formatted configuration file specified on the command line. The configuration file will allow the user to specify the IP address and port of the (single) NINA instance to connect to, as well as the IP and port and credentials to use to connect to the (single) MQTT broker. The configuration file also allows customization of MQTT discovery prefix, base topics, and availability topics, with reasonable defaults to be used if not otherwise specified.

Defaults:
# NINA connection
NINA_API_URI = "http://127.0.0.1:1888/v2/api"

# MQTT connection
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None
MQTT_CLIENT_ID = "nina_mqtt_bridge"
MQTT_KEEPALIVE = 60

# MQTT topics
DISCOVERY_PREFIX = "homeassistant"
BASE_TOPIC = "nina"
AVAILABILITY_TOPIC = "{BASE_TOPIC}/{DEVICE}/availability"
COMMAND_TOPIC = "{BASE_TOPIC}/{DEVICE}/command"
COMMAND_ERROR_TOPIC = "${BASE_TOPIC}/{DEVICE}/command/error"
COMMAND_RESPONSE_TIMEOUT = 10

# Device info for Home Assistant
DEVICE_ID = "nina_server"
DEVICE_NAME = "NINA Advanced API"
DEVICE_MANUFACTURER = "christian-photo"
DEVICE_MODEL = "NINA Advanced API")

For each class of device (camera, mount, dome, filterwheel, etc), the configuration file will allow the user to control whether or not to pull that device's information from NINA, and how frequently to do so. For the image endpoints for Livestack and Get Prepared Image, right now this tool will simply use the autoPrepare=true flag to retrieve and present the image exactly as seen in NINA. Livestack will be identified as "livestack" while Get Prepared Image will be identified as "most_recent_image". A future revision will allow image processing customization. Images will be transmitted over MQTT in binary payload JPEG format with a user-configurable maximum size that defaults to 3 megabytes. They will be exposed as Camera types in Home Assistant with a separate unique ID for Livestack and for . Should an image from either livestack or most_recent_image fail to load, the MQTT publisher will publish availabilty OFF for the associated camera device until an image successfully loads from NINA.

For each device type, the configuration file will allow a `refresh_every` property which specifies in seconds how often to queue an update to the status of a device, with a default of 60 seconds if not otherwise specified. NINA servers are often low-powered devices. Rate limiting of API calls should be implemented, with a default maximum of 120 calls per minute. It's possible that there will be backpressure as scheduled tasks queue up faster than they can be dispatched given rate limiting. In this event, should be average number of queued requests waiting for processing increase over three one-minute periods, an error should be logged and queuing should pause until the backpressure decreases.

# Project Layout

This is a relatively simple python script. It has a task scheduler/dispatcher thread that accumulates data from the NINA API on a schedule defined in the configuration file, a MQTT publisher thread that publishes the data to MQTT, and a basic setup and configuration parsing module to set itself up. It will be built into a Docker container, which will be managed by a docker-compose.yml defining the configuration file path for each instance of the service that's running. If a user wants to pull data from multiple NINA instances, for example running multiple telescope rigs, they would run multiple instances of the docker container, each one configured for the appropriate NINA instance.


## State Variables per Device

# Application (multiple API endpoints)
nina_version (string)
api_version (string)
application_start (datetime)
screenshot (image)

# Camera (/equipment/camera/info endpoint)
target_temp (number)
temperature (number)
gain (number)
binx (number)
biny (number)
bitdepth (number)
offset (number)
cooler_on (boolean)
cooler_power (number)
dewheater_on (boolean)
is_exposing (boolean)
name (string)
display_name (string)
connected (boolean)

# Dome (/equipment/dome/info endpoint)
shutter_status (string)
at_park (boolean)
at_home (boolean)
driver_following (boolean)
slewing (boolean)
azimuth (number)
connected (boolean)
name (string)
displayname (string)
is_following (boolean)
is_synchronized (boolean)

# Filter Wheel (/equipment/filterwheel/info endpoint)
connected (boolean)
name (string)
displayname (string)
description (string)
is_moving (boolean)
selected_filter_name (string)
selected_filter_id (number)

# Flat Panel (/equipment/flatdevice/info endpoint)
cover_state (string)
light_on (boolean)
brightness (number)
connected (boolean)
name (string)
displayname (string)

# Focuser (/equipment/focuser/info endpoint)
position (number)
temperature (number)
is_moving (boolean)
is_settling (boolean)
temp_comp (boolean)
connected (boolean)
name (string)
displayname (string)

# Guider (/equipment/guider/info endpoint)
connected (boolean)
name (string)
displayname (string)
rmserror_ra_pixels (number)
rmserror_ra_arcsec (number)
rmserror_dec_pixels (number)
rmserror_dec_arcsec (number)
rmserror_total_pixels (number)
rmserror_total_arcsec (number)
rmserror_peak_ra_pixels (number)
rmserror_peak_ra_arcsec (number)
rmserror_peak_dec_pixels (number)
rmserror_peak_dec_arcsec (number)
state (string)

# Mount (/equipment/mount/info endpoint)
## from the "Response" object of the endpoint response
tracking_mode (string)
sidereal_time (number)
right_ascension (number)
declination (number)
site_latitude (number)
site_longitude (number)
site_elevation (number)
right_ascension_string (string)
declination_string (string)

## from the remaining portion of the endpoint response
time_to_flip (number)
side_of_pier (string)
altitude (number)
azimuth (number)
sidereal_time_string (string)
hours_to_meridian (string)
at_park (boolean)
at_home (boolean)
tracking_enabled (boolean)
slewing (boolean)
time_to_flip_string (string)
is_pulse_guiding (boolean)
connected (boolean)
utc_date (datetime)
name (string)
displayname (string)

# Rotator (/equipment/rotator/info endpoint)
mechanical_position (number)
position (number)
is_moving (boolean)
connected (boolean)
name (string)
displayname (string)

# Safety Monitor (/equipment/safetymonitor/info endpoint)
is_safe (boolean)
connected (boolean)
name (string)
displayname (string)

# Sequence (/sequence/json endpoint)
## From the Response object of the endpoint
status (string)
name (string)

# Switch (/equipment/switch/info endpoint)
## This will require unrolling the WriteableSwitches and ReadonlySwitches response arrays and creating objects for each entry
readonly_switch_{n}_name (string)
readonly_switch_{n}_value (number)
readonly_switch_{n}_id (number)
readonly_switch_{n}_description (string)
writable_switch_{n}_name (string)
writable_switch_{n}_id (number)
writable_switch_{n}_min (number)
writable_switch_{n}_max (number)
writable_switch_{n}_description (string)
writable_switch_{n}_stepsize (number)
writable_switch_{n}_targetvalue (number)

# From the remaining fields of the endpoint
connected (boolean)
name (string)
displayname (string)

# Weather (/equipment/weather/info endpoint)
cloudcover (number)
averageperiod (number)
dewpoint (number)
humidity (number)
pressure (number)
rain_rate (string)
sky_brightness (string)
sky_quality (string)
sky_temperature (string)
star_fwhm (string)
temperature (number)
wind_direction (number)
wind_gust (string)
wind_speed (number)
connected (boolean)
name (string)
displayname (string)
