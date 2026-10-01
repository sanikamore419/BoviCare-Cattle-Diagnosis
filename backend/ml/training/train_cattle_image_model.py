"""
CNN Model C — Cattle Disease Image Classifier
Dataset: https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets
3244 images, 3 classes: foot-and-mouth (746), healthy (1291), lumpy (1207)
All images 300x300 RGB (lumpy class varies)

Architecture: MobileNetV2 pretrained on ImageNet, final classifier replaced.
Chosen for: small dataset size, CPU-friendly, fast convergence with transfer learning.
Input size: 224x224 (MobileNetV2 standard)
Split: 70% train / 15% val / 15% test (stratified)
"""
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score
)
from sklearn.model_selection import train_test_split

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

DATA_ROOT  = Path(__file__).resolve().parents[1] / "data" / "cattle_diseases" / "Cows datasets"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)

IMG_SIZE   = 224
BATCH_SIZE = 32
EPOCHS     = 15
LR         = 1e-3
PATIENCE   = 4
MODEL_VERSION = "bovicare-cattle-image-v1"

train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
eval_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def make_splits(dataset):
    labels = [dataset.targets[i] for i in range(len(dataset))]
    idx = list(range(len(dataset)))
    train_idx, tmp_idx = train_test_split(idx, test_size=0.30, stratify=labels, random_state=SEED)
    tmp_labels = [labels[i] for i in tmp_idx]
    val_idx, test_idx = train_test_split(tmp_idx, test_size=0.50, stratify=tmp_labels, random_state=SEED)
    return train_idx, val_idx, test_idx


def build_model(num_classes):
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    # Freeze all layers except classifier
    for param in model.features.parameters():
        param.requires_grad = False
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)
    return model


def evaluate(model, loader, device):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            preds = outputs.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return np.array(all_preds), np.array(all_labels)


def main():
    print("=== CNN Model C — Cattle Disease Image Classifier ===\n")
    device = torch.device("cpu")
    print(f"Device: {device}")

    # Load full dataset with eval transforms first (for splits)
    full_dataset = datasets.ImageFolder(DATA_ROOT, transform=eval_tf)
    classes = full_dataset.classes
    class_to_idx = full_dataset.class_to_idx
    num_classes = len(classes)

    print(f"Classes ({num_classes}): {classes}")
    print(f"Class distribution:")
    for cls, idx in class_to_idx.items():
        count = sum(1 for _, t in full_dataset.samples if t == idx)
        print(f"  {cls}: {count}")
    print(f"Total images: {len(full_dataset)}")

    train_idx, val_idx, test_idx = make_splits(full_dataset)
    print(f"\nSplit: train={len(train_idx)}, val={len(val_idx)}, test={len(test_idx)}")

    # Train set uses augmentation transforms
    train_dataset = datasets.ImageFolder(DATA_ROOT, transform=train_tf)
    train_loader = DataLoader(Subset(train_dataset, train_idx), batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(Subset(full_dataset,  val_idx),   batch_size=BATCH_SIZE, shuffle=False)
    test_loader  = DataLoader(Subset(full_dataset,  test_idx),  batch_size=BATCH_SIZE, shuffle=False)

    # Class weights for imbalance
    train_labels = [full_dataset.targets[i] for i in train_idx]
    counts = np.bincount(train_labels)
    weights = torch.tensor(1.0 / counts, dtype=torch.float32).to(device)
    print(f"\nClass weights: {dict(zip(classes, weights.numpy().round(4)))}")

    model = build_model(num_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2, factor=0.5)

    print(f"\nTraining MobileNetV2 (frozen features, training classifier only)")
    print(f"Epochs={EPOCHS}, BatchSize={BATCH_SIZE}, LR={LR}, EarlyStop patience={PATIENCE}\n")

    best_val_f1 = -1
    patience_counter = 0
    best_state = None

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss, correct, total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += imgs.size(0)

        train_acc = correct / total
        train_loss /= total

        val_preds, val_labels = evaluate(model, val_loader, device)
        val_acc = accuracy_score(val_labels, val_preds)
        val_f1  = f1_score(val_labels, val_preds, average="macro")
        scheduler.step(1 - val_f1)

        print(f"Epoch {epoch:2d}/{EPOCHS}  train_loss={train_loss:.4f}  train_acc={train_acc:.4f}  val_acc={val_acc:.4f}  val_macro_f1={val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"Early stopping at epoch {epoch}")
                break

    # Load best weights
    model.load_state_dict(best_state)

    # Test evaluation
    test_preds, test_labels = evaluate(model, test_loader, device)
    test_acc  = accuracy_score(test_labels, test_preds)
    test_f1   = f1_score(test_labels, test_preds, average="macro")

    print(f"\n=== Test-set evaluation ({len(test_idx)} samples) ===")
    print(f"Accuracy:  {test_acc:.4f}")
    print(f"Macro F1:  {test_f1:.4f}")
    print("\nPer-class report:")
    print(classification_report(test_labels, test_preds, target_names=classes))

    # Save artifacts
    torch.save(model.state_dict(), MODELS_DIR / "cattle_image_model.pt")
    meta = {
        "model_version": MODEL_VERSION,
        "architecture": "MobileNetV2",
        "num_classes": num_classes,
        "classes": classes,
        "img_size": IMG_SIZE,
        "test_accuracy": round(test_acc, 4),
        "test_macro_f1": round(test_f1, 4),
    }
    with open(MODELS_DIR / "cattle_image_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nArtifacts saved:")
    print(f"  ml/models/cattle_image_model.pt")
    print(f"  ml/models/cattle_image_meta.json")
    print("\nModel C training complete.")


if __name__ == "__main__":
    main()
