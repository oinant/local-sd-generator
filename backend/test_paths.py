#!/usr/bin/env python3
import os
from pathlib import Path

# Test des chemins corrigés
paths = [
    '/mnt/d/StableDiffusion/apioutput',
    '/mnt/d/StableDiffusion/stable-diffusion-webui/outputs'
]

for path in paths:
    p = Path(path)
    print(f'Path: {path}')
    print(f'  Exists: {p.exists()}')
    print(f'  Is directory: {p.is_dir()}')
    print(f'  Readable: {os.access(path, os.R_OK)}')
    if p.exists() and p.is_dir():
        try:
            contents = list(p.iterdir())
            print(f'  Contents count: {len(contents)}')
            print(f'  First 3 items: {[item.name for item in contents[:3]]}')

            # Test comptage images pour le premier sous-dossier
            if contents:
                first_subdir = contents[0]
                if first_subdir.is_dir():
                    print(f'  Testing subdir: {first_subdir.name}')
                    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                    image_count = sum(1 for f in first_subdir.iterdir()
                                    if f.is_file() and f.suffix.lower() in image_extensions)
                    print(f'    Images in subdir: {image_count}')
        except Exception as e:
            print(f'  Error reading contents: {e}')
    print()