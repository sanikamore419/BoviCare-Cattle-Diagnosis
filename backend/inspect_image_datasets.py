import os
from pathlib import Path
from collections import defaultdict

def inspect_dir(root, label):
    root = Path(root)
    print(f"\n{'='*60}")
    print(f"Dataset: {label}")
    print(f"Root: {root}")
    if not root.exists():
        print("  ERROR: path does not exist")
        return

    # Walk up to 4 levels, count images per folder
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    class_counts = defaultdict(int)
    total = 0
    corrupt = 0
    sample_sizes = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)
        imgs = [f for f in filenames if Path(f).suffix.lower() in IMAGE_EXTS]
        if imgs:
            class_counts[str(rel)] += len(imgs)
            total += len(imgs)
            # Sample first image size
            if len(sample_sizes) < 3:
                try:
                    from PIL import Image
                    img_path = Path(dirpath) / imgs[0]
                    with Image.open(img_path) as im:
                        sample_sizes.append((str(rel), im.size, im.mode))
                except Exception as e:
                    corrupt += 1

    print(f"Total images: {total}")
    print(f"Corrupt/unreadable (sampled): {corrupt}")
    print(f"\nFolder structure (image counts):")
    for folder, count in sorted(class_counts.items()):
        print(f"  {folder}: {count}")
    if sample_sizes:
        print(f"\nSample image sizes:")
        for name, size, mode in sample_sizes:
            print(f"  {name}: {size} {mode}")

    # Top-level dirs
    top = sorted([d for d in root.iterdir() if d.is_dir()])
    print(f"\nTop-level dirs: {[d.name for d in top]}")
    for d in top[:3]:
        sub = sorted([s for s in d.iterdir() if s.is_dir()])
        if sub:
            print(f"  {d.name}/ -> {[s.name for s in sub[:10]]}")

inspect_dir("ml/data/cattle_diseases", "Cattle Diseases Dataset")
inspect_dir("ml/data/lumpy_skin", "Lumpy Skin Dataset")
