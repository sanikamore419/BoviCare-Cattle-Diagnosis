"""
Image inference service for Models C and D.
Model C uses the final EfficientNet-B0 checkpoint; Model D remains MobileNetV2.
"""
from __future__ import annotations
import io, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, UnidentifiedImageError

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
FINAL_MODEL_DIR = Path(__file__).resolve().parents[1] / "final_model"
IMG_SIZE = 224
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB

_eval_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


@dataclass
class ImagePrediction:
    rank: int
    label: str
    probability: float


@dataclass
class ImagePredictionResult:
    model: str
    model_version: str
    predictions: list[ImagePrediction]
    top_label: str
    top_probability: float
    risk_level: str


def _risk(prob: float) -> str:
    if prob >= 0.70:
        return "high"
    if prob >= 0.40:
        return "moderate"
    return "low"


def _build_mobilenet(num_classes: int) -> nn.Module:
    m = models.mobilenet_v2(weights=None)
    m.classifier[1] = nn.Linear(m.last_channel, num_classes)
    return m


class _EfficientNetPredictor:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Optional[nn.Module] = None
        self._meta: Optional[dict] = None
        self._classes: Optional[list[str]] = None
        self._transform = None

    def _load(self) -> None:
        if self._model is not None:
            return

        with open(FINAL_MODEL_DIR / "model_config.json", encoding="utf-8") as f:
            config = json.load(f)
        with open(FINAL_MODEL_DIR / "preprocessing_config.json", encoding="utf-8") as f:
            preprocessing = json.load(f)
        with open(FINAL_MODEL_DIR / "class_names.json", encoding="utf-8") as f:
            class_metadata = json.load(f)

        if config["model_name"] != "EfficientNet-B0":
            raise RuntimeError("Unsupported Model C architecture in model_config.json.")
        classes = [class_metadata["classes"][str(i)] for i in range(class_metadata["num_classes"])]
        if len(classes) != config["num_classes"]:
            raise RuntimeError("Model C class metadata does not match model_config.json.")

        checkpoint = torch.load(
            FINAL_MODEL_DIR / config["checkpoint"],
            map_location="cpu",
            weights_only=True,
        )
        if checkpoint.get("class_names") != classes:
            raise RuntimeError("Model C checkpoint class order does not match class_names.json.")
        if checkpoint.get("config", {}).get("classes") != classes:
            raise RuntimeError("Model C checkpoint config class order does not match class_names.json.")

        net = models.efficientnet_b0(weights=None)
        net.classifier[1] = nn.Linear(net.classifier[1].in_features, config["num_classes"])
        net.load_state_dict(checkpoint["model_state_dict"], strict=True)
        net.eval()

        self._transform = transforms.Compose([
            transforms.Resize(tuple(preprocessing["input_size"])),
            transforms.ToTensor(),
            transforms.Normalize(
                preprocessing["normalization"]["mean"],
                preprocessing["normalization"]["std"],
            ),
        ])
        self._meta = {"model_version": config["model_version"]}
        self._classes = classes
        self._model = net

    def is_available(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False

    def predict(self, image_bytes: bytes) -> ImagePredictionResult:
        self._load()
        try:
            with io.BytesIO(image_bytes) as buf:
                img = Image.open(buf).convert("RGB")
        except Exception as e:
            raise ValueError(f"Cannot read image: {e}")

        tensor = self._transform(img).unsqueeze(0)
        with torch.inference_mode():
            logits = self._model(tensor)
            if logits.shape[1] != len(self._classes):
                raise RuntimeError("Model C output count does not match its class metadata.")
            probs = torch.softmax(logits, dim=1)[0].numpy()

        ranked = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        predictions = [
            ImagePrediction(rank=i + 1, label=self._classes[idx], probability=round(float(p), 4))
            for i, (idx, p) in enumerate(ranked)
        ]
        top = predictions[0]
        return ImagePredictionResult(
            model=self._model_name,
            model_version=self._meta["model_version"],
            predictions=predictions,
            top_label=top.label,
            top_probability=top.probability,
            risk_level=_risk(top.probability),
        )


class _CNNPredictor:
    def __init__(self, model_file: str, meta_file: str, model_name: str) -> None:
        self._model_file = MODELS_DIR / model_file
        self._meta_file  = MODELS_DIR / meta_file
        self._model_name = model_name
        self._model: Optional[nn.Module] = None
        self._meta: Optional[dict] = None

    def _load(self) -> None:
        if self._model is not None:
            return
        with open(self._meta_file) as f:
            self._meta = json.load(f)
        net = _build_mobilenet(self._meta["num_classes"])
        net.load_state_dict(torch.load(self._model_file, map_location="cpu", weights_only=True))
        net.eval()
        self._model = net

    def is_available(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False

    def predict(self, image_bytes: bytes) -> ImagePredictionResult:
        self._load()
        try:
            with io.BytesIO(image_bytes) as buf:
                img = Image.open(buf).convert("RGB")
        except (UnidentifiedImageError, Exception) as e:
            raise ValueError(f"Cannot read image: {e}")

        tensor = _eval_tf(img).unsqueeze(0)
        with torch.inference_mode():
            logits = self._model(tensor)
            probs  = torch.softmax(logits, dim=1)[0].numpy()

        classes = self._meta["classes"]
        ranked = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
        predictions = [
            ImagePrediction(rank=i + 1, label=classes[idx], probability=round(float(p), 4))
            for i, (idx, p) in enumerate(ranked)
        ]
        top = predictions[0]
        return ImagePredictionResult(
            model=self._model_name,
            model_version=self._meta["model_version"],
            predictions=predictions,
            top_label=top.label,
            top_probability=top.probability,
            risk_level=_risk(top.probability),
        )


cattle_image_predictor = _EfficientNetPredictor("cattle_image_classifier")

lumpy_skin_predictor = _CNNPredictor(
    "lumpy_skin_model.pt",
    "lumpy_skin_meta.json",
    "lumpy_skin_specialist",
)
