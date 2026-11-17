"""Phase 1 Proof-of-Concept patcher for Our World Is Ended (PCSG01076).
Tests:
1. Transplanting English text from PC Scene00.book into Vita Scene00.book
   (both sharedassets1.assets and StreamingAssets/OREO/PSP2/scene00.chapter.asset).
2. Setting proportional advance widths on ASCII glyphs in Vita's 4 _BMP Font assets.
"""
import os
import re
import UnityPy

VITA_MEDIA = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media"
BACKUP_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup"
PC_SA1 = r"C:\Program Files (x86)\Steam\steamapps\common\Our World Is Ended\OurWorldIsEnded_Data\sharedassets1.assets"


def sanitize_en(text: str) -> str:
    # Normalize characters missing from Vita's _BMP fonts for PoC
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("—", "―")
    text = text.replace('"', '”')  # temporary until we draw ASCII '"' & ','
    text = text.replace(",", "，")  # temporary fullwidth comma check
    return text


def load_book_nodes():
    ab_path = os.path.join(BACKUP_DIR, "PSP2", "scene00.chapter.asset")
    env_ab = UnityPy.load(ab_path)
    for obj in env_ab.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name() == "Scene00.book":
            return obj.serialized_type.nodes
    raise RuntimeError("Could not find Scene00.book TypeTree")


def extract_pc_translations(book_nodes, book_name: str) -> dict[str, str]:
    env_p = UnityPy.load(PC_SA1)
    for obj in env_p.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name() == book_name:
            tt = obj.read_typetree(book_nodes)
            mapping = {}
            for grid in tt["importGridList"]:
                rows = grid.get("rows", [])
                if not rows:
                    continue
                header = rows[0]["strings"]
                if "Text" not in header or "English" not in header:
                    continue
                idx_jp = header.index("Text")
                idx_en = header.index("English")
                for row in rows[1:]:
                    s = row["strings"]
                    if len(s) > max(idx_jp, idx_en) and s[idx_jp] and s[idx_en]:
                        mapping[s[idx_jp]] = sanitize_en(s[idx_en])
            return mapping
    raise RuntimeError(f"PC {book_name} not found")


def patch_book_tt(tt: dict, jp_to_en: dict[str, str]) -> tuple[int, int]:
    patched = 0
    total = 0
    for grid in tt["importGridList"]:
        rows = grid.get("rows", [])
        if not rows:
            continue
        header = rows[0]["strings"]
        if "Text" not in header:
            continue
        idx_jp = header.index("Text")
        for row in rows[1:]:
            s = row["strings"]
            if len(s) > idx_jp and s[idx_jp]:
                total += 1
                en = jp_to_en.get(s[idx_jp])
                if en:
                    s[idx_jp] = en
                    patched += 1
    return patched, total


def main():
    book_nodes = load_book_nodes()
    jp_to_en = extract_pc_translations(book_nodes, "Scene00.book")
    print(f"Loaded {len(jp_to_en)} JP->EN rows from PC Scene00.book")

    # 1. Patch sharedassets1.assets (Scene00.book + Font proportional advance)
    env_sa1 = UnityPy.load(os.path.join(BACKUP_DIR, "sharedassets1.assets"))
    for obj in env_sa1.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name() == "Scene00.book":
            tt = obj.read_typetree(book_nodes)
            patched, total = patch_book_tt(tt, jp_to_en)
            obj.save_typetree(tt, book_nodes)
            print(f"sharedassets1 Scene00.book: patched {patched}/{total} text rows")
        elif obj.type.name == "Font" and "_BMP" in obj.peek_name():
            d = obj.read()
            changed = 0
            for r in d.m_CharacterRects:
                if r.index == 32:
                    r.advance = 8.0
                    changed += 1
                elif 33 <= r.index <= 126:
                    r.advance = float(max(6, min(18, round(r.vert.width) + 2)))
                    changed += 1
            d.save()
            print(f"Font {d.m_Name}: updated {changed} ASCII advance widths")

    out_sa1 = os.path.join(VITA_MEDIA, "sharedassets1.assets")
    with open(out_sa1, "wb") as f:
        f.write(env_sa1.file.save())
    print(f"Wrote {out_sa1} ({os.path.getsize(out_sa1)} bytes)")

    # 2. Patch StreamingAssets/OREO/PSP2/scene00.chapter.asset
    env_ab = UnityPy.load(os.path.join(BACKUP_DIR, "PSP2", "scene00.chapter.asset"))
    for obj in env_ab.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name() == "Scene00.book":
            tt = obj.read_typetree(book_nodes)
            patched, total = patch_book_tt(tt, jp_to_en)
            obj.save_typetree(tt)
            print(f"scene00.chapter.asset Scene00.book: patched {patched}/{total} text rows")
    out_ab = os.path.join(VITA_MEDIA, "StreamingAssets", "OREO", "PSP2", "scene00.chapter.asset")
    with open(out_ab, "wb") as f:
        f.write(env_ab.file.save())
    print(f"Wrote {out_ab} ({os.path.getsize(out_ab)} bytes)")


if __name__ == "__main__":
    main()
