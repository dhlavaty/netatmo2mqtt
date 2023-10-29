# Yet Another netatmo2mqtt

Reads room temperatures from Netatmo API and publish them to a MQTT broker.

# Requirements

Requires OAUTH `client_id`, `client_secret` and `refresh_token`. You can get yours from https://dev.netatmo.com/apps/

**AWARE:** You need to set `read_thermostat` topic when generating your tokens.

# How it works

The script performs the following steps:

1. Gets OAUTH's access-token from https://api.netatmo.com/oauth2/token
1. Loads room names from [Netatmo API /api/homesdata](https://dev.netatmo.com/apidocumentation/energy#homesdata)
   - current limitation: if you have multiple homes, only the first one is loaded
1. Loads actual room temperatures from [Netatmo API /api/homestatus](https://dev.netatmo.com/apidocumentation/energy#homestatus)
1. Publishes MQTT message for each room, containing room name and temperature with topic `netatmo2mqtt/<ROOM-NAME>`

MQTT message example:

```json
{
  "topic": "netatmo2mqtt/my-room",
  "payload": {
    "roomId": "1234567890",
    "slug": "my-room",
    "roomName": "My Room",
    "temperature": 23
  },
  "qos": 0,
  "retain": false
}
```

# Usage

## Local development

We use [Poetry](https://python-poetry.org/) for local development. On macOS you can install Poetry with `brew install poetry`.

```sh
poetry install
poetry run python netatmo2mqtt.py --help
```

You can set required variables from command line:

```sh
poetry run python netatmo2mqtt.py --oauth-client-id 600000000000000000000004 --oauth-client-secret F000000000000000000000000000000000000B --oauth-refresh-token 500000000000000000000000000000000000000000000000000000000
```

Or you can set required variables from environment variables:

```sh
OAUTH_CLIENT_ID="600000000000000000000004" OAUTH_CLIENT_SECRET="F000000000000000000000000000000000000B" OAUTH_REFRESH_TOKEN="500000000000000000000000000000000000000000000000000000000" poetry run python netatmo2mqtt.py
```

## Docker usage

Docker image is published on https://hub.docker.com/r/dhlavaty/netatmo2mqtt

For docker image, you need to send required parameters via env variables:

```sh
docker run --env OAUTH_CLIENT_ID="600000000000000000000004" --env OAUTH_CLIENT_SECRET="F000000000000000000000000000000000000B" --env OAUTH_REFRESH_TOKEN="500000000000000000000000000000000000000000000000000000000" --env MQTT_HOSTNAME="localhost" -it --rm dhlavaty/netatmo2mqtt
```

Or using `docker-compose.yml`:

```yml
version: "3.8"

services:
  netatmo2mqtt:
    container_name: netatmo2mqtt
    restart: unless-stopped
    image: dhlavaty/netatmo2mqtt
    environment:
      OAUTH_CLIENT_ID: 600000000000000000000004
      OAUTH_CLIENT_SECRET: F000000000000000000000000000000000000B
      OAUTH_REFRESH_TOKEN: 500000000000000000000000000000000000000000000000000000000
      MQTT_HOSTNAME: "localhost"
```

Docker version runs every 10 minutes.

# CLI help

```sh
# poetry run python netatmo2mqtt.py --help
usage: netatmo2mqtt.py [--help]
                       --oauth-client-id OAUTHCLIENTID
                       --oauth-client-secret OAUTHCLIENTSECRET
                       --oauth-refresh-token OAUTHREFRESHTOKEN
                       [--mqtt-hostname MQTTHOSTNAME]
                       [--mqtt-port MQTTPORT]
                       [--mqtt-topic-prefix MQTTTOPICPREFIX]

Read room temperatures from Netatmo API and publish them to a MQTT broker.

options:
  -h, --help            show this help message and exit
  --oauth-client-id OAUTHCLIENTID
                        Netatmo OAUTH Client ID | or use OAUTH_CLIENT_ID env var (get it from
                        https://dev.netatmo.com/apps/)
  --oauth-client-secret OAUTHCLIENTSECRET
                        Netatmo OAUTH Client Secret | or use OAUTH_CLIENT_SECRET env var (get it from
                        https://dev.netatmo.com/apps/)
  --oauth-refresh-token OAUTHREFRESHTOKEN
                        Netatmo OAUTH Refresh Token | or use OAUTH_REFRESH_TOKEN env var (get it from
                        https://dev.netatmo.com/apps/)
  --mqtt-hostname MQTTHOSTNAME
                        MQTT server hostname (Default: 'localhost') | or use MQTT_HOSTNAME env var
  --mqtt-port MQTTPORT  MQTT server port (Default: 1883) | or use MQTT_PORT env var
  --mqtt-topic-prefix MQTTTOPICPREFIX
                        MQTT topic prefix (Default: 'netatmo2mqtt/') | or use MQTT_TOPIC_PREFIX env var
```

# Other

## Docker build

Build multi-arch image:

```sh
docker buildx create --name mybuilder
docker buildx use mybuilder

# (Optional) check your builder
docker buildx inspect

docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 --tag dhlavaty/netatmo2mqtt . --push

# (Optional) Inspect your image
docker buildx imagetools inspect dhlavaty/netatmo2mqtt
```

Lint dockerfile:

```sh
docker run --rm -i hadolint/hadolint < Dockerfile
```

## License

This project is licensed under MIT - http://opensource.org/licenses/MIT
