#!/usr/bin/env python3
"""Preview exact map data; this is not an UltiCa/game screenshot."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from build_flora_treehouse import SECTIONS, FLORA, GUARDS

ROOT=Path(__file__).resolve().parents[1]
COLORS={'.':'#769966','d':'#b99868','T':'#21452d','#':'#75513a','_':'#c9a976','r':'#bd764d','+':'#edd1a6','W':'#a1d1cd','G':'#493a27','R':'#65503b'}
LABELS=[(15,7,'Библиотека'),(15,15,'Гостиная'),(12,25,'Гостевая I'),(18,28,'Гостевая II'),(24,14,'Духовное\nдерево'),(34,15,'Кухня'),(39,9,'Кладовая'),(35,21,'Мастерская'),(24,26,'Южная галерея'),(8,36,'Травы'),(34,38,'Сад'),(4,14,'Западный\nвыход'),(24,42,'Южный\nвыход')]
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    maps=json.loads((ROOT/'mods/Berserk/mapgen/flora_manor.json').read_text());field=[['.']*48 for _ in range(48)];props=[]
    for obj,(_,ox,oy) in zip(maps,SECTIONS):
        for y,row in enumerate(obj['object']['rows']):
            for x,c in enumerate(row):field[y+oy*24][x+ox*24]=c
        props += [(p['furn'],p['x']+ox*24,p['y']+oy*24) for p in obj['object']['place_furniture']]
    fig,ax=plt.subplots(figsize=(11,11));rgb=np.array([[matplotlib.colors.to_rgb(COLORS[c]) for c in row] for row in field])
    ax.imshow(rgb,origin='upper',interpolation='nearest')
    for id_,x,y in props:
        aid=id_.startswith('f_berserk_flora_aid_');book=id_.endswith('_shelf');bed=id_.endswith('linen_bed');optional=id_.endswith(('manuscript','root_niche'))
        marker='s' if aid or bed or book else 'D' if optional else '.';color='#ffe180' if aid else '#984626' if book else '#faf3dc' if bed else '#78ddec' if optional else '#342b23'
        ax.scatter(x,y,s=60 if marker!='.' else 30,c=color,marker=marker,edgecolors='#32261c' if marker!='.' else None,linewidths=.8,zorder=3)
    ax.scatter(*FLORA,s=65,c='#b6f4db',marker='*',edgecolors='#111',zorder=5)
    for x,y in GUARDS:ax.scatter(x,y,s=60,c='#95d289',marker='^',edgecolors='#111',zorder=5)
    for x,y,txt in LABELS:ax.text(x,y,txt,ha='center',va='center',fontsize=10,color='white',bbox=dict(boxstyle='round,pad=.15',facecolor='#202b22',alpha=.88,edgecolor='none'),zorder=6)
    ax.axvline(23.5,ls='--',lw=.6,c='white',alpha=.5);ax.axhline(23.5,ls='--',lw=.6,c='white',alpha=.5)
    ax.set_xticks(range(0,48,6));ax.set_yticks(range(0,48,6));ax.set_title('Дом Флоры у духовного дерева · 48 × 48 клеток',fontsize=17,pad=18)
    fig.text(.5,.055,'Схема из JSON, не скриншот игры\nЖёлтые квадраты — разрешённые запасы; голубые ромбы — рукопись и ниша\nЗелёные треугольники — стражи; пунктир — стыки OMT',ha='center',fontsize=11)
    fig.subplots_adjust(top=.9,bottom=.16);args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=150);plt.close(fig)
if __name__=='__main__':main()
