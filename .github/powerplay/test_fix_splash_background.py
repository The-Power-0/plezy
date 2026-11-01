#!/usr/bin/env python3
"""Regression: unified splash colors across Android resource qualifiers."""
from pathlib import Path
from tempfile import TemporaryDirectory
from fix_splash_background import COLOR, NAMES, update_splash_background

with TemporaryDirectory() as d:
    res = Path(d) / 'android/app/src/main/res'
    for qualifier in ('values', 'values-night'):
        p = res / qualifier / 'colors.xml'
        p.parent.mkdir(parents=True)
        p.write_text('<resources>' + ''.join(
            f'<color name="{name}">#000000</color>' for name in NAMES) + '</resources>')
    for qualifier in ('values-v31', 'values-night-v31'):
        p = res / qualifier / 'styles.xml'
        p.parent.mkdir(parents=True)
        p.write_text('<resources>' + ''.join(
            f'<style name="{name}"><item name="android:windowBackground">@color/splash_background</item></style>'
            for name in ('LaunchTheme', 'SplashTheme.Dark', 'SplashTheme.Oled', 'SplashTheme.Light', 'SplashTheme.System')) + '</resources>')
    update_splash_background(Path(d))
    update_splash_background(Path(d))
    for qualifier in ('values', 'values-night'):
        assert (res / qualifier / 'colors.xml').read_text().count(COLOR) == 5
    for qualifier in ('values-v31', 'values-night-v31'):
        assert (res / qualifier / 'styles.xml').read_text().count('android:windowSplashScreenBackground') == 5
print('PASS: unified splash resource regression')
