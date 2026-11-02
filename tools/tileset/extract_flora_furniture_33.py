#!/usr/bin/env python3
"""Copy the pinned native UltiCa frames without repainting or rotation."""
import argparse,hashlib,io,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-dir',required=True,type=Path);args=p.parse_args()
 d=json.loads((ROOT/'docs/flora-native-furniture-2026-11-02.json').read_text());images={}
 for file,sha in d['source_hashes'].items():
  raw=(args.native_dir/file).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError(file)
  images[file]=Image.open(io.BytesIO(raw)).convert('RGBA')
 out=Image.new('RGBA',(32*len(d['sources']),64))
 for i,source in enumerate(d['sources']):
  x,y,w,h=source['rect'];out.alpha_composite(images[source['source']].crop((x,y,x+w,y+h)),(32*i,64-h))
 b=io.BytesIO();out.save(b,format='PNG');raw=b.getvalue()
 if hashlib.sha256(raw).hexdigest()!=d['sha256']:raise ValueError('Output differs from reviewed atlas')
 (ROOT/'mods/Berserk'/d['sheet']).write_bytes(raw)
if __name__=='__main__':main()
