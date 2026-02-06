import json
import unittest
from unittest.mock import patch

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.functions import publish_value, publish_registration


class DummyMQTT:
    def __init__(self):
        self.calls = []

    def publish(self, topic, payload, qos=0, retain=False):
        self.calls.append((topic, payload, qos, retain))


class TestPublish(unittest.TestCase):
    def test_publish_value(self):
        client = DummyMQTT()
        config = {"publish_to": "MeterMonitor/{device}/"}

        with patch("builtins.print"):
            publish_value(client, config, "meter-1", 1234)

        self.assertEqual(len(client.calls), 1)
        topic, payload, qos, retain = client.calls[0]
        self.assertEqual(topic, "MeterMonitor/meter-1/value")
        self.assertEqual(qos, 1)
        self.assertTrue(retain)

        data = json.loads(payload)
        self.assertAlmostEqual(data["value"], 1.234, places=6)

    def test_publish_registration(self):
        client = DummyMQTT()
        config = {"publish_to": "MeterMonitor/{device}/"}

        with patch("builtins.print"):
            publish_registration(client, config, "meter-1", "value")

        self.assertEqual(len(client.calls), 1)
        topic, payload, qos, retain = client.calls[0]
        self.assertEqual(topic, "MeterMonitor/meter-1/config")
        self.assertEqual(qos, 1)
        self.assertTrue(retain)

        data = json.loads(payload)
        self.assertEqual(data["state_topic"], "MeterMonitor/meter-1/value")
        self.assertEqual(data["unique_id"], "watermeter_meter-1")
        self.assertEqual(data["device"]["name"], "meter-1")
        self.assertEqual(data["unit_of_measurement"], "m\u00b3")


if __name__ == "__main__":
    unittest.main()
