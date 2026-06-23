import paho.mqtt.client as mqtt
import os
from deepface import DeepFace
from influxdb import InfluxDBClient

# === MQTT Settings ===
MQTT_BROKER = "localhost" # MQTT Broker's address (use "localhost" if running on the same machine)
MQTT_TOPIC = "umbrella/#"

# === InfluxDB 1.x Settings ===
INFLUX_HOST = "10.18.66.54" # This is your Raspberry Pi's IP address.
INFLUX_PORT = 8086
INFLUX_DB = "umbrellarack"

client_db = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)

# Memory: track slot occupancy status only, no user names
current_slot_status = {
    "slot1": 0,
    "slot2": 0
}

# Restore slot state from InfluxDB on startup so we know which slots are occupied
# even after a system restart.
def restore_memory_from_db():
    print("\n[System] Restoring previous memory from database...")
    for slot in ["slot1", "slot2"]:
        query = f"SELECT * FROM slot_status WHERE slot_id='{slot}' ORDER BY time DESC LIMIT 1"
        try:
            result = client_db.query(query)
            points = list(result.get_points())
            if len(points) > 0 and points[0].get('is_occupied') == 1:
                current_slot_status[slot] = 1
                print(f"🔄 Restore successful: {slot} is currently occupied.")
            else:
                print(f"🔄 Restore successful: {slot} is currently empty.")
        except Exception as e:
            print(f"⚠️ Failed to read from database: {e}")
    print("-" * 40)

# Called whenever a new MQTT message is received on the subscribed topic.
def on_message(client, userdata, msg):
    print(f"💡 Received MQTT message, Topic: {msg.topic}, Payload size: {len(msg.payload)} bytes")

    topic = msg.topic
    if topic == "umbrella/alarm":
        return

    parts = topic.split('/')
    if len(parts) < 3:
        return

    slot_id = parts[1]  # "slot1" or "slot2"
    action = parts[2]   # "insert" or "remove"

    print(f"\n[System] Received {action} action image for {slot_id}...")

    owner_img_path = f"{slot_id}_owner.jpg"  # owner photo saved on umbrella insertion
    temp_img_path = "temp_remove.jpg"        # visitor photo captured on umbrella removal

    if action == "insert":
        # Save the owner's photo as the anti-theft reference
        with open(owner_img_path, "wb") as f:
            f.write(msg.payload)

        current_slot_status[slot_id] = 1
        print(f"🌂 Recorded owner features for {slot_id}, anti-theft protection activated.")

        # Write to InfluxDB (no name registered — label as Visitor)
        json_body = [{
            "measurement": "slot_status",
            "tags": {"slot_id": slot_id, "user": f"{slot_id}_Visitor"},
            "fields": {"is_occupied": 1}
        }]
        client_db.write_points(json_body)
        print("📝 Synchronized to InfluxDB (inserted)")

    elif action == "remove":
        # Save the visitor photo to disk before comparison
        with open(temp_img_path, "wb") as f:
            f.write(msg.payload)

        # Guard: ensure owner photo exists before attempting comparison
        if not os.path.exists(owner_img_path):
            print(f"❌ Cannot find owner photo for {slot_id}, comparison failed!")
            return

        print("🔍 Performing facial feature comparison (1-to-1 Verification)...")
        try:
            result = DeepFace.verify(
                img1_path=owner_img_path,
                img2_path=temp_img_path,
                enforce_detection=True,       # require a detectable face in both images
                detector_backend="retinaface", # high-accuracy detector; alternatives: "yolov8", "mtcnn"
                model_name="Facenet"
            )

            is_same_person = result["verified"]

            if is_same_person:
                print(f"🔓 Identity verification successful! Same person, umbrella from {slot_id} successfully retrieved.")
                current_slot_status[slot_id] = 0

                json_body = [{
                    "measurement": "slot_status",
                    "tags": {"slot_id": slot_id, "user": f"{slot_id}_Visitor"},
                    "fields": {"is_occupied": 0}
                }]
                client_db.write_points(json_body)
                print("📝 Synchronized to InfluxDB (removed)")

                if os.path.exists(owner_img_path):
                    os.remove(owner_img_path)

            else:
                print(f"🚨 Alert! Identity mismatch! The person retrieving the umbrella is NOT the owner!")
                client.publish("umbrella/alarm", "ON")

        except ValueError:
            print("🚨 Alert! No clear face detected in the image! (Face may be covered or not facing the camera)")
            client.publish("umbrella/alarm", "ON")

        except Exception as e:
            print(f"⚠️ System or network error occurred: {e}")

# Called when the MQTT client connects to the broker.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Successfully connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Connection failed, error code: {rc}")

# === main ===
restore_memory_from_db()

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.subscribe(MQTT_TOPIC)

print("🚀 Fog Node zero-registration anti-theft brain started, waiting for images...")
mqtt_client.loop_forever()
