#!/usr/bin/env python3
"""Canonical 3.3 story rebuild, followed by the approved visual policy."""
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILDERS=[
    'build_godo_dialogue_33.py',
    'build_rickert_dialogue_33.py',
    'build_apostol_body_rules_33.py',
    'build_skull_knight_dialogue_33.py',
    'build_direct_hunt_missions_33.py',
    'build_flora_dialogue_33.py',
    'build_count_prisoner_dialogue_33.py',
    'build_named_apostle_dialogues_33.py',
    'build_godhand_dialogue_33.py',
    'build_common_dialogue_33.py',
    'build_reference_journal_33.py',
    'apply_visual_fallbacks_33.py',
    'apply_english_source_33.py',
]

if __name__=='__main__':
    for builder in BUILDERS:
        subprocess.run([sys.executable,str(ROOT/'tools'/builder)],cwd=ROOT,check=True)
