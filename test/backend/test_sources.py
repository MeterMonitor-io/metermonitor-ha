import base64
from io import BytesIO
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from PIL import Image

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.migrations import run_migrations
from lib.capture_utils import capture_from_http_source, capture_and_process_source, capture_from_ha_source


class FakeResponse:
    def __init__(self, data, content_type):
        self._data = data
        self.headers = {"Content-Type": content_type}

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestSources(unittest.TestCase):
    def test_capture_from_http_source_rejects_invalid_url(self):
        with self.assertRaises(ValueError):
            capture_from_http_source({"url": "ftp://example.com/image.png"})

    def test_capture_from_http_source_reads_png(self):
        img = Image.new("RGB", (8, 6), (120, 10, 10))
        buf = BytesIO()
        img.save(buf, format="PNG")
        raw = buf.getvalue()

        with patch("urllib.request.urlopen", return_value=FakeResponse(raw, "image/png")):
            data, fmt, flash = capture_from_http_source({"url": "http://example.com/image.png"})

        self.assertEqual(data, raw)
        self.assertEqual(fmt, "png")
        self.assertFalse(flash)

    def test_capture_from_ha_source_success_with_flash(self):
        config = {"homeassistant": {"url": "http://ha.local", "token": "secret"}}
        source_config = {
            "camera_entity_id": "camera.test",
            "flash_entity_id": "light.flash",
            "flash_delay_ms": 0,
        }
        requests = []

        def fake_urlopen(req, timeout=None):
            requests.append(req)
            if req.full_url.endswith("/api/services/light/turn_on"):
                return FakeResponse(b"{}", "application/json")
            if req.full_url.endswith("/api/camera_proxy/camera.test"):
                return FakeResponse(b"imgbytes", "image/jpeg")
            if req.full_url.endswith("/api/services/light/turn_off"):
                return FakeResponse(b"{}", "application/json")
            raise AssertionError(f"Unexpected URL: {req.full_url}")

        with patch("lib.capture_utils.add_ha_auth_header") as add_auth:
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                raw, fmt, flash_enabled = capture_from_ha_source(config, source_config)

        self.assertEqual(raw, b"imgbytes")
        self.assertEqual(fmt, "jpeg")
        self.assertTrue(flash_enabled)
        self.assertEqual(add_auth.call_count, 3)
        self.assertEqual(len(requests), 3)
        self.assertTrue(requests[0].full_url.endswith("/api/services/light/turn_on"))
        self.assertEqual(requests[0].get_method(), "POST")
        self.assertIsNotNone(requests[0].data)
        self.assertTrue(requests[1].full_url.endswith("/api/camera_proxy/camera.test"))
        self.assertEqual(requests[1].get_method(), "GET")
        self.assertTrue(requests[2].full_url.endswith("/api/services/light/turn_off"))
        self.assertEqual(requests[2].get_method(), "POST")

    def test_capture_from_ha_source_requires_camera_entity(self):
        config = {"homeassistant": {"url": "http://ha.local", "token": "secret"}}
        with self.assertRaises(ValueError):
            capture_from_ha_source(config, {"flash_entity_id": "light.flash"})

    def test_capture_from_ha_source_turns_off_flash_on_error(self):
        config = {"homeassistant": {"url": "http://ha.local", "token": "secret"}}
        source_config = {
            "camera_entity_id": "camera.test",
            "flash_entity_id": "light.flash",
            "flash_delay_ms": 0,
        }
        requests = []

        def fake_urlopen(req, timeout=None):
            requests.append(req)
            if req.full_url.endswith("/api/services/light/turn_on"):
                return FakeResponse(b"{}", "application/json")
            if req.full_url.endswith("/api/camera_proxy/camera.test"):
                raise urllib.error.HTTPError(
                    req.full_url, 500, "err", None, BytesIO(b"fail")
                )
            if req.full_url.endswith("/api/services/light/turn_off"):
                return FakeResponse(b"{}", "application/json")
            raise AssertionError(f"Unexpected URL: {req.full_url}")

        with patch("lib.capture_utils.add_ha_auth_header"):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                with self.assertRaises(Exception):
                    capture_from_ha_source(config, source_config)

        self.assertEqual(len(requests), 3)
        self.assertTrue(requests[2].full_url.endswith("/api/services/light/turn_off"))

    def test_capture_and_process_source_updates_db(self):
        img = Image.new("RGB", (8, 6), (120, 10, 10))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        raw = buf.getvalue()
        bbox = base64.b64encode(b"bbox").decode("utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            run_migrations(db_path)

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sources (name, source_type, enabled, poll_interval_s, config_json, updated_ts) "
                    "VALUES (?, 'http', 1, 60, ?, datetime('now'))",
                    ("meter-1", json.dumps({"url": "http://example.com/image.jpg"})),
                )
                source_id = cursor.lastrowid
                conn.commit()

            source_row = {
                "id": source_id,
                "name": "meter-1",
                "source_type": "http",
                "config_json": json.dumps({"url": "http://example.com/image.jpg"}),
            }

            with patch("lib.capture_utils.capture_from_http_source", return_value=(raw, "jpeg", False)):
                with patch("lib.capture_utils.reevaluate_latest_picture", return_value=(None, None, bbox)):
                    capture_and_process_source({}, db_path, source_row, object())

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT picture_number, picture_data_bbox FROM watermeters WHERE name = ?",
                    ("meter-1",),
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], bbox)

                cursor.execute(
                    "SELECT last_success_ts, last_error FROM sources WHERE id = ?",
                    (source_id,),
                )
                src_row = cursor.fetchone()
                self.assertIsNotNone(src_row[0])
                self.assertIsNone(src_row[1])


if __name__ == "__main__":
    unittest.main()
