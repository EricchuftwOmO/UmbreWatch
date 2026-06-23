# UmbreWatch: Smart Umbrella Rack with Anti-Theft Detection

An Edge-Fog-Cloud IoT system that prevents forgotten and stolen umbrellas using facial recognition, MQTT messaging, and cloud analytics.

## System Architecture

| Layer | Hardware / Software | Role |
|-------|-------------------|------|
| **Edge** | Raspberry Pi + GrovePi HAT | Ultrasonic sensors detect slot occupancy; PIR sensors detect customer exit; buzzer/LED alert |
| **Fog** | PC (this Python script) | MQTT broker; DeepFace facial recognition for zero-registration anti-theft |
| **Cloud** | InfluxDB + Grafana + Azure OpenAI | Data storage, dashboards, LLM image analysis |

## Hardware Wiring

**Slot 1**
- Ultrasonic sensor → Digital port 8
- Green LED → Digital port 6
- Red LED → Digital port 4

**Slot 2**
- Ultrasonic sensor → Digital port 7
- Green LED → Digital port 5
- Red LED → Digital port 3

**Shared**
- Buzzer → Digital port 2

## Setup Guide

### 1. Import Node-RED Flow
Import `node-red-flow.json` into Node-RED:
1. Open Node-RED in your browser (`http://<RaspberryPi_IP>:1880`)
2. Click the top-right menu → **Import**
3. Select `node-red-flow.json` from this repo and click **Import**

### 2. Configure IP Addresses
Update the following to match your own network:

- In `smartUmbrellaRackEn.py`: set `INFLUX_HOST` to your Raspberry Pi's IP.
- In Node-RED MQTT broker node: set the server to your PC's IP.
- In Node-RED InfluxDB node: set the host to your Raspberry Pi's IP.
- In Grafana → Connections → Data Sources → DB → URL: set to `http://<RaspberryPi_IP>:8086`.

### 3. Configure API Keys
The API keys in `node-red-flow.json` have been replaced with placeholders. Fill in your own keys:
- **Node-RED "Send Picture To LLM" node**: replace `YOUR_AZURE_OPENAI_API_KEY` with your Azure OpenAI API key.
- **Node-RED "set zip code" node**: replace `YOUR_OPENWEATHER_API_KEY` with your OpenWeather API key.

### 4. Create Azure OpenAI Service
Deploy an Azure OpenAI resource to enable LLM-based image reasoning.

### 5. Start MQTT Broker (on PC)
```powershell
cd "C:\Program Files\Mosquitto"
.\mosquitto_sub.exe -h localhost -t "umbrella/slot1/photo" -v
```

### 6. Run the Fog-Layer Python Script
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the anti-theft brain
python .\smartUmbrellaRackEn.py
```

The system will restore slot memory from InfluxDB on startup, then listen for MQTT image messages. When an umbrella is inserted, the owner's photo is saved. When removed, DeepFace verifies the identity — if it doesn't match, `umbrella/alarm` is published to trigger all alarms.

## Grafana Dashboards

| Dashboard | Content |
|-----------|---------|
| Dashboard 1 | Slot Status & Data Analysis |
| Dashboard 2 | LLM image explanation (Azure OpenAI) |
| Dashboard 3 | Cloud service usage metrics |

## Face Reference Images

Place your own face photos in the `my_faces/` folder (`.jpg` / `.png`). These are used by DeepFace to build the identity database for comparison. Photos are excluded from this repo — **do not commit personal images**.

## Dependencies

Install inside a Python virtual environment:

```
paho-mqtt
deepface
influxdb
```

DeepFace also requires `tensorflow`, `opencv-python`, and `dlib`.

## Project Documents

- [`docs/ProjectPaper.pdf`](docs/ProjectPaper.pdf) — IEEE-style research paper
- [`docs/Poster.pptx`](docs/Poster.pptx) — Project poster
- [`docs/README.pdf`](docs/README.pdf) — Original setup guide with screenshots
