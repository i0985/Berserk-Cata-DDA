#!/usr/bin/env python3
"""Prepare staged Git changes for the connected GitHub API; never publishes.

The caller must upload binary blobs, create the tree and commit, update the ref
with the expected parent, compare tree SHA, and verify the remote branch head.
No tokens or other credentials are read or exported.
"""
import argparse
import base64
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    base = git('rev-parse', 'HEAD')
    entries = []
    changes = git('diff', '--cached', '--name-status', '--no-renames').splitlines()
    for line in changes:
        status, path = line.split('\t', 1)
        if status == 'D':
            entries.append(dict(path=path, mode='100644', type='blob', sha=None))
            continue
        raw = subprocess.check_output(['git', 'show', ':' + path])
        mode = git('ls-files', '-s', '--', path).split()[0]
        obj = dict(path=path, mode=mode, type='blob')
        try: obj['content'] = raw.decode('utf-8')
        except UnicodeDecodeError: obj['base64'] = base64.b64encode(raw).decode('ascii')
        entries.append(obj)
    result = dict(base=base, base_tree=git('rev-parse', 'HEAD^{tree}'),
                  expected_tree=git('write-tree'), entries=entries)
    output = Path(args.output)
    output.write_text(json.dumps(result, ensure_ascii=False))
    print(json.dumps(dict(base=base, tree=result['expected_tree'], entries=len(entries),
                          chars=len(output.read_text()), bytes=output.stat().st_size)))


if __name__ == '__main__': main()
