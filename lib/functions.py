import base64
import sqlite3
import json

from PIL import Image
from io import BytesIO

from lib.history_correction import correct_value

# This file reevaluates the latest picture of a watermeter and saves the result in the database.
def reevaluate_latest_picture(db_file: str, name:str, meter_preditor, config, publish: bool = False, mqtt_client = None):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # get latest image from watermeter
        cursor.execute("SELECT picture_data, picture_timestamp, setup FROM watermeters WHERE name = ? ORDER BY picture_number DESC LIMIT 1", (name,))
        row = cursor.fetchone()
        if not row:
            conn.commit()
            return None
        image_data = base64.b64decode(row[0])
        timestamp = row[1]
        setup = row[2] == 1

        # Get current settings for the watermeter
        cursor.execute('''
                   SELECT threshold_low, threshold_high, threshold_last_low, threshold_last_high, islanding_padding,
                    segments, shrink_last_3, extended_last_digit, max_flow_rate, rotated_180
                   FROM settings
                   WHERE name = ?
               ''', (name,))
        settings = cursor.fetchone()
        thresholds = [settings[0], settings[1]]
        thresholds_last = [settings[2], settings[3]]
        islanding_padding = settings[4]
        segments = settings[5]
        shrink_last_3 = settings[6]
        extended_last_digit = settings[7]
        max_flow_rate = settings[8]
        rotated_180 = settings[9]

        # Get the target_brightness from the last history entry
        cursor.execute("SELECT target_brightness FROM history WHERE name = ? ORDER BY ROWID DESC LIMIT 1", (name,))
        row = cursor.fetchone()
        target_brightness = None
        if row:
            target_brightness = row[0]
        conn.commit()
        image = Image.open(BytesIO(image_data))

        # Use the meter predictor to extract the digits from the image
        result, digits, target_brightness = meter_preditor.extract_display_and_segment(image, segments=segments, shrink_last_3=shrink_last_3,
                                                                  extended_last_digit=extended_last_digit, rotated_180=rotated_180, target_brightness=target_brightness)

        if not result or len(result) == 0:
            print(f"Meter-Eval: No result found for {name}")
            return None

        # Apply thresholds and extract the digits
        processed = []
        prediction = []
        if len(thresholds) == 0:
            print(f"Meter-Eval: No thresholds found for {name}")
        else:
            processed, digits = meter_preditor.apply_thresholds(digits, thresholds, thresholds_last, islanding_padding)
            prediction, second_model_results = meter_preditor.predict_digits(digits)

        # If the setup is finished, try to correct the value and save the result
        value = None
        confidence = 0
        if setup:
            r = correct_value(db_file, name, [result, processed, prediction, timestamp, second_model_results], allow_negative_correction=config["allow_negative_correction"], max_flow_rate=max_flow_rate)
            if r is not None:
                value, confidence = r
                cursor.execute('''
                    INSERT INTO history
                    VALUES (?,?,?,?,?,?)
                ''', (
                    name,
                    value,
                    confidence,
                    target_brightness,
                    timestamp,
                    False
                ))

                # remove old entries (keep 30)
                cursor.execute('''
                    DELETE FROM history
                    WHERE name = ?
                    AND ROWID NOT IN (
                        SELECT ROWID
                        FROM history
                        WHERE name = ?
                        ORDER BY ROWID DESC
                        LIMIT ?
                    )
                ''', (name, name, config['max_history']))

                if publish and mqtt_client:
                    publish_value(mqtt_client, config, name, value)

        cursor.execute('''
                   INSERT INTO evaluations
                   VALUES (?,?)
               ''', (
            name,
            json.dumps([result, processed, prediction, timestamp, value, second_model_results, confidence])
        ))

        # remove old evaluations (keep 5)
        cursor.execute('''
                   DELETE FROM evaluations
                   WHERE name = ?
                   AND ROWID NOT IN (
                       SELECT ROWID
                       FROM evaluations
                       WHERE name = ?
                       ORDER BY ROWID DESC
                       LIMIT ?
                   )
               ''', (name, name, config['max_evals']))

        conn.commit()

        print(f"Meter-Eval: Prediction saved for {name}")
        return target_brightness, confidence

# Function to publish the value to the MQTT broker, compatible with Home Assistant
def publish_value(mqtt_client, config, name, value):
    # publish to topic
    topic = config["publish_to"].replace("{device}", name) + "value"
    dict = {
        "value": int(value) / 1000.0,
    }
    mqtt_client.publish(topic, json.dumps(dict), qos=1, retain=True)
    print(f"Meter-Eval: Value published for {name} ({value} m³)")

# Function to publish the registration to the MQTT broker, compatible with Home Assistant
def publish_registration(mqtt_client, config, name, type):
    # publish to topic
    topic = config["publish_to"].replace("{device}", name) + "config"
    dict = {
      "name": "Water usage",
      "state_topic": config["publish_to"].replace("{device}", name) + type,
      "unit_of_measurement": "m³",
      "device_class": "water",
      "unique_id": "watermeter_" + name,
      "value_template": "{{ value_json.value }}",
      "device": {
        "identifiers": ["watermeter_" + name],
        "name": name,
        "manufacturer": "DIY",
        "model": "WM-1",
        "sw_version": "1.0"
      }
    }
    mqtt_client.publish(topic, json.dumps(dict), qos=1, retain=True)
    print(f"Meter-Eval: Registration published for {name}")

# Function to add a history entry to the database, removing old entries
def add_history_entry(db_file: str, name: str, value: int, confidence:int, target_brightness: float, timestamp: str, config, manual: bool = False):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history
            VALUES (?,?,?,?,?,?)
        ''', (
            name,
            value,
            confidence,
            target_brightness,
            timestamp,
            manual
        ))

        # remove old entries (keep 30)
        cursor.execute('''
            DELETE FROM history
            WHERE name = ?
            AND ROWID NOT IN (
                SELECT ROWID
                FROM history
                WHERE name = ?
                ORDER BY ROWID DESC
                LIMIT ?
            )
        ''', (name, name, config['max_history']))

        conn.commit()
        print(f"Meter-Eval: History entry added for {name}")