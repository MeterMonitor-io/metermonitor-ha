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