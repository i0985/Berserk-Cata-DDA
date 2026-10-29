#!/usr/bin/env python3
"""Reproduce native UltiCa layer copies from the pinned, original source sheet.

No art is redrawn and no authored Berserk image is an output of this script.
Usage: python tools/tileset/extract_apostle_overlays_33.py --source-sheet /path/human_body.png
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sheet', required=True, type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT/'docs/apostol-native-sprite-sources-33.json').read_text())
    raw = args.source_sheet.read_bytes()
    if hashlib.sha256(raw).hexdigest() != data['source_sha256']:
        raise ValueError('Source sheet differs from the reviewed CDDA 0.I UltiCa sheet')
    source = Image.open(io.BytesIO(raw)).convert('RGBA')
    out = Image.new('RGBA', (32*len(data['tiles']), 36))
    for i, tile in enumerate(data['tiles']):
        sex = 'female' if tile['id'].startswith('overlay_female_') else 'male'
        stem = tile['id'].split('_mutation_BERSERK_', 1)[1].removesuffix('_FORM')
        layers = [s for s in data['sources'] if s['sex']==sex and s['target']==stem]
        image = Image.new('RGBA', (32,36))
        for layer in layers:
            x,y,w,h = layer['rect']
            image.alpha_composite(source.crop((x,y,x+w,y+h)))
        out.alpha_composite(image, (32*i,0))
    buffer = io.BytesIO(); out.save(buffer,format='PNG'); result=buffer.getvalue()
    if hashlib.sha256(result).hexdigest() != data['sha256']:
        raise ValueError('Extracted PNG differs from the saved reviewed result')
    path = ROOT/'mods/Berserk'/data['sheet']; path.write_bytes(result)
    print('Reproduced 16 native overlays; existing authored sheets unchanged.')


if __name__ == '__main__': main()
