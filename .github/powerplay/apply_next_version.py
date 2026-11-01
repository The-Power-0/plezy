#!/usr/bin/env python3
"""Apply the reviewed PowerPlay changes to the exact published 1.0.0 source."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from fix_splash_background import update_splash_background


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    machinery = Path(__file__).resolve().parent
    release = json.loads((machinery / 'release.json').read_text())
    version, number = release['version'], release['build_number']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version) or type(number) is not int or number <= 10000:
        raise SystemExit('Invalid release version or non-increasing Android build number')
    pubspec = source / 'pubspec.yaml'
    original = pubspec.read_text()
    if original.count('version: 1.0.0+10000') != 1:
        raise SystemExit('Expected the pinned published PowerPlay 1.0.0 source')
    if 'applicationId = "com.power.powerplay"' not in (source / 'android/app/build.gradle.kts').read_text():
        raise SystemExit('The source does not have the PowerPlay application identity')
    patch = str(machinery / 'next-version.patch')
    # Check all hunks before writing anything. The patch is relative to the
    # source directory, which need not be a Git working tree.
    subprocess.run(['git', 'apply', '--check', patch], cwd=source, check=True)
    subprocess.run(['git', 'apply', patch], cwd=source, check=True)
    feature_patch = str(machinery / 'library-defaults.patch')
    subprocess.run(['git', 'apply', '--check', feature_patch], cwd=source, check=True)
    subprocess.run(['git', 'apply', feature_patch], cwd=source, check=True)
    update_splash_background(source)
    shutil.copyfile(source / 'assets/plezy.png', source / 'assets/powerplay.png')
    updated = pubspec.read_text().replace('version: 1.0.0+10000', f'version: {version}+{number}')
    updated = updated.replace('description: "A beautiful Plex and Jellyfin client for Flutter"',
                              'description: "PowerPlay: a Plex client for Fire TV"')
    pubspec.write_text(updated)
    print(f'Applied PowerPlay {version}+{number}: defaults, branding, and hardware-aware library visibility')


if __name__ == '__main__':
    main()
