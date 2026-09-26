"""Regression checks for ZIP metadata used by CDDA's persistent JSON cache."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import package_release


class ReleaseArchiveTests(unittest.TestCase):
    def test_updated_json_has_a_different_cache_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "Berserk/berserk_arm_cannon_tileset.json"
            source = root / "mods" / relative
            source.parent.mkdir(parents=True)
            snapshots = []
            for name, count, mtime in (("old", 2, 1767225600), ("new", 1, 1790452800)):
                source.write_text(json.dumps([{"type": "mod_tileset"}] * count), encoding="utf-8")
                os.utime(source, (mtime, mtime))
                archive_path = root / f"{name}.zip"
                with patch.object(package_release, "ROOT", root):
                    package_release.write_archive(archive_path, ("Berserk",))
                with zipfile.ZipFile(archive_path) as archive:
                    snapshots.append((archive.getinfo(relative).date_time, archive.read(relative)))
            self.assertNotEqual(snapshots[0][1], snapshots[1][1])
            # CDDA compares mtimes only. Different JSON bytes must not retain
            # the same fixed date when the source file has been updated.
            self.assertNotEqual(snapshots[0][0], snapshots[1][0])

    def test_unchanged_source_produces_identical_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "mods" / "Berserk" / "sample.json"
            source.parent.mkdir(parents=True)
            source.write_text("[]\n", encoding="utf-8")
            os.utime(source, (1790452800, 1790452800))
            archives = [root / "first.zip", root / "second.zip"]
            with patch.object(package_release, "ROOT", root):
                for archive in archives:
                    package_release.write_archive(archive, ("Berserk",))
            self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())


if __name__ == "__main__":
    unittest.main()
