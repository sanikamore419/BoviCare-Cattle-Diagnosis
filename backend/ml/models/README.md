# Legacy image model metadata

The `cattle_image_meta.json` and `lumpy_skin_meta.json` files describe older
MobileNetV2 checkpoints in this directory. Their classes are respectively
`foot-and-mouth` / `healthy` / `lumpy` and `Lumpy Skin` / `Normal Skin`.
They do not describe the frozen seven-class EfficientNet-B0 checkpoint under
`backend/ml/final_model/`, whose class order is recorded in that directory's
`class_names.json`.

No model weights or metadata have been rewritten. The active API currently
uses the symptom prediction service and does not load the seven-class image
checkpoint. `frontend/src/config/imageClasses.js` is display metadata only; it
does not map old classifier outputs to new classes or run inference. Do not
infer an equivalence between the legacy classes and the seven-class model.
