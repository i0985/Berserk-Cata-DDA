#!/usr/bin/env python3
"""Render exact JSON geography, not a screenshot of CDDA or UltiCa."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from build_grunbeld_stronghold import SECTIONS,SPAWNS,SEAL
R=Path(__file__).resolve().parents[1]
COLORS={'.':'#777f55','d':'#a9946e','T':'#314432','#':'#64676a','s':'#848080','R':'#343a40','q':'#b0a697','_':'#c7bfa8','i':'#6c5d50','a':'#4b4440','+':'#d7a271'}
LABELS=[(13,4,'Осадные\nпозиции'),(13,17,'Пробитые\nворота'),(24,22,'Гарнизонный\nдвор'),(39,22,'Арсенал'),(11,36,'Карьер'),(31,32,'Казарма'),(39,34,'Перевязочная'),(39,41,'Кухня'),(23,38,'Ремонтный\nдвор'),(31,47,'Внутренний\nрубеж'),(13,61,'Кузница'),(36,59,'Арена'),(35,70,'Южный выход')]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 data=[o for o in json.loads((R/'mods/Berserk/mapgen/apostle_grunbeld.json').read_text()) if o['type']=='mapgen'];field=[['.']*48 for _ in range(72)];props=[]
 for m,(_,ox,oy) in zip(data,SECTIONS):
  for y,row in enumerate(m['object']['rows']):
   for x,c in enumerate(row):field[y+24*oy][x+24*ox]=c
  props += [(p['furn'],p['x']+ox*24,p['y']+oy*24) for p in m['object']['place_furniture']]
 fig,ax=plt.subplots(figsize=(10,14));ax.imshow(np.array([[matplotlib.colors.to_rgb(COLORS[c]) for c in row] for row in field]),origin='upper',interpolation='nearest')
 for fid,x,y in props:ax.scatter(x,y,s=18,c='#eed38f' if fid.startswith('f_berserk_grunbeld') else '#272826',marker='s',linewidths=0,zorder=3)
 for x,y in SPAWNS:ax.scatter(x,y,s=55,c='#ff775b',marker='^',edgecolors='#211',linewidths=.6,zorder=4)
 ax.scatter(*SEAL,s=70,c='#7ee8e6',marker='D',edgecolors='#211',linewidths=.6,zorder=4)
 for x,y,txt in LABELS:ax.text(x,y,txt,ha='center',va='center',fontsize=9,color='white',bbox=dict(boxstyle='round,pad=.15',facecolor='#1c2024',alpha=.87,edgecolor='none'),zorder=5)
 ax.axvline(23.5,c='white',ls='--',lw=.7,alpha=.5)
 for y in [23.5,47.5]:ax.axhline(y,c='white',ls='--',lw=.7,alpha=.5)
 ax.set_xticks(range(0,48,6));ax.set_yticks(range(0,72,6));ax.set_title('Крепость Грюнбельда · 48 × 72 клетки',fontsize=16,pad=16)
 fig.text(.5,.035,'Схема из JSON; не изображение игры\nКрасные треугольники — возможные точки одного босса; голубой ромб — прорыв\nПунктир — стыки OMT; жёлтые отметки — находки и свидетельства',ha='center',fontsize=10)
 fig.subplots_adjust(top=.94,bottom=.11);args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=140);plt.close(fig)
if __name__=='__main__':main()
