# mesh_meteo_thingspeak.py
import paho.mqtt.client as mqtt
import json, time, os, requests

MESH_HOST  = "mqtt.meshtastic.org"
MESH_PORT  = 1883
MESH_USER  = "meshdev"
MESH_PASS  = "large4cats"
MESH_TOPIC = "msh/EU_868/2/json/#"

TS_API_KEY = os.environ["TS_WRITE_KEY"]   # ThingSpeak Write API Key
TS_URL     = "https://api.thingspeak.com/update"
MY_NODE_ID = os.environ["NODE_ID"]        # ID decimale del tuo nodo

def send_to_thingspeak(temp=None, hum=None, press=None,
                       rain=None, uv=None, batt=None):
    params = {"api_key": TS_API_KEY}
    if temp  is not None: params["field1"] = round(temp,  1)
    if hum   is not None: params["field2"] = round(hum,   1)
    if press is not None: params["field3"] = round(press, 1)
    if rain  is not None: params["field4"] = round(rain,  2)
    if uv    is not None: params["field5"] = round(uv,    2)
    if batt  is not None: params["field6"] = round(batt,  2)
    
    r = requests.get(TS_URL, params=params)
    if r.text == "0":
        print("Errore ThingSpeak — troppo frequente o chiave sbagliata")
    else:
        print(f"Salvato su ThingSpeak (entry {r.text}): {params}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        if str(data.get("from")) != MY_NODE_ID:
            return

        payload = data.get("payload", {})
        if data.get("type") != "telemetry":
            return

        env  = payload.get("environment_metrics", {})
        pwr  = payload.get("power_metrics", {})

        send_to_thingspeak(
            temp  = env.get("temperature"),
            hum   = env.get("relative_humidity"),
            press = env.get("barometric_pressure"),
            rain  = env.get("rainfall"),
            uv    = env.get("uv_lux"),
            batt  = pwr.get("ch1_voltage")
        )
    except Exception as e:
        print(f"Errore: {e}")

client = mqtt.Client(client_id=f"meteo-ts-{int(time.time())}")
client.username_pw_set(MESH_USER, MESH_PASS)
client.on_message = on_message
client.connect(MESH_HOST, MESH_PORT, keepalive=60)
client.subscribe(MESH_TOPIC)
print("In ascolto su Meshtastic MQTT → ThingSpeak...")
client.loop_forever()
