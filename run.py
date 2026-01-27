import os
import sqlite3
import threading
from contextlib import asynccontextmanager

import uvicorn
import json
from fastapi import FastAPI

from db.migrations import run_migrations
from lib.http_server import prepare_setup_app
from lib.mqtt_handler import MQTTHandler
from lib.polling_handler import PollingHandler

config = {}

# parse settings.json or options.json
# options.json is used in the addon, while settings.json is used in standalone mode
# the addon will merge the options.json with the contents of ha_default_settings.json

# ha_default_settings.json contains settings that should not be changed by the user when running in Home Assistant

path = '/data/options.json'
if not os.path.exists(path):
    print("[INIT] Running standalone, using settings.json")
    path = 'settings.json'
    with open(path, 'r') as f:
        config = json.load(f)
else:
    print("[INIT] Running as Home Assistant addon, using options.json and merging with ha_default_settings.json")
    #load options.json
    with open(path, 'r') as f:
        config = json.load(f)

    # merge missing options in options.json with settings.json
    with open('ha_default_settings.json', 'r') as f:
        settings = json.load(f)
        for key in settings:
            if key not in config:
                config[key] = settings[key]

print("[INIT] Loaded config:")
# pretty print json
print(json.dumps(config, indent=4))

# Run migrations
run_migrations(config['dbfile'])

MQTT_CONFIG = config['mqtt']

# start application. if http is enabled, start the http server
# if not, start only the mqtt handler

# start polling service
polling_handler = PollingHandler(config, db_file=config['dbfile'])
polling_handler.start()

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
    print(f"[INIT] Started setup server on http://{config['http']['host']}:{config['http']['port']}")
    uvicorn.run(app, host=config['http']['host'], port=config['http']['port'], log_level="error")

else:
    mqtt_handler = MQTTHandler(config, db_file=config['dbfile'], forever=True)
    mqtt_handler.start(**MQTT_CONFIG)
