import os, json, argparse
import requests
import paho.mqtt.publish as publish

NETATMO_OAUTH_URL = "https://api.netatmo.com/oauth2/token"
NETATMO_HOMESTATUS_URL = "https://api.netatmo.com/api/homestatus"
NETATMO_HOMESDATA_URL = "https://api.netatmo.com/api/homesdata"


def env_or_required(env):
    """
    Use to load ENV variables in 'argparse'

    See https://stackoverflow.com/a/45392259
    """
    if os.environ.get(env):
        return {"default": os.environ.get(env)}
    else:
        return {"required": True}


def env_or_default(env, default):
    """
    Use to load ENV variables in 'argparse', or use default value
    """
    if os.environ.get(env):
        return {"default": os.environ.get(env)}
    else:
        return {"default": default}


def getOAUTHAccessToken(oauthClientId, oauthClientSecret, oauthRefreshToken):
    """Gets OAUTH access-token from Netatmo auth server"""

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": oauthRefreshToken,
        "client_id": oauthClientId,
        "client_secret": oauthClientSecret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    res = requests.post(NETATMO_OAUTH_URL, data=payload, headers=headers)
    data = res.json()

    assert res.status_code == 200, NETATMO_OAUTH_URL + "did not return HTTP 200"
    assert "access_token" in data, "#36 no access_token in response"

    return data["access_token"]


def getRoomsTemperatures(accessToken, homeId):
    """Loads temperature for each room"""

    headers = {"Authorization": "Bearer " + accessToken}
    params = {"home_id": homeId}
    res = requests.get(NETATMO_HOMESTATUS_URL, params, headers=headers)
    data = res.json()

    assert res.status_code == 200, NETATMO_HOMESTATUS_URL + "did not return HTTP 200"
    assert "home" in data["body"], "#66 data in unknown format"
    assert "modules" in data["body"]["home"], "#67 data in unknown format"

    roomTempDict = {}
    for room in data["body"]["home"]["rooms"]:
        roomTempDict[room["id"]] = room["therm_measured_temperature"]

    return roomTempDict


def getRoomsNamesAndHomeId(accessToken):
    """Loads homeID and name for each room"""

    headers = {"Authorization": "Bearer " + accessToken}
    res = requests.get(NETATMO_HOMESDATA_URL, headers=headers)
    data = res.json()

    assert res.status_code == 200, NETATMO_HOMESDATA_URL + "did not return HTTP 200"
    assert "homes" in data["body"], "#70 data in unknown format"
    assert "rooms" in data["body"]["homes"][0], "#71 data in unknown format"

    homeId = data["body"]["homes"][0]["id"]

    roomNameDict = {}
    for room in data["body"]["homes"][0]["rooms"]:
        roomNameDict[room["id"]] = room["name"]

    return homeId, roomNameDict


def slugify(value):
    """Converts to lowercase and converts spaces to hyphens."""
    return value.replace(" ", "-").lower()


parser = argparse.ArgumentParser(
    description="Read room temperatures from Netatmo API and publish them to a MQTT broker.",
)
parser.add_argument(
    "--oauth-client-id",
    dest="oauthClientId",
    action="store",
    help="Netatmo OAUTH Client ID | or use OAUTH_CLIENT_ID env var (get it from https://dev.netatmo.com/apps/)",
    **env_or_required("OAUTH_CLIENT_ID")
)
parser.add_argument(
    "--oauth-client-secret",
    dest="oauthClientSecret",
    action="store",
    help="Netatmo OAUTH Client Secret | or use OAUTH_CLIENT_SECRET env var (get it from https://dev.netatmo.com/apps/)",
    **env_or_required("OAUTH_CLIENT_SECRET")
)
parser.add_argument(
    "--oauth-refresh-token",
    dest="oauthRefreshToken",
    action="store",
    help="Netatmo OAUTH Refresh Token | or use OAUTH_REFRESH_TOKEN env var (get it from https://dev.netatmo.com/apps/)",
    **env_or_required("OAUTH_REFRESH_TOKEN")
)
parser.add_argument(
    "--mqtt-hostname",
    dest="mqttHostname",
    action="store",
    help="MQTT server hostname (Default: 'localhost') | or use MQTT_HOSTNAME env var",
    **env_or_default("MQTT_HOSTNAME", "localhost")
)
parser.add_argument(
    "--mqtt-port",
    dest="mqttPort",
    action="store",
    type=int,
    help="MQTT server port (Default: 1883) | or use MQTT_PORT env var",
    **env_or_default("MQTT_PORT", 1883)
)
parser.add_argument(
    "--mqtt-topic-prefix",
    dest="mqttTopicPrefix",
    action="store",
    help="MQTT topic prefix (Default: 'netatmo2mqtt/') | or use MQTT_TOPIC_PREFIX env var",
    **env_or_default("MQTT_TOPIC_PREFIX", "netatmo2mqtt/")
)
args = parser.parse_args()


accessToken = getOAUTHAccessToken(
    args.oauthClientId, args.oauthClientSecret, args.oauthRefreshToken
)
print("New access token: ..." + accessToken[-8:])

homeId, roomNameDict = getRoomsNamesAndHomeId(accessToken)
print("HomeId:", homeId)
print("Rooms names:", roomNameDict)

roomTempDict = getRoomsTemperatures(accessToken, homeId)
print("Rooms temperatures:", roomTempDict)

# Join Room names with temperatures and create resulting List of Dictionaries
temperatures = []
for id in roomTempDict:
    data = {
        "roomId": id,
        "slug": slugify(roomNameDict[id]),
        "roomName": roomNameDict[id],
        "temperature": roomTempDict[id],
    }
    temperatures.append(data)

# Publish values to MQTT
for iter in temperatures:
    topic = args.mqttTopicPrefix + iter["slug"]
    publish.single(
        topic=topic,
        payload=json.dumps(iter),
        hostname=args.mqttHostname,
        port=args.mqttPort,
        client_id="netatmo2mqtt",
    )
    print("MQTT published: ", topic)

print("Done")
