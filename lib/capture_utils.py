import datetime
import base64
import json
from io import BytesIO
from PIL import Image
import sqlite3
import urllib.request
import urllib.error
import time

from lib.functions import reevaluate_latest_picture
from lib.model_singleton import get_meter_predictor

def capture_from_ha_source(config, source_config):
    """Capture image from HA camera source. Returns (raw_bytes, format)."""
    cam_entity_id = source_config.get('camera_entity_id')
    flash_entity_id = source_config.get('flash_entity_id')
    flash_delay_ms = source_config.get('flash_delay_ms', 10000)

    if not cam_entity_id:
        raise ValueError("No camera_entity_id in source config")

    # HA API functions
    def _ha_request_json_with_method(url, method='GET', body=None):
        full_url = f"{config['homeassistant']['url']}{url}"
        req = urllib.request.Request(full_url, method=method)
        req.add_header('Authorization', f"Bearer {config['homeassistant']['token']}")
        req.add_header('Content-Type', 'application/json')
        if body:
            req.data = json.dumps(body).encode('utf-8')
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            raise Exception(f"HA API error {e.code}: {e.read().decode('utf-8')}")
        except Exception as e:
            raise Exception(f"HA API unexpected error: {e}")

    def _ha_get_bytes(url):
        full_url = f"{config['homeassistant']['url']}{url}"
        req = urllib.request.Request(full_url)
        req.add_header('Authorization', f"Bearer {config['homeassistant']['token']}")
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            raise Exception(f"HA API error {e.code}: {e.read().decode('utf-8')}")
        except Exception as e:
            raise Exception(f"HA API unexpected error: {e}")

    flash_enabled = False
    try:
        if flash_entity_id and flash_entity_id.strip():
            _ha_request_json_with_method(
                "/api/services/light/turn_on",
                method='POST',
                body={'entity_id': flash_entity_id},
            )
            flash_enabled = True
            time.sleep(max(0.0, flash_delay_ms / 1000.0))

        raw = _ha_get_bytes(f"/api/camera_proxy/{cam_entity_id}")
        return raw, "jpeg"
    finally:
        if flash_enabled:
            try:
                _ha_request_json_with_method(
                    "/api/services/light/turn_off",
                    method='POST',
                    body={'entity_id': flash_entity_id},
                )
            except Exception:
                pass

def process_captured_image(db_file, name, raw_image, format_, config, meter_predictor, publish=True):
    """Process the captured image: save to DB and reevaluate."""
    b64 = base64.b64encode(raw_image).decode('utf-8')
    img = Image.open(BytesIO(raw_image))
    width, height = img.size
    timestamp = datetime.datetime.now().isoformat()

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        # Update or insert into watermeters
        cursor.execute("SELECT 1 FROM watermeters WHERE name = ?", (name,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute('''
                UPDATE watermeters 
                SET 
                    picture_number = picture_number + 1,
                    wifi_rssi = NULL,
                    picture_format = ?,
                    picture_timestamp = ?,
                    picture_width = ?,
                    picture_height = ?,
                    picture_length = ?,
                    picture_data = ?,
                    picture_data_bbox = NULL
                WHERE name = ?
            ''', (
                format_,
                timestamp,
                width,
                height,
                len(raw_image),
                b64,
                name
            ))
        else:
            cursor.execute('''
                INSERT INTO watermeters (name, picture_number, wifi_rssi, picture_format, picture_timestamp, picture_width, picture_height, picture_length, picture_data, setup, picture_data_bbox)
                VALUES (?,?,?,?,?,?,?,?,?,?,NULL)
            ''', (
                name,
                1,
                None,
                format_,
                timestamp,
                width,
                height,
                len(raw_image),
                b64,
                0
            ))
            # Also insert default settings
            cursor.execute('''
                INSERT OR IGNORE INTO settings
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                name,
                0,
                100,
                0,
                100,
                20,
                7,
                False,
                False,
                False,
                1.0,
                None
            ))

        conn.commit()
        print(f"[CAPTURE] Saved image for {name}")

        # Process the image
        _, _, boundingboxed_image = reevaluate_latest_picture(db_file, name, meter_predictor,
                                                              config, publish=publish)
        if boundingboxed_image:
            cursor.execute('''
                UPDATE watermeters 
                SET picture_data_bbox = ?
                WHERE name = ?
            ''', (
                boundingboxed_image,
                name
            ))
            conn.commit()
            print(f"[CAPTURE] Saved boundingboxed image for {name}")

    return timestamp

def capture_and_process_source(config, db_file, source_row, meter_predictor):
    config_json = source_row['config_json']
    if not config_json:
        return
    cfg = json.loads(config_json)
    raw_image, format_ = capture_from_ha_source(config, cfg)
    timestamp = process_captured_image(db_file, source_row['name'], raw_image, format_, config, meter_predictor)

    # Update source last_success_ts
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE sources SET last_success_ts = ?, last_error = NULL WHERE id = ?", (timestamp, source_row['id']))
        conn.commit()
