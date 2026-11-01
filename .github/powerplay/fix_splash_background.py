#!/usr/bin/env python3
"""Align released PowerPlay splash resources with the approved icon background."""
import argparse
import re
from pathlib import Path

COLOR = '#04070E'
NAMES = ('ic_launcher_background', 'splash_background', 'splash_dark', 'splash_oled', 'splash_light')
STYLES = re.compile(r'(<style name="(?:LaunchTheme|SplashTheme\.[^"]+)"[^>]*>)(.*?)(</style>)', re.S)
SYSTEM_BACKGROUND = '<item name="android:windowSplashScreenBackground">@color/splash_background</item>'


def update_splash_background(source: Path) -> None:
    res = source / 'android/app/src/main/res'
    for qualifier in ('values', 'values-night'):
        path = res / qualifier / 'colors.xml'
        xml = path.read_text(encoding='utf-8')
        for name in NAMES:
            pattern = r'(<color\s+name="' + re.escape(name) + r'">)\s*#[0-9A-Fa-f]{6,8}(\s*</color>)'
            xml, count = re.subn(pattern, lambda m: m.group(1) + COLOR + m.group(2), xml)
            if count != 1:
                raise ValueError(f'{path}: {name} found {count} times, expected 1')
        path.write_text(xml, encoding='utf-8')
    # Android 12 has a separate system splash background color.
    for qualifier in ('values-v31', 'values-night-v31'):
        path = res / qualifier / 'styles.xml'
        xml = path.read_text(encoding='utf-8')
        seen = 0
        def patch(match):
            nonlocal seen
            seen += 1
            start, body, end = match.groups()
            if 'android:windowSplashScreenBackground' in body:
                body, count = re.subn(
                    r'<item name="android:windowSplashScreenBackground">[^<]*</item>',
                    SYSTEM_BACKGROUND, body)
            else:
                body, count = re.subn(
                    r'(<item name="android:windowBackground">[^<]*</item>)',
                    lambda m: m.group(1) + '\n        ' + SYSTEM_BACKGROUND, body, count=1)
            if count != 1:
                raise ValueError(f'Missing or repeated system splash background in {path}')
            return start + body + end
        xml = STYLES.sub(patch, xml)
        if seen != 5:
            raise ValueError(f'Expected five splash themes in {path}, found {seen}')
        path.write_text(xml, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    update_splash_background(parser.parse_args().source)
    print('PASS: PowerPlay icon and launch canvas match in all themes')
