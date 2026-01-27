v3.0.1-beta - 27.01.2026
- Implemented concept of image sources: MQTT, Home Assistant Camera (not yet implemented: HTTP)
- Added polling service for Home Assistant camera sources with configurable intervals
- Added source management UI: create, edit, and delete sources (MQTT, HA Camera, HTTP)
- Fixed a crtitical bug that caused the bounding box to be rotated 90-180 degrees in some cases
- Test capturing in source creation
- Fixed UnicodeDecodeError by base64 encoding binary image data in API responses
- Added sources table migration for database schema
- Improved error handling and logging in capture and polling operations
- Various UI improvements and bug fixes

v.2.1.1 - 26.01.2026
- Added sparkline chart to water meter cards showing consumption history
- Added "Clear Evaluations" button in meter details view
- Added "Clear history" link in setup benchmark section
- Benchmark now limits samples to available evaluations and shows message when too few historical images
- Improved timestamp formatting across the UI (WaterMeterCard, MeterDetails)
- Replaced checkboxes with switches in segmentation configurator
- Card title now truncates with ellipsis when too long
- Meter view now refreshes after dataset upload
- Removed unnecessary log output

v.2.1.0 - 26.01.2026
- Fixed BGR/RGB color space issue in YOLO model inference, significantly improving detection accuracy
- Added automatic threshold grid search: Finds optimal threshold values by maximizing model confidence
- Added light/dark theme support with automatic sync to Home Assistant theme preference
- Theme toggle button (auto/light/dark) in top-right corner
- Frontend now responsive and mobile-friendly
- Improved timestamp display on segmentation preview (now overlaid on image)
- Evaluation results now show two confidence values: used confidence (only digits not rejected by correction algorithm) and total confidence (all digits), showing used confidence more prominently
- Various UI improvements for both light and dark modes

v.2.0.5 - 29.12.2025
- Switched to ONNX Runtime for inference (~20% RAM usage, a lot faster on CPU)

v.2.0.0 - 29.12.2025

IMPORTANT: Increase the "Maximum evaluations" settings in the UI after updating to this version (at least 100).
- Improved setup process: benchmarks the threshold values using older evaluations
- Improved model (better dataset, new loss function)
- Improved Correction Algorithm: Added confidence thresholds
- Refactored API and Frontend
- All views mobile-friendly
- Improved device list
- Added bouding box to preview image
