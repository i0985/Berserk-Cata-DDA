#!/usr/bin/env python3
"""Draw the generated map data, not a game screenshot or an AI/lighting test."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from build_wyald_rosine_locations import wyald, rosine

COLORS={'.':'#567746','d':'#93734e','T':'#23412b','#':'#646467',
        'm':'#c8aa6b','c':'#3c281a','v':'#e4cf8d','p':'#674831',
        'l':'#86a267','s':'#6d7464','G':'#332e20','R':'#4b402b'}
LABELS=[[(6,7,'Wagon bells'),(16,6,'Sleeping tents'),(39,12,'Command'),
         (10,22,'Kitchen'),(21,18,'Repair'),(18,28,'Cages'),
         (10,39,'Quarry bypass'),(37,36,'Wyald arena')],
        [(10,7,'Arrival'),(24,14,'False paradise'),(29,25,'Cocoon grove'),
         (8,26,'Gully bypass'),(14,38,'Last rest'),(36,26,'Giant roots'),
         (36,38,'Rosine nest')]]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    fig,axes=plt.subplots(1,2,figsize=(14,8.5))
    for ax,build,title,labels in zip(axes,[wyald,rosine],
                                   ['Black Dogs — 48 × 48','Mistvale — 48 × 48'],LABELS):
        field=build()
        rgb=np.array([[matplotlib.colors.to_rgb(COLORS[c]) for c in row] for row in field.rows])
        ax.imshow(rgb,origin='upper',extent=(-.5,47.5,47.5,-.5),interpolation='nearest')
        for kind,x,y in field.props:
            if kind.startswith('f_berserk_location_') or kind.endswith('shell_material'):
                marker='s';color='#ffe388'
            elif 'cocoon_watchful' in kind:marker='o';color='#f89bad'
            elif kind.endswith('_breach'):marker='*';color='#fff'
            elif kind.endswith(('_record','warning','story_cocoon','_scene')):
                marker='D';color='#8cd5ed'
            else:marker='.';color='#252623'
            ax.scatter(x,y,s=28 if marker!='.' else 14,c=color,marker=marker,
                       edgecolors='#212121' if marker!='.' else None,linewidths=.4,zorder=3)
        for _,x,y in field.actors:
            ax.scatter(x,y,s=32,c='#de4343',marker='x',linewidths=1.4,zorder=4)
        for x,y,label in labels:
            ax.text(x,y,label,ha='center',va='center',fontsize=8,color='white',
                    bbox=dict(boxstyle='round,pad=.18',facecolor='#121d1c',alpha=.85,edgecolor='none'),zorder=6)
        ax.axvline(23.5,color='white',linestyle='--',linewidth=.7,alpha=.6)
        ax.axhline(23.5,color='white',linestyle='--',linewidth=.7,alpha=.6)
        ax.set_xticks(range(0,48,6));ax.set_yticks(range(0,48,6))
        ax.set_title(title,fontsize=15,pad=14)
        ax.set_xlim(-1,48);ax.set_ylim(48,-1);ax.set_aspect('equal')
    fig.suptitle('Location data preview · CDDA 0.I-1 · not an in-game screenshot',fontsize=16,y=.95)
    fig.text(.5,.105,'Yellow squares: finite supplies   •   Pink circles: occupied cocoons   •   Red crosses: initial guards\n'
             'Blue diamonds: clues / warnings   •   White stars: existing breach seals   •   Dashed lines: OMT seams',ha='center',fontsize=11)
    fig.subplots_adjust(top=.86,bottom=.2,wspace=.12)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output,dpi=160)
    plt.close(fig)


if __name__=='__main__':main()
