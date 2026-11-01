import 'package:flutter/material.dart';

/// PowerPlay's curated UI palettes. Display brightness (including true-black
/// OLED) is an independent preference: every palette supports every mode.
enum PowerPlayPalette {
  signaturePurple(
    'Signature Purple',
    'Violet accents and rich plum surfaces',
    Color(0xFFA78BFA),
    Color(0xFF7445BD),
    Color(0xFF181125),
    Color(0xFF302047),
    Color(0xFFF7F4FC),
  ),
  moonlightBlue(
    'Moonlight Blue',
    'Cool blue accents over deep navy',
    Color(0xFF56B9F5),
    Color(0xFF126DA9),
    Color(0xFF0B1729),
    Color(0xFF1A334E),
    Color(0xFFF3F8FD),
  ),
  ember(
    'Ember',
    'Warm amber and dark charcoal',
    Color(0xFFFFAB69),
    Color(0xFFA65020),
    Color(0xFF20140F),
    Color(0xFF3B281D),
    Color(0xFFFCF7F2),
  ),
  evergreen(
    'Evergreen',
    'Forest greens and soft mint',
    Color(0xFF65DEAC),
    Color(0xFF14774F),
    Color(0xFF0D1D1A),
    Color(0xFF203D34),
    Color(0xFFF3FAF6),
  ),
  rose(
    'Rosé',
    'Soft rose accents and wine-toned surfaces',
    Color(0xFFF5A0CE),
    Color(0xFFAD377A),
    Color(0xFF24141F),
    Color(0xFF4A2840),
    Color(0xFFFCF5F9),
  ),
  monochrome(
    'Monochrome',
    'The original minimalist PowerPlay appearance',
    Color(0xFFEDEDED),
    Color(0xFF111111),
    Color(0xFF0E0F12),
    Color(0xFF15171C),
    Color(0xFFF7F7F8),
  );

  const PowerPlayPalette(
    this.label,
    this.description,
    this.darkAccent,
    this.lightAccent,
    this.darkBackground,
    this.darkSurface,
    this.lightBackground,
  );

  final String label;
  final String description;
  final Color darkAccent;
  final Color lightAccent;
  final Color darkBackground;
  final Color darkSurface;
  final Color lightBackground;

  /// A painted swatch, independent of the viewer's brightness setting.
  Color get swatch => darkAccent;

  PowerPlayPaletteColors colors({required bool dark, bool oled = false}) {
    // Keep the legacy Monochrome colors byte-for-byte for existing installs.
    if (this == PowerPlayPalette.monochrome) {
      if (oled) {
        return const PowerPlayPaletteColors(
          background: Color(0xFF000000),
          surface: Color(0xFF0A0A0A),
          outline: Color(0x1FFFFFFF),
          text: Color(0xFFEDEDED),
          textMuted: Color(0x99EDEDED),
          accent: Color(0xFFEDEDED),
          onAccent: Color(0xFF000000),
        );
      }
      if (dark) {
        return const PowerPlayPaletteColors(
          background: Color(0xFF0E0F12),
          surface: Color(0xFF15171C),
          outline: Color(0x1FFFFFFF),
          text: Color(0xFFEDEDED),
          textMuted: Color(0x99EDEDED),
          accent: Color(0xFFEDEDED),
          onAccent: Color(0xFF0E0F12),
        );
      }
      return const PowerPlayPaletteColors(
        background: Color(0xFFF7F7F8),
        surface: Color(0xFFFFFFFF),
        outline: Color(0x19000000),
        text: Color(0xFF111111),
        textMuted: Color(0x99111111),
        accent: Color(0xFF111111),
        onAccent: Color(0xFFFFFFFF),
      );
    }

    if (oled) {
      return PowerPlayPaletteColors(
        background: const Color(0xFF000000),
        // Dark cards may be tinted; the actual scaffold stays OLED black.
        surface: const Color(0xFF0A0A0A),
        outline: const Color(0x30FFFFFF),
        text: const Color(0xFFF2F1F5),
        textMuted: const Color(0xB2F2F1F5),
        accent: darkAccent,
        onAccent: const Color(0xFF101017),
      );
    }

    if (dark) {
      return PowerPlayPaletteColors(
        background: darkBackground,
        surface: darkSurface,
        outline: const Color(0x33FFFFFF),
        text: const Color(0xFFF2F1F5),
        textMuted: const Color(0xB2F2F1F5),
        accent: darkAccent,
        onAccent: const Color(0xFF101017),
      );
    }

    return PowerPlayPaletteColors(
      background: lightBackground,
      surface: const Color(0xFFFFFFFF),
      outline: const Color(0x26000000),
      text: const Color(0xFF18171D),
      textMuted: const Color(0xA618171D),
      accent: lightAccent,
      onAccent: const Color(0xFFFFFFFF),
    );
  }
}

@immutable
class PowerPlayPaletteColors {
  const PowerPlayPaletteColors({
    required this.background,
    required this.surface,
    required this.outline,
    required this.text,
    required this.textMuted,
    required this.accent,
    required this.onAccent,
  });

  final Color background;
  final Color surface;
  final Color outline;
  final Color text;
  final Color textMuted;
  final Color accent;
  final Color onAccent;
}
