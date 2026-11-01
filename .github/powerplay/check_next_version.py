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
    # Verify the APK source, not the legacy repository-root Android files.
    for qualifier in ['values', 'values-night']:
        colors = ET.parse(res / qualifier / 'colors.xml')
        for name in ['ic_launcher_background', 'splash_background', 'splash_dark',
                     'splash_oled', 'splash_light']:
            nodes = colors.findall(f"./color[@name='{name}']")
            assert len(nodes) == 1 and nodes[0].text == '#04070E', (qualifier, name)
    for qualifier in ['values-v31', 'values-night-v31']:
        themes = ET.parse(res / qualifier / 'styles.xml')
        for name in ['LaunchTheme', 'SplashTheme.Dark', 'SplashTheme.Oled',
                     'SplashTheme.Light', 'SplashTheme.System']:
            nodes = themes.findall(f"./style[@name='{name}']")
            assert len(nodes) == 1, (qualifier, name)
            bgs = [i.text for i in nodes[0] if i.attrib.get('name') == 'android:windowSplashScreenBackground']
            assert bgs == ['@color/splash_background'], (qualifier, name)
    ET.parse(res / 'drawable/powerplay_launch_background.xml')
    palette = (root / 'lib/theme/powerplay_palette.dart').read_text()
    for theme in ('signaturePurple', 'moonlightBlue', 'ember', 'evergreen', 'rose', 'monochrome'):
        assert theme in palette, theme
    assert 'if (oled)' in palette
    assert '0xFF000000' in palette
    assert "'color_palette'" in settings
    provider = (root / 'lib/providers/theme_provider.dart').read_text()
    assert 'colorPalette' in provider and 'palette: _palette' in provider
    assert 'colorPalette' in main and 'lightTheme: monoTheme(dark: false, palette: palette)' in main
    appearance = (root / 'lib/screens/settings/appearance_settings_screen.dart').read_text()
    assert '_PaletteGallery' in appearance
    assert (root / 'test/theme/mono_theme_test.dart').read_text().count('every curated palette') == 1
    assert (root / 'test/services/powerplay_defaults_test.dart').is_file()
    print('PASS: actual build source has PowerPlay identity, defaults, splash, themes, OLED support, About, and regression tests')


if __name__ == '__main__':
    main()
