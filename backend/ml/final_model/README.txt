BoviCare AI — Final ML Model
================================

MODEL
-----
Architecture: EfficientNet-B0
Framework: PyTorch
Input size: 224 x 224
Number of classes: 7
Dropout: 0.40

CLASSES
-------
0: HEALTHY
1: LSD
2: RINGWORM
3: FMD
4: IBK
5: PEDICULOSIS
6: DERMATOPHILOSIS

FINAL TEST PERFORMANCE
----------------------
Test samples: 2261
Accuracy: 95.67%
Macro Precision: 80.88%
Macro Recall: 79.91%
Macro F1: 80.35%
Weighted F1: 95.63%
Top-5 Accuracy: 99.69%

CALIBRATION
-----------
Expected Calibration Error: 0.0284
Maximum Calibration Error: 0.1307

REAL-WORLD EXPLORATORY TEST
---------------------------
Images tested: 10
Correct: 8

This was a small manually collected exploratory test
and is not a formal external benchmark.

INFERENCE PREPROCESSING
-----------------------
Resize: 224 x 224
Normalization mean:
0.485, 0.456, 0.406

Normalization std:
0.229, 0.224, 0.225

MODEL STATUS
------------
FROZEN

The checkpoint in this directory is the final candidate
for BoviCare application integration.

Do not overwrite this checkpoint during application
development. Create a new version if the model is
subsequently retrained.
