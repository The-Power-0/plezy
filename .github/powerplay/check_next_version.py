#!/usr/bin/env python3
"""Check branding and settings in the actual source consumed by the APK build."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    root = parser.parse_args().source
    data = json.loads((Path(__file__).parent / 'release.json').read_text())
    assert f"version: {data['version']}+{data['build_number']}" in (root / 'pubspec.yaml').read_text()
    settings = (root / 'lib/services/settings_service.dart').read_text()
    for text in [
        'defaultValue: ContinueWatchingAction.details,',
        'defaultValue: EpisodeAction.details,',
        "BoolPref('match_content_frame_rate', defaultValue: true)",
        "IntPref('auto_skip_delay', defaultValue: 3)",
        "'skip_intro_mode',\n    legacyKey: _legacyAutoSkipIntroKey,\n    defaultValue: SkipMarkerMode.auto,",
        "_SkipMarkerModePref('skip_credits_mode', legacyKey: _legacyAutoSkipCreditsKey)",
    ]:
        assert text in settings, text
    main = (root / 'lib/main.dart').read_text()
    assert 'plezy_adaptive_foreground.svg' not in main
    assert main.count("Image.asset('assets/powerplay.png'") == 2
    assert (root / 'assets/powerplay.png').read_bytes() == (root / 'assets/plezy.png').read_bytes()
    about = (root / 'lib/screens/settings/about_screen.dart').read_text()
    for text in ["const appName = 'PowerPlay'", 'assets/powerplay.png',
                 'Plex client for Fire TV', 'Based on Plezy by edde746', 'GNU GPLv3',
                 'github.com/The-Power-0/PowerPlay', 'const LicensesScreen()']:
        assert text in about, text
    res = root / 'android/app/src/main/res'
    adaptive = (res / 'mipmap-anydpi-v26/ic_launcher.xml').read_text()
    assert '@drawable/powerplay_foreground' in adaptive
    assert '@drawable/ic_launcher_foreground' not in adaptive
    assert '@drawable/powerplay_foreground' in (res / 'drawable/splash_icon.xml').read_text()
    for path in ['values/styles.xml', 'values-night/styles.xml']:
        tree = ET.parse(res / path)
        for style in tree.findall('style'):
            name = style.attrib['name']
            if name == 'LaunchTheme' or name.startswith('SplashTheme.'):
                background = next(i.text for i in style if i.attrib.get('name') == 'android:windowBackground')
                assert background == '@drawable/powerplay_launch_background', (path, name)
    ET.parse(res / 'drawable/powerplay_launch_background.xml')
    assert (root / 'test/services/powerplay_defaults_test.dart').is_file()
    print('PASS: actual build source has PowerPlay identity, defaults, splash, About, and regression tests')


if __name__ == '__main__':
    main()
