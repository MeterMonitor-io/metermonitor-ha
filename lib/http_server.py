import os
from io import BytesIO


import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException, Body, Header, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import base64
import sqlite3
import zlib
import re
from typing import List

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse

from lib.functions import reevaluate_latest_picture, add_history_entry
from lib.meter_processing.meter_processing import MeterPredictor
from lib.global_alerts import get_alerts, add_alert


# http server class
# FastAPOI automatically creates a documentation for the API on the path /docs

def prepare_setup_app(config, lifespan):
    app = FastAPI(lifespan=lifespan)
    SECRET_KEY = config['secret_key']
    db_connection = lambda: sqlite3.connect(config['dbfile'])

    # Warn user if secret key is not changed
    if config['secret_key'] == "change_me" and config['enable_auth']:
        add_alert("authentication", "Please change the secret key in the configuration file!")

    # create instance of meter predictor
    meter_preditor = MeterPredictor()

    print("[HTTP] Successfully initialized the meter predictor.")

    # CORS Konfiguration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # When using home assistant ingress, restrict access to the ingress IP
    @app.middleware("http")
    async def restrict_ip_middleware(request, call_next):
        client_ip = request.client.host  # Get the requester's IP address
        if config["ingress"] and client_ip != "172.30.32.2": # Home Assistant IP for Ingress
            return JSONResponse(status_code=403, content={"message": "Forbidden"})

        return await call_next(request)

    # Authentication
    def authenticate(secret: str = Header(None)):
        if not config['enable_auth']:
            return
        if secret != SECRET_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Models
    class PictureData(BaseModel):
        format: str
        timestamp: str
        width: int
        height: int
        length: int
        data: str

    class ConfigRequest(BaseModel):
        name: str
        picture_number: int
        WiFi_RSSI: int
        picture: PictureData

    class SettingsRequest(BaseModel):
        name: str
        threshold_low: int
        threshold_high: int
        threshold_last_low: int
        threshold_last_high: int
        islanding_padding: int
        segments: int
        rotated_180: bool
        shrink_last_3: bool
        extended_last_digit: bool
        max_flow_rate: float

    class EvalRequest(BaseModel):
        eval: str

    class SetupData(BaseModel):
        value: int
        timestamp: str

    class DatasetUpload(BaseModel):
        name: str
        labels: List[str]
        colored: List[str]
        thresholded: List[str]

    # Helper to sanitize meter name for filenames
    def _sanitize_name(name: str) -> str:
        # allow alnum, dash and underscore; replace others with _
        return re.sub(r"[^A-Za-z0-9_-]", "_", name)

    @app.get("/api/discovery", dependencies=[Depends(authenticate)])
    def get_discovery():
        cursor = db_connection().cursor()
        cursor.execute("SELECT name, picture_timestamp, wifi_rssi FROM watermeters WHERE setup = 0")
        return {"watermeters": [row for row in cursor.fetchall()]}

    @app.post("/api/dataset/upload", dependencies=[Depends(authenticate)])
    def upload_dataset(payload: DatasetUpload):
        # Validate equal lengths
        n = len(payload.labels)
        if not (len(payload.colored) == n == len(payload.thresholded)):
            raise HTTPException(status_code=400, detail="'labels', 'colored' and 'thresholded' arrays must have equal length")

        # allowed labels are 0-9 and 'r'
        allowed = set([str(i) for i in range(10)] + ["r"])

        out_root = config.get('output_dataset', '/data/output_dataset')
        os.makedirs(out_root, exist_ok=True)

        saved = 0
        meter_name = _sanitize_name(payload.name)

        for idx in range(n):
            raw_label = payload.labels[idx]
            label = str(raw_label)
            if label not in allowed:
                raise HTTPException(status_code=400, detail=f"Invalid label at index {idx}: {label}")

            # ensure color and th label folders exist
            color_label_dir = os.path.join(out_root, 'color', label)
            th_label_dir = os.path.join(out_root, 'th', label)
            os.makedirs(color_label_dir, exist_ok=True)
            os.makedirs(th_label_dir, exist_ok=True)

            # decode images
            try:
                col_bytes = base64.b64decode(payload.colored[idx])
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid base64 in 'colored' at index {idx}")
            try:
                th_bytes = base64.b64decode(payload.thresholded[idx])
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid base64 in 'thresholded' at index {idx}")

            # compute crc32 of combined bytes for uniqueness
            crc_input = col_bytes + th_bytes
            crc = zlib.crc32(crc_input) & 0xFFFFFFFF
            crc_hex = f"{crc:08x}"

            filename = f"{label}_{meter_name}_{crc_hex}.png"
            filepath_col = os.path.join(color_label_dir, filename)
            filepath_th = os.path.join(th_label_dir, filename)

            # write files
            try:
                with open(filepath_col, 'wb') as f:
                    f.write(col_bytes)
                with open(filepath_th, 'wb') as f:
                    f.write(th_bytes)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to write files for index {idx}: {e}")

            saved += 1

        return {"saved": saved, "output_root": out_root}

    @app.post("/api/evaluate/single", dependencies=[Depends(authenticate)])
    def evaluate(
            base64str: str = Body(...),  # Changed from Query to Body for POST requests
            threshold_low: float = Body(0, ge=0, le=255),
            threshold_high: float = Body(155, ge=0, le=255),
            islanding_padding: int = Body(20, ge=0),
    ):
            # Decode the base64 image
            image_data = base64.b64decode(base64str)

            # Get PIL image from base64
            image = Image.open(BytesIO(image_data))
            # to numpy array
            image = np.array(image)

            # Apply threshold with the passed values
            base64r, digits = meter_preditor.apply_threshold(image, threshold_low, threshold_high, islanding_padding)

            # Return the result
            return {"base64": base64r}

    @app.get("/api/alerts", dependencies=[Depends(authenticate)])
    def get_current_alerts():
        return get_alerts()

    @app.get("/api/config", dependencies=[Depends(authenticate)])
    def get_config():
        tconfig = config.copy()
        del tconfig['secret_key']
        return tconfig

    @app.get("/api/watermeters", dependencies=[Depends(authenticate)])
    def get_watermeters():
        cursor = db_connection().cursor()
        cursor.execute("SELECT name, picture_timestamp, wifi_rssi FROM watermeters WHERE setup = 1")
        return {"watermeters": [row for row in cursor.fetchall()]}

    @app.post("/api/setup/{name}/finish", dependencies=[Depends(authenticate)])
    def post_setup_finished(name: str, data: SetupData):
        db = db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE watermeters SET setup = 1 WHERE name = ?", (name,))
        db.commit()
        target_brightness, confidence = reevaluate_latest_picture(config['dbfile'], name, meter_preditor, config)
        add_history_entry(config['dbfile'], name, data.value, 1, target_brightness, data.timestamp, config, manual=True)

        # clear evaluations
        cursor = db.cursor()
        cursor.execute("DELETE FROM evaluations WHERE name = ?", (name,))
        db.commit()

        return {"message": "Setup completed"}

    @app.post("/api/setup/{name}/enable", dependencies=[Depends(authenticate)])
    def post_setup_enable(name: str):
        db = db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE watermeters SET setup = 0 WHERE name = ?", (name,))
        db.commit()
        return {"message": "Setup completed"}

    @app.get("/api/watermeters/{name}/history", dependencies=[Depends(authenticate)])
    def get_watermeter(name: str):
        cursor = db_connection().cursor()
        cursor.execute("SELECT value, timestamp, confidence, manual FROM history WHERE name = ?", (name,))
        return {"history": [row for row in cursor.fetchall()]}

    @app.get("/api/watermeters/{name}", dependencies=[Depends(authenticate)])
    def get_watermeter(name: str):
        cursor = db_connection().cursor()
        cursor.execute("SELECT * FROM watermeters WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Watermeter not found")
        return {
            "name": row[0],
            "picture_number": row[1],
            "WiFi-RSSI": row[2],
            "picture": {
                "format": row[3],
                "timestamp": row[4],
                "width": row[5],
                "height": row[6],
                "length": row[7],
                "data": row[8]
            }
        }

    @app.delete("/api/watermeters/{name}", dependencies=[Depends(authenticate)])
    def delete_watermeter(name: str):
        db = db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM watermeters WHERE name = ?", (name,))
        cursor.execute("DELETE FROM evaluations WHERE name = ?", (name,))
        cursor.execute("DELETE FROM history WHERE name = ?", (name,))
        cursor.execute("DELETE FROM settings WHERE name = ?", (name,))
        db.commit()
        return {"message": "Watermeter deleted", "name": name}

    @app.post("/api/setup", dependencies=[Depends(authenticate)])
    def setup_watermeter(config: ConfigRequest):
        db = db_connection()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO watermeters (name, picture_number, wifi_rssi, picture_format, 
            picture_timestamp, picture_width, picture_height, picture_length, picture_data, setup) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                config.name,
                config.picture_number,
                config.WiFi_RSSI,
                config.picture.format,
                config.picture.timestamp,
                config.picture.width,
                config.picture.height,
                config.picture.length,
                config.picture.data
            )
        )
        db.commit()
        return {"message": "Watermeter configured", "name": config.name}

    @app.get("/api/settings/{name}", dependencies=[Depends(authenticate)])
    def get_settings(name: str):
        cursor = db_connection().cursor()
        cursor.execute("SELECT threshold_low, threshold_high, threshold_last_low, threshold_last_high, islanding_padding, segments, shrink_last_3, extended_last_digit, max_flow_rate, rotated_180 FROM settings WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Thresholds not found")
        return {
            "threshold_low": row[0],
            "threshold_high": row[1],
            "threshold_last_low": row[2],
            "threshold_last_high": row[3],
            "islanding_padding": row[4],
            "segments": row[5],
            "shrink_last_3": row[6],
            "extended_last_digit": row[7],
            "max_flow_rate": row[8],
            "rotated_180": row[9]
        }

    @app.post("/api/settings", dependencies=[Depends(authenticate)])
    def set_settings(settings: SettingsRequest):
        db = db_connection()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO settings (name, threshold_low, threshold_high, threshold_last_low, threshold_last_high, islanding_padding, segments, shrink_last_3, extended_last_digit, max_flow_rate, rotated_180) 
            VALUES (?, ?, ?, ?,?,?, ?, ? , ?, ?, ?) ON CONFLICT(name) DO UPDATE SET 
            threshold_low=excluded.threshold_low, threshold_high=excluded.threshold_high, threshold_last_low=excluded.threshold_last_low, threshold_last_high=excluded.threshold_last_high,
            islanding_padding=excluded.islanding_padding,
            segments=excluded.segments, shrink_last_3=excluded.shrink_last_3, extended_last_digit=excluded.extended_last_digit, max_flow_rate=excluded.max_flow_rate, rotated_180=excluded.rotated_180
            """,
            (settings.name, settings.threshold_low, settings.threshold_high, settings.threshold_last_low, settings.threshold_last_high, settings.islanding_padding,
             settings.segments, settings.shrink_last_3, settings.extended_last_digit, settings.max_flow_rate, settings.rotated_180)
        )
        db.commit()
        return {"message": "Thresholds set", "name": settings.name}

    @app.get("/api/reevaluate_latest/{name}", dependencies=[Depends(authenticate)])
    def reevaluate_latest(name: str):
        return (reevaluate_latest_picture(config['dbfile'], name, meter_preditor, config) != None)

    # GET endpoint for retrieving evaluations
    @app.get("/api/watermeters/{name}/evals", dependencies=[Depends(authenticate)])
    def get_evals(name: str):
        cursor = db_connection().cursor()
        # Check if watermeter exists
        cursor.execute("SELECT name FROM watermeters WHERE name = ?", (name,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Watermeter not found")
        # Retrieve all evaluations for the watermeter
        cursor.execute("SELECT eval FROM evaluations WHERE name = ?", (name,))
        evals = [row[0] for row in cursor.fetchall()]
        return {"evals": evals}

    # POST endpoint for adding an evaluation
    @app.post("/api/watermeters/{name}/evals", dependencies=[Depends(authenticate)])
    def add_eval(name: str, eval_req: EvalRequest):
        db = db_connection()
        cursor = db.cursor()
        # Check if watermeter exists
        cursor.execute("SELECT name FROM watermeters WHERE name = ?", (name,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Watermeter not found")
        # Insert the new evaluation
        cursor.execute(
            "INSERT INTO evaluations (name, eval) VALUES (?, ?)",
            (name, eval_req.eval)
        )
        db.commit()
        return {"message": "Eval added", "name": name}

    @app.get("/")
    async def serve_index():
        file_path = os.path.join("frontend/dist", "index.html")
        response = FileResponse(file_path)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        return response

    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    print("[HTTP] Setup complete.")
    return app
