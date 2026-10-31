#!/usr/bin/env python3
"""Rebrand the frozen optimized Plezy 2.25.0 source as side-by-side PowerPlay."""
import argparse
import base64
import io
import re
import tarfile
from pathlib import Path

from PIL import Image

ROOT = Path.cwd()

def change(path, old, new):
    p = ROOT / path
    original = p.read_text(encoding="utf-8")
    if old not in original:
        raise SystemExit("Branding input changed: " + path + " / " + old)
    p.write_text(original.replace(old, new), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-b64", required=False)
    args = parser.parse_args()

    change("android/app/build.gradle.kts", 'applicationId = "com.edde746.plezy"', 'applicationId = "com.power.powerplay"')
    manifest = ROOT / "android/app/src/main/AndroidManifest.xml"
    s = manifest.read_text(encoding="utf-8")
    assert s.count('android:label="Plezy"') == 1
    assert s.count('<data android:scheme="plezy"/>') == 1
    s = s.replace('android:label="Plezy"', 'android:label="PowerPlay"')
    s = s.replace('<data android:scheme="plezy"/>', '<data android:scheme="powerplay"/>')
    s, n = re.subn(r'android:(name|targetActivity)="\.((?:PlezyActivity|MainActivity|appicon\.[^"]+))"', r'android:\1="com.edde746.plezy.\2"', s)
    assert n > 5, "Component names need explicit original Kotlin namespace"
    s = s.replace("com.edde746.plezy.fileprovider", "com.power.powerplay.fileprovider")
    s = s.replace("com.edde746.plezy.systemshelf.artwork", "com.power.powerplay.systemshelf.artwork")
    manifest.write_text(s, encoding="utf-8")
    changes = {
        "android/app/src/main/kotlin/com/edde746/plezy/ExternalPlayerChannel.kt": [
            ("com.edde746.plezy.fileprovider", "com.power.powerplay.fileprovider")],
        "android/app/src/main/kotlin/com/edde746/plezy/deeplink/DeepLinkPlugin.kt": [
            ('private const val SCHEME = "plezy"', 'private const val SCHEME = "powerplay"')],
        "android/app/src/main/kotlin/com/edde746/plezy/watchnext/SystemShelfArtworkProvider.kt": [
            ("com.edde746.plezy.systemshelf.artwork", "com.power.powerplay.systemshelf.artwork")],
        "android/app/src/main/kotlin/com/edde746/plezy/watchnext/WatchNextProvider.kt": [
            ('uri.scheme != "plezy"', 'uri.scheme != "powerplay"'),
            ('.scheme("plezy")', '.scheme("powerplay")')],
        "lib/services/deep_links/deep_link.dart": [
            ("static const scheme = 'plezy'", "static const scheme = 'powerplay'")],
        "android/app/src/main/res/drawable/splash_icon.xml": [
            ("@drawable/ic_launcher_foreground", "@drawable/powerplay_foreground")],
        "android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml": [
            ("@drawable/ic_launcher_foreground", "@drawable/powerplay_foreground")],
        "android/app/src/main/res/values/colors.xml": [
            ('name="ic_launcher_background">#ffffff', 'name="ic_launcher_background">#060810')],
    }
    for path, pairs in changes.items():
        for old, new in pairs:
            change(path, old, new)

    for root in ("test", "android/app/src/test"):
        for p in (ROOT / root).rglob("*"):
            if p.suffix not in (".dart", ".kt"):
                continue
            s = p.read_text(encoding="utf-8")
            t = s.replace("plezy://", "powerplay://").replace("PLEZY://", "POWERPLAY://")
            if t != s:
                p.write_text(t, encoding="utf-8")
    for p in (ROOT / "lib/i18n").glob("*"):
        if p.suffix not in (".dart", ".json"):
            continue
        s = p.read_text(encoding="utf-8")
        t = s.replace('"title": "Plezy"', '"title": "PowerPlay"')
        if p.name.startswith("strings_"):
            t = t.replace("'Plezy'", "'PowerPlay'")
        if t != s:
            p.write_text(t, encoding="utf-8")

    if args.assets_b64:
        raw = base64.b64decode(Path(args.assets_b64).read_text(encoding="ascii").strip(), validate=True)
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            icon = Image.open(io.BytesIO(archive.extractfile("icon.webp").read())).convert("RGB")
            banner = Image.open(io.BytesIO(archive.extractfile("banner.webp").read())).convert("RGB")
    else:
        from PIL import ImageDraw
        icon = Image.new("RGB", (512, 512), "#070917")
        d = ImageDraw.Draw(icon)
        d.rounded_rectangle((62, 102, 450, 389), radius=36, outline="#af3cf5", width=24)
        d.rectangle((241, 388, 272, 416), fill="#ad36ec")
        d.rounded_rectangle((187, 411, 328, 429), radius=8, fill="#ad36ec")
        d.rounded_rectangle((172, 164, 364, 334), radius=73, fill="#d833f7")
        d.polygon([(172, 164), (172, 333), (144, 376), (195, 336)], fill="#9a25fb")
        d.polygon([(229, 203), (229, 300), (315, 252)], fill="#070917")
        banner = Image.new("RGB", (640, 360), "#070917")
        banner.paste(icon.resize((290,290)), (6,35))
        from PIL import ImageFont
        d2 = ImageDraw.Draw(banner)
        d2.text((300,155), "PowerPlay", fill="#ecb9fb", font=ImageFont.load_default(size=52))
        print("WARNING: placeholder artwork; replace with approved logo before public release.")
    resources = ROOT / "android/app/src/main/res"
    def save(path, image):
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG", optimize=True)
    save(resources / "drawable-nodpi/powerplay_foreground.png", icon.resize((432, 432), Image.Resampling.LANCZOS))
    for pixels, density in [(48, "mdpi"), (72, "hdpi"), (96, "xhdpi"), (144, "xxhdpi"), (192, "xxxhdpi")]:
        save(resources / f"mipmap-{density}/ic_launcher.png", icon.resize((pixels, pixels), Image.Resampling.LANCZOS))
    for pixels, density in [(320, "xhdpi"), (480, "xxhdpi"), (640, "xxxhdpi")]:
        save(resources / f"drawable-{density}/tv_banner.png", banner.resize((pixels, pixels * 9 // 16), Image.Resampling.LANCZOS))
    save(ROOT / "assets/plezy.png", icon.resize((512, 512), Image.Resampling.LANCZOS))

    (ROOT / "POWERPLAY-RELEASE-NOTICE.md").write_text(
        "# PowerPlay — unofficial Plezy derivative\n\n"
        "Based on Plezy 2.25.0, licensed under GNU GPLv3. Upstream: https://github.com/edde746/plezy.\n"
        "This modified Fire TV edition uses the separate application ID com.power.powerplay, "
        "powerplay:// deep links, independent content provider authorities, and PowerPlay artwork.\n"
        "Original license and copyright notices are retained. This project is not affiliated "
        "with Plex, Plezy, or Amazon.\n", encoding="utf-8")
    print("PowerPlay identity and logo installed; Plezy platform-channel names retained.")

if __name__ == "__main__":
    main()
