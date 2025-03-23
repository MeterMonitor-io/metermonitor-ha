import os
import sqlite3
import threading
from contextlib import asynccontextmanager

import uvicorn

# check if args --setup is given
import json
from fastapi import FastAPI

from lib.http_server import prepare_setup_app
from lib.mqtt_handler import MQTTHandler


config = {}

# parse settings.json or options.json
# options.json is used in the addon, while settings.json is used in standalone mode
# the addon will merge the options.json with the settings.json

path = '/data/options.json'
if not os.path.exists(path):
    print("Running standalone, using settings.json")
    path = 'settings.json'
    with open(path, 'r') as f:
        config = json.load(f)
else:
    #load options.json
    with open(path, 'r') as f:
        config = json.load(f)

    # merge missing options in options.json with settings.json
    with open('settings.json', 'r') as f:
        settings = json.load(f)
        for key in settings:
            if key not in config:
                config[key] = settings[key]

print("Config: ", config)

# create database and tables
db_connection = sqlite3.connect(config['dbfile'])
cursor = db_connection.cursor()
cursor.execute('''
            CREATE TABLE IF NOT EXISTS watermeters (
                name TEXT PRIMARY KEY,
                picture_number INTEGER,
                wifi_rssi INTEGER,
                picture_format TEXT,
                picture_timestamp TEXT,
                picture_width INTEGER,
                picture_height INTEGER,
                picture_length INTEGER,
                picture_data TEXT,
                setup BOOLEAN DEFAULT 0
            )
        ''')
cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                name TEXT PRIMARY KEY,
                threshold_low INTEGER,
                threshold_high INTEGER,
                threshold_last_low INTEGER,
                threshold_last_high INTEGER,
                islanding_padding INTEGER,
                segments INTEGER,
                rotated_180 BOOLEAN,
                shrink_last_3 BOOLEAN,
                extended_last_digit BOOLEAN,
                max_flow_rate FLOAT,
                FOREIGN KEY(name) REFERENCES watermeters(name)
            )
        ''')
# Add evaluations table
cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                name TEXT,
                eval TEXT,
                FOREIGN KEY(name) REFERENCES watermeters(name)
            )
        ''')
cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                name TEXT,
                value INTEGER,
                confidence FLOAT,
                target_brightness FLOAT,
                timestamp TEXT,
                manual BOOLEAN,
                FOREIGN KEY(name) REFERENCES watermeters(name)
            )
        ''')
db_connection.commit()
MQTT_CONFIG = config['mqtt']

# start application. if http is enabled, start the http server
# if not, start only the mqtt handler

if config['http']['enabled']:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        def run_mqtt():
            mqtt_handler = MQTTHandler(config, db_file=config['dbfile'], forever=True)
            mqtt_handler.start(**MQTT_CONFIG)

        thread = threading.Thread(target=run_mqtt, daemon=True)
        thread.start()
        yield

    app = prepare_setup_app(config, lifespan)
    print(f"Starting setup server on http://{config['http']['host']}:{config['http']['port']}")
    uvicorn.run(app, host=config['http']['host'], port=config['http']['port'], log_level="error")

else:
    mqtt_handler = MQTTHandler(db_file=config['dbfile'], forever=True)
    mqtt_handler.start(**MQTT_CONFIG)
