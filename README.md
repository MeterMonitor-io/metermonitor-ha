![alt logo](./logogit.png)
# MeterMonitor - OCR + AI for Water Meters



**MeterMonitor** is an AI-powered backend for reading analog water meters via ESP32 cameras. Instead of running OCR on-device, this solution offloads image processing and digit recognition to a server, significantly reducing device power consumption. It integrates with **Home Assistant** but can also run **standalone**.

---

## Features

- AI-based display detection using YOLOv11
- CNN-powered digit recognition with error correction
- MQTT image ingestion from ESP32 devices
- FastAPI backend with Vue 3 frontend
- Seamless Home Assistant integration (incl. MQTT discovery)

---

## 🏠 Home Assistant Setup (Recommended)

1. **Add Repo**: Add `https://github.com/phiph-s/metermonitor-managementserver` as a repository in Home Assistant.
2. **Install**: Find and install the **MeterMonitor** add-on.
3. **Configure**: Set MQTT credentials.
4. **Start & Use**: Launch the add-on. Access the UI via Ingress.

MQTT sensors are auto-discovered as long as the Mosquitto addon is used and auto discovery is enabled (default). No manual YAML needed.
The docker container is beeing built for the architecture `amd64` and `aarch64` (arm), with `aarch64` being untested.
---

## 🖥️ Standalone Setup

### Manual

```bash
git clone https://github.com/phiph-s/metermonitor-managementserver.git
cd metermonitor-managementserver
pip install -r requirements.txt
cd frontend && yarn install && yarn build && cd ..
python3 run.py
```

Edit `settings.json` to configure MQTT and model paths.

### Docker

```bash
git clone https://github.com/phiph-s/metermonitor-managementserver.git
docker build -t metermonitor .
docker run -d -p 8070:8070 -v ~/metermonitor-data:/data metermonitor
```

Put `options.json` in `~/metermonitor-data` (same format as `settings.json`).

---

## Project Structure

```
├── run.py                # Main entry point
├── lib/                  # Backend modules (OCR, MQTT, API)
├── models/               # YOLO & CNN models
├── frontend/             # Vue 3 web UI
├── tools/                # Utilities (e.g. MQTT bulk sender)
├── settings.json         # Config (standalone)
├── config.json           # Add-on config (Home Assistant)
```

---

## Architecture

1. ESP32 sends meter images via MQTT
2. YOLOv11 detects display region
3. CNN classifies digits (0-9 + "rotation")
4. Correction logic ensures consistent readings
5. Results sent via MQTT & visible in web UI / Home Assistant

---

For more details, see the full documentation or PDF thesis.

---

MIT License | Developed as Master Project @ Hochschule RheinMain

