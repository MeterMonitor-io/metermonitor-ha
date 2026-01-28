v3.0.1 - 28.01.2026
- Added configurable correctional algorithm with Full/Light modes
  - Full mode: Complete correction with positive flow check, max flow rate validation, and fallback handling
  - Light mode: Only replaces rotation class and low-confidence digits with last known values
- Added toggle switch in setup to select between Full/Light correctional algorithm
- Added "Reset Corr. Alg." context menu item to mark all evaluations as outdated for re-evaluation
- Added API endpoint `/api/watermeters/{name}/evaluations/mark-outdated` to trigger re-evaluation
- Display current correction algorithm mode (Full/Light) in meter details
- Max flow rate input is automatically disabled when Light mode is selected
- Fixed ROI template editor not applying point updates correctly (v-model binding issue)
- Fixed display_corners not being properly scaled to pixel coordinates when saving ROI templates
- Added `use_correctional_alg` setting to database schema with migration support

v3.0.0 - 27.01.2026
- Implemented concept of image sources: MQTT, Home Assistant Camera, HTTP
- Added template-based ROI extractor (ORBExtractor) for manual display region selection
- Added ROI extraction framework with BypassExtractor, YOLOExtractor, and ORBExtractor
- Added selectable ROI extractors in setup with template configuration UI
- Added template management: create, edit, and configure reference points for ORB matching
- Added HTTP source support with custom headers, body, and URL configuration
- Added polling service for Home Assistant camera sources with configurable intervals
- Added source management UI: create, edit, and delete sources (MQTT, HA Camera, HTTP)
- Revamped frontend layouts with unified header controls and improved responsiveness for meter and source views
- Added source validation for water meters and a collapsible source editor in meter details
- Enhanced meter charts with combined usage/confidence series and improved layout
- Added correction evaluation metadata (flow rate, deltas, rejection reasons, digit-change stats) with full API + UI exposure
- Added evaluation detail dialog with dedicated API endpoint and click-to-view in evaluation results
- Overhauled evaluation list UX: infinite scroll, relative timestamps, per-digit grouping, and clearer outdated separation
- Added bounding box validation and warnings for missing bounding boxes in meter details/cards
- Added `used_confidence` persistence in history/evaluations for more consistent confidence reporting
- Improved Home Assistant camera capture flow with better error messaging and flash light configuration UX
- Removed obsolete endpoints and streamlined source/setup UI
- Fixed a critical bug that caused the bounding box to be rotated 90-180 degrees in some cases
- Test capturing in source creation
- Fixed UnicodeDecodeError by base64 encoding binary image data in API responses
- Added sources table migration for database schema
- Improved error handling and logging in capture and polling operations
- Fixed `/api/watermeters/{name}/evals/count` routing to avoid eval_id parsing errors
- Reduced excessive debug logging in Home Assistant token handling and HTTP requests
- Various UI improvements and bug fixes
- Added shared Home Assistant authentication utilities with centralized token management
- Implemented supervisor token support with automatic fallback to manual tokens
- Added homeassistant_api permission for proper supervisor endpoint access
- Improved Home Assistant API error handling with context-aware 401 error messages
- Optimized Docker build process with layer caching and platform-specific builds
- Fixed configuration loading with deep merge for nested config options
- Ensured default values from ha_default_settings.json are properly applied

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
