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