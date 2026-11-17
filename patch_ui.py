"""Patch Japanese Config UI sprites in BG00 and UI00 directly in sharedassets1.assets.resS for PCSG01076."""
import os
import shutil
import UnityPy
from UnityPy.enums import TextureFormat
from UnityPy.export import Texture2DConverter
from PIL import Image, ImageDraw, ImageFont

MEDIA_SA1 = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\sharedassets1.assets"
BACKUP_RESS = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup\sharedassets1.assets.resS"
MEDIA_RESS = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\sharedassets1.assets.resS"
INSPECT_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\ui_inspect"


def get_font(size: int):
    for p in (
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def patch_bg00(bg: Image.Image) -> Image.Image:
    bg = bg.copy()
    # SysConfigBg is at Unity (4, 396, 960, 544) -> PIL top = 2048 - (396 + 544) = 1108
    sx, sy = 4, 2048 - (396 + 544)
    crop = bg.crop((sx, sy, sx + 960, sy + 544))
    draw = ImageDraw.Draw(crop)
    font = get_font(14)

    # Left strips: x=352..496 + dark border sliver at 496..512 (clean border at y=260..280)
    left_labels = [
        (136, 156, "Text Speed"),
        (196, 216, "Auto Speed"),
        (436, 456, "Opacity"),
    ]
    border_clean = crop.crop((496, 260, 512, 280))
    for y0, y1, text in left_labels:
        strip_col = crop.crop((352, y0, 353, y1))
        for xx in range(352, 496):
            crop.paste(strip_col, (xx, y0))
        crop.paste(border_clean, (496, y0))
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = 352 + (144 - tw) // 2
        ty = y0 + (20 - th) // 2 - 2
        draw.text((tx, ty), text, font=font, fill=(60, 55, 45, 255))

    # Right strips: x=548..620, sample clean vertical slice at x=550
    right_labels = [
        (136, 156, "Master", font),
        (316, 336, "Ambience", get_font(12)),
        (376, 396, "Voice", font),
    ]
    for y0, y1, text, rf in right_labels:
        strip_col = crop.crop((550, y0, 551, y1))
        for xx in range(550, 620):
            crop.paste(strip_col, (xx, y0))
        bbox = draw.textbbox((0, 0), text, font=rf)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = 617 - tw
        ty = y0 + (20 - th) // 2 - 2
        draw.text((tx, ty), text, font=rf, fill=(60, 55, 45, 255))

    crop.save(os.path.join(INSPECT_DIR, "SysConfigBg_patched.png"))
    bg.paste(crop, (sx, sy))
    return bg


def patch_ui00(ui: Image.Image) -> Image.Image:
    ui = ui.copy()
    draw = ImageDraw.Draw(ui)
    font = get_font(16)

    # (name, unity_x, unity_y, w, h, left_pad, right_pad, text)
    buttons = [
        ("SysButtonConfigBackTitle", 1684, 1028, 184, 44, 6, 14, "Return to Title"),
        ("SysButtonConfigBackTitleOn", 4, 5, 184, 44, 6, 14, "Return to Title"),
        ("SysButtonConfigBtConfigReset", 682, 865, 184, 44, 6, 14, "Reset Defaults"),
        ("SysButtonConfigBtConfigResetOn", 420, 544, 184, 44, 6, 14, "Reset Defaults"),
        ("SysButtonConfigMidokuSkipOff", 430, 898, 244, 44, 41, 16, "Skip Unread"),
        ("SysButtonConfigMidokuSkipOn", 972, 1004, 244, 44, 41, 16, "Skip Unread"),
        ("SysButtonConfigSentakStopOff", 430, 846, 244, 44, 41, 16, "Stop at Choices"),
        ("SysButtonConfigSentakStopOn", 4, 413, 244, 44, 41, 16, "Stop at Choices"),
        ("SysButtonConfigVoiceEndOff", 430, 950, 244, 44, 41, 16, "Play Full Voice"),
        ("SysButtonConfigVoiceEndOn", 4, 361, 244, 44, 41, 16, "Play Full Voice"),
    ]

    preview = Image.new("RGBA", (300, len(buttons) * 50), (40, 40, 40, 255))
    for idx, (name, ux, uy, w, h, lpad, rpad, text) in enumerate(buttons):
        top = 2048 - (uy + h)
        # Copy clean vertical slice from (ux + w - rpad - 2) to cover text area
        sample_x = ux + w - rpad - 2
        col = ui.crop((sample_x, top + 5, sample_x + 1, top + h - 5))
        for xx in range(ux + lpad, ux + w - rpad):
            ui.paste(col, (xx, top + 5))

        is_on = name.endswith("On") and "BackTitle" not in name and "Reset" not in name
        fg = (195, 165, 25, 255) if is_on else (75, 70, 58, 255)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        area_w = (w - rpad) - lpad
        tx = ux + lpad + (area_w - tw) // 2
        ty = top + (h - th) // 2 - 2
        draw.text((tx, ty), text, font=font, fill=fg)

        cropped_btn = ui.crop((ux, top, ux + w, top + h))
        preview.paste(cropped_btn, (10, idx * 50 + 3), cropped_btn)

    preview.save(os.path.join(INSPECT_DIR, "ui_buttons_patched.png"))
    return ui


def main():
    shutil.copy2(BACKUP_RESS, MEDIA_RESS)
    env = UnityPy.load(MEDIA_SA1)
    targets = {}
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            name = obj.peek_name()
            if name in ("BG00", "UI00"):
                d = obj.read()
                targets[name] = (d.m_StreamData.offset, d.m_StreamData.size)

    with open(MEDIA_RESS, "r+b") as f:
        for name, patch_fn in (("BG00", patch_bg00), ("UI00", patch_ui00)):
            off, sz = targets[name]
            clean_img = Image.open(os.path.join(INSPECT_DIR, f"{name}.png"))
            patched_img = patch_fn(clean_img)
            raw, fmt = Texture2DConverter.image_to_texture2d(patched_img, TextureFormat.DXT5, flip=True)
            if len(raw) != sz:
                raise ValueError(f"{name}: expected {sz} bytes, got {len(raw)}")
            f.seek(off)
            f.write(raw)
            print(f"Patched {name} in-place in {MEDIA_RESS} at offset {off} ({sz} bytes)")


if __name__ == "__main__":
    main()
