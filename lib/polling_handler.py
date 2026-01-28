import datetime
import time
import threading
import sqlite3
import json
from typing import Dict, Any

from lib.capture_utils import capture_and_process_source
from lib.model_singleton import get_meter_predictor
from lib.global_alerts import add_alert, remove_alert
import traceback

class PollingHandler:

    def __init__(self, config, db_file: str = 'watermeters.db'):
        self.db_file = db_file
        self.config = config
        self.meter_predictor = get_meter_predictor()
        self.stop_event = threading.Event()
        print("[POLLING] Using shared meter predictor singleton instance.")

    def _process_capture(self, source_row):
        try:
            capture_and_process_source(self.config, self.db_file, source_row, self.meter_predictor)
        except Exception as e:
            # On failure, update last_success_ts to now to prevent immediate retry
            import datetime
            now = datetime.datetime.now().isoformat()
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE sources SET last_success_ts = ? WHERE id = ?", (now, source_row['id']))
                conn.commit()
            # Re-raise to log the error
            raise

    def _polling_loop(self):
        while not self.stop_event.is_set():
            try:
                with sqlite3.connect(self.db_file) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, name, source_type, poll_interval_s, config_json, last_success_ts
                        FROM sources
                        WHERE enabled = 1 AND poll_interval_s > 0 AND source_type IN ('ha_camera', 'http')
                    """)
                    sources = cursor.fetchall()

                for source in sources:
                    # Check if it's time to poll
                    last_ts = source['last_success_ts']
                    interval = source['poll_interval_s']
                    now = datetime.datetime.now()
                    if last_ts:
                        last_dt = datetime.datetime.fromisoformat(last_ts)
                        if (now - last_dt).total_seconds() < interval:
                            continue
                    # Capture
                    self._process_capture(source)

            except Exception as e:
                print(f"[POLLING] Error in polling loop: {e}")
                traceback.print_exc()

            # Sleep for a short time before next check
            self.stop_event.wait(10)  # Check every 10 seconds

    def start(self):
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()
        print("[POLLING] Polling handler started")

    def stop(self):
        self.stop_event.set()
        if hasattr(self, 'thread'):
            self.thread.join()
        print("[POLLING] Polling handler stopped")
