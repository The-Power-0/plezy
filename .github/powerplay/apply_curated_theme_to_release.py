#!/usr/bin/env python3
"""Apply PowerPlay's six curated palettes to the *published* source tree.

The published APK is based on the checksum-pinned 1.0.0 source, whose theme
provider differs significantly from the repository-root legacy Dart tree.
Adapt the existing MonoPalette system rather than replacing its provider,
Supporter gates, custom editor, startup logic, or D-pad navigation.
"""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
changes = {}

def edit(path, before, after):
    if path not in changes:
        changes[path] = (source / path).read_text()
    old = changes[path]
    count = old.count(before)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}: {before[:100]!r}")
    changes[path] = old.replace(before, after, 1)

def main():
    global source
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()

    # Shared, approved curated colors; adapt them to the published MonoPalette.
    canonical = ROOT / "lib/theme/powerplay_palette.dart"
    if not canonical.is_file():
        raise SystemExit("Missing curated palette definition in release machinery")
    dest = source / "lib/theme/powerplay_palette.dart"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(canonical, dest)

    (source / "lib/theme/powerplay_palette_release_adapter.dart").write_text("""\
import 'mono_theme.dart';
import 'powerplay_palette.dart';

export 'powerplay_palette.dart';

/// Use the existing published MonoPalette theme builder and its cache.
extension PowerPlayPaletteReleaseAdapter on PowerPlayPalette {
  MonoPalette toMonoPalette({required bool dark, bool oled = false}) {
    final c = colors(dark: dark, oled: oled);
    return MonoPalette(
      bg: c.background,
      surface: c.surface,
      outline: c.outline,
      text: c.text,
      textMuted: c.textMuted,
      accent: c.accent,
    );
  }
}
""")

    edit("lib/services/settings_service.dart",
         "import '../theme/mono_theme.dart' show MonoPalette;",
         "import '../theme/mono_theme.dart' show MonoPalette;\nimport '../theme/powerplay_palette.dart';")
    edit("lib/services/settings_service.dart",
         "  /// The Custom theme's colours, or null until the theme editor first saves",
         """  /// Curated color is independent of the existing brightness mode.
  /// Monochrome preserves the original PowerPlay appearance on upgrade.
  static const colorPalette = EnumPref<PowerPlayPalette>(
    'color_palette',
    values: PowerPlayPalette.values,
    defaultValue: PowerPlayPalette.monochrome,
  );

  /// The Custom theme's colours, or null until the theme editor first saves""")

    provider = "lib/providers/theme_provider.dart"
    edit(provider, "import '../theme/mono_theme.dart';",
         "import '../theme/mono_theme.dart';\nimport '../theme/powerplay_palette_release_adapter.dart';")
    edit(provider, "  MonoPalette? _customPalette;\n",
         "  MonoPalette? _customPalette;\n  PowerPlayPalette _curatedPalette = PowerPlayPalette.monochrome;\n")
    edit(provider,
         "prefs: [settings.SettingsService.themeMode, settings.SettingsService.customThemePalette],",
         "prefs: [settings.SettingsService.themeMode, settings.SettingsService.customThemePalette, settings.SettingsService.colorPalette],")
    edit(provider, "final previous = (_storedMode, _customPalette);",
         "final previous = (_storedMode, _customPalette, _curatedPalette);")
    edit(provider, "forceNotify: (_storedMode, _customPalette) != previous",
         "forceNotify: (_storedMode, _customPalette, _curatedPalette) != previous")
    edit(provider,
         "    _customPalette = service.read(settings.SettingsService.customThemePalette);",
         "    _customPalette = service.read(settings.SettingsService.customThemePalette);\n    _curatedPalette = service.read(settings.SettingsService.colorPalette);")
    edit(provider,
         "    if (changed || pushSplash) _updateSplashTheme(next.palette);",
         """    if (changed || pushSplash) {
      _updateSplashTheme(
        _curatedPalette == PowerPlayPalette.monochrome
            ? next.palette
            : _curatedPalette.toMonoPalette(dark: isDarkMode, oled: next.mode == settings.ThemeMode.oled),
      );
    }""")
    edit(provider,
         "  MonoPalette get activePalette => _choice.palette ?? (isDarkMode ? MonoPalette.dark : MonoPalette.light);",
         """  PowerPlayPalette get curatedPalette => _curatedPalette;

  MonoPalette get activePalette => _curatedPalette == PowerPlayPalette.monochrome
      ? (_choice.palette ?? (isDarkMode ? MonoPalette.dark : MonoPalette.light))
      : _curatedPalette.toMonoPalette(
          dark: isDarkMode,
          oled: _choice.mode == settings.ThemeMode.oled,
        );""")
    edit(provider,
         """  ThemeData get lightTheme => lightThemeFor(_choice.palette);
  ThemeData get darkTheme => darkThemeFor(_choice.palette);

  ThemeMode get materialThemeMode => materialThemeModeFor(_choice.palette);""",
         """  ThemeData get lightTheme => _curatedPalette == PowerPlayPalette.monochrome
      ? lightThemeFor(_choice.palette)
      : monoTheme(_curatedPalette.toMonoPalette(dark: false));
  ThemeData get darkTheme => _curatedPalette == PowerPlayPalette.monochrome
      ? darkThemeFor(_choice.palette)
      : monoTheme(_curatedPalette.toMonoPalette(dark: true, oled: _choice.mode == settings.ThemeMode.oled));

  ThemeMode get materialThemeMode {
    if (_curatedPalette == PowerPlayPalette.monochrome) return materialThemeModeFor(_choice.palette);
    return switch (_choice.mode) {
      settings.ThemeMode.system => ThemeMode.system,
      settings.ThemeMode.light => ThemeMode.light,
      _ => ThemeMode.dark,
    };
  }""")
    edit(provider,
         "  bool get isDarkMode => isDarkFor(_choice.palette, _systemBrightness);",
         """  bool get isDarkMode {
    if (_curatedPalette == PowerPlayPalette.monochrome) return isDarkFor(_choice.palette, _systemBrightness);
    return switch (_choice.mode) {
      settings.ThemeMode.system => _systemBrightness == Brightness.dark,
      settings.ThemeMode.light => false,
      _ => true,
    };
  }""")
    edit(provider, "  Future<void> reload() async {",
         """  Future<void> setCuratedPalette(PowerPlayPalette palette) async {
    final service = _settingsBinding.settings ?? await settings.SettingsService.getInstance();
    if (service.read(settings.SettingsService.colorPalette) == palette) return;
    await service.write(settings.SettingsService.colorPalette, palette);
    if (_settingsBinding.settings == null) {
      _readStored(service);
      _apply(pushSplash: true, forceNotify: true);
    }
  }

  Future<void> reload() async {""")

    main = "lib/main.dart"
    edit(main, "import 'theme/mono_theme.dart';",
         "import 'theme/mono_theme.dart';\nimport 'theme/powerplay_palette_release_adapter.dart';\nimport 'services/settings_service.dart' as color_settings show ThemeMode;")
    edit(main,
         "  final palette = ThemeProvider.resolveStored(settings, unlocked: SupporterService.startupUnlocked(settings)).palette;",
         """  final choice = ThemeProvider.resolveStored(settings, unlocked: SupporterService.startupUnlocked(settings));
  final curated = settings.read(SettingsService.colorPalette);
  if (curated != PowerPlayPalette.monochrome) {
    final mode = choice.mode;
    final flutterMode = switch (mode) {
      color_settings.ThemeMode.system => material.ThemeMode.system,
      color_settings.ThemeMode.light => material.ThemeMode.light,
      _ => material.ThemeMode.dark,
    };
    ThemeProvider.applyWindowChromeBrightness(
      mode == color_settings.ThemeMode.system
          ? WidgetsBinding.instance.platformDispatcher.platformBrightness == Brightness.dark
          : mode != color_settings.ThemeMode.light,
    );
    return (
      themeMode: flutterMode,
      lightTheme: monoTheme(curated.toMonoPalette(dark: false)),
      darkTheme: monoTheme(curated.toMonoPalette(dark: true, oled: mode == color_settings.ThemeMode.oled)),
    );
  }
  final palette = choice.palette;""")

    picker = "lib/screens/settings/theme_settings_screen.dart"
    edit(picker, "import '../../theme/mono_theme.dart';",
         "import '../../theme/mono_theme.dart';\nimport '../../theme/powerplay_palette_release_adapter.dart';")
    edit(picker,
         "          title: showPerks ? t.themeEditor.builtIn : null,",
         "          title: 'Display mode',")
    edit(picker,
         """          children: [for (final mode in _builtIns) option(mode)],
        ),""",
         """          children: [for (final mode in _builtIns) option(mode)],
        ),
        SettingsGroup(
          title: 'PowerPlay color themes',
          children: [
            for (final preset in PowerPlayPalette.values)
              FocusableListTile(
                key: ValueKey('curated_' + preset.name),
                leading: PaletteSwatch(palette: preset.toMonoPalette(dark: true)),
                title: Text(preset.label),
                subtitle: Text(preset.description),
                trailing: AppIcon(
                  theme.curatedPalette == preset
                      ? Symbols.radio_button_checked_rounded
                      : Symbols.radio_button_unchecked_rounded,
                  fill: 1,
                  color: theme.curatedPalette == preset
                      ? Theme.of(context).colorScheme.primary
                      : null,
                ),
                onTap: () => theme.setCuratedPalette(preset),
              ),
          ],
        ),""")

    # Dedicated test in the exact compiled source; don't replace existing
    # mature theme-provider and Supporter regression tests.
    test = source / "test/theme/powerplay_curated_palette_test.dart"
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text("""\
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:plezy/theme/mono_theme.dart';
import 'package:plezy/theme/powerplay_palette_release_adapter.dart';

void main() {
  test('six curated palettes each support light, dark and OLED', () {
    expect(PowerPlayPalette.values.length, 6);
    final colors = <Color>{};
    for (final palette in PowerPlayPalette.values) {
      final light = palette.toMonoPalette(dark: false);
      final dark = palette.toMonoPalette(dark: true);
      final oled = palette.toMonoPalette(dark: true, oled: true);
      expect(light.brightness, Brightness.light);
      expect(dark.brightness, Brightness.dark);
      expect(oled.bg, const Color(0xFF000000));
      expect(monoTheme(oled).scaffoldBackgroundColor, const Color(0xFF000000));
      expect(colors.add(dark.accent), isTrue);
    }
  });

  test('legacy monochrome remains identical to current built-ins', () {
    expect(PowerPlayPalette.monochrome.toMonoPalette(dark: false), MonoPalette.light);
    expect(PowerPlayPalette.monochrome.toMonoPalette(dark: true), MonoPalette.dark);
    expect(PowerPlayPalette.monochrome.toMonoPalette(dark: true, oled: true), MonoPalette.oled);
  });

  test('cached themes share identity for the same resolved palette', () {
    final one = PowerPlayPalette.signaturePurple.toMonoPalette(dark: true, oled: true);
    final two = PowerPlayPalette.signaturePurple.toMonoPalette(dark: true, oled: true);
    expect(identical(monoTheme(one), monoTheme(two)), isTrue);
  });
}
""")

    for rel, value in changes.items():
        (source / rel).write_text(value)
    print("Applied six PowerPlay curated palettes to published MonoPalette source; OLED independent.")

if __name__ == "__main__":
    main()
