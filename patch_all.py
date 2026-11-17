"""Phase 2 Full Script & Font Patcher for Our World Is Ended (PCSG01076).
1. Patches all 4 _BMP Font assets in sharedassets1.assets:
   - Proportional ASCII advance + clean vert.x bearing
   - Adds ASCII ',' (44) from "'" (39) shifted to baseline
   - Adds ASCII '"' (34) from '”' (8221)
2. Extracts all JP->EN mappings from PC sharedassets1.assets (*.book).
3. Patches all 41 Vita .book MonoBehaviours in sharedassets1.assets AND
   all corresponding StreamingAssets/OREO/PSP2/*.chapter.asset bundles,
   auto-splitting any >3-line dialogue so nothing overflows the textbox.
"""
import copy
import glob
import os
import re
import UnityPy

VITA_MEDIA = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media"
BACKUP_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup"
PC_SA1 = r"C:\Program Files (x86)\Steam\steamapps\common\Our World Is Ended\OurWorldIsEnded_Data\sharedassets1.assets"

MAX_LINE_PX = 680.0
MAX_LINES = 3


def sanitize_en(text: str) -> str:
    return (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("—", "―")
        .replace("\u00a0", " ")
    )


def load_book_nodes():
    ab_path = os.path.join(BACKUP_DIR, "PSP2", "scene00.chapter.asset")
    env_ab = UnityPy.load(ab_path)
    for obj in env_ab.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name() == "Scene00.book":
            return obj.serialized_type.nodes
    raise RuntimeError("Could not find Scene00.book TypeTree")


def extract_all_pc_translations(book_nodes):
    env_p = UnityPy.load(PC_SA1)
    per_book = {}
    global_map = {}
    norm_map = {}
    dateplace_map = {}
    for obj in env_p.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name().endswith(".book"):
            name = obj.peek_name()
            tt = obj.read_typetree(book_nodes)
            bmap = {}
            for grid in tt["importGridList"]:
                rows = grid.get("rows", [])
                if not rows:
                    continue
                hdr = rows[0]["strings"]
                if "Text" in hdr and "English" in hdr:
                    ij, ie = hdr.index("Text"), hdr.index("English")
                    for row in rows[1:]:
                        s = row["strings"]
                        if len(s) > max(ij, ie) and s[ij] and s[ie]:
                            en = sanitize_en(s[ie])
                            bmap[s[ij]] = en
                            global_map.setdefault(s[ij], en)
                            norm_map.setdefault(re.sub(r"\s+", "", s[ij]), en)
                if "Arg3" in hdr and "Arg5" in hdr and "Arg6" in hdr:
                    for row in rows[1:]:
                        s = row["strings"]
                        if len(s) >= 7 and s[0] == "SendMessageByName" and s[1] == "DatePlace":
                            if s[3] and s[5]:
                                dateplace_map.setdefault(s[3], sanitize_en(s[5]))
                            if s[4] and s[6]:
                                dateplace_map.setdefault(s[4], sanitize_en(s[6]))
            per_book[name] = bmap
    return per_book, global_map, norm_map, dateplace_map


def patch_fonts_and_get_widths(env_sa1) -> dict[int, float]:
    widths: dict[int, float] = {}
    for obj in env_sa1.objects:
        if obj.type.name == "Font" and "_BMP" in obj.peek_name():
            d = obj.read()
            is_outline = "_Outline" in d.m_Name
            rects = d.m_CharacterRects
            by_idx = {r.index: r for r in rects}

            for r in rects:
                if r.index == 32:
                    r.advance = 6.5
                elif 33 <= r.index <= 126:
                    w = r.vert.width - (4.0 if is_outline else 0.0)
                    r.vert.x = -1.0 if is_outline else 1.0
                    r.advance = float(min(15, max(4, round(w) + 1)))
                elif r.index in (8220, 8221):  # “ ”
                    r.advance = 12.0

            # Add ',' (44) cloned from "'" (39) shifted down to baseline
            if 44 not in by_idx and 39 in by_idx:
                c_rect = copy.deepcopy(by_idx[39])
                c_rect.index = 44
                c_rect.vert.x = -1.0 if is_outline else 1.0
                c_rect.vert.y = 10.0 if is_outline else 8.0
                c_rect.advance = 7.0
                rects.append(c_rect)
                by_idx[44] = c_rect

            # Add '"' (34) cloned from '”' (8221)
            if 34 not in by_idx and 8221 in by_idx:
                q_rect = copy.deepcopy(by_idx[8221])
                q_rect.index = 34
                q_rect.vert.x = -1.0 if is_outline else 1.0
                q_rect.advance = 12.0
                rects.append(q_rect)
                by_idx[34] = q_rect

            d.save()
            if d.m_Name == "TT_NNewRodin-B_BMP":
                widths = {r.index: r.advance for r in rects}
            print(f"Font {d.m_Name}: total glyphs={len(rects)} (added , and \")")
    return widths


def estimate_lines(text: str, widths: dict[int, float]) -> int:
    lines = 0
    for para in text.replace("\r\n", "\n").split("\n"):
        if not para:
            lines += 1
            continue
        cur = 0.0
        para_lines = 1
        for word in para.split(" "):
            w_px = sum(widths.get(ord(ch), 16.0) for ch in word)
            sp_px = widths.get(32, 6.5)
            if cur == 0.0:
                cur = w_px
            elif cur + sp_px + w_px <= MAX_LINE_PX:
                cur += sp_px + w_px
            else:
                para_lines += 1
                cur = w_px
        lines += para_lines
    return lines


def split_long_dialogue(text: str, widths: dict[int, float]) -> list[str]:
    if estimate_lines(text, widths) <= MAX_LINES:
        return [text]
    words = text.replace("\r\n", " ").replace("\n", " ").split(" ")
    mid = len(words) // 2
    # Prefer splitting at sentence end (. ! ?) near the middle
    best = None
    best_dist = 10**9
    for i in range(max(2, mid - 12), min(len(words) - 1, mid + 12)):
        if words[i - 1].endswith((".", "!", "?", '."', '!"', '?"', "…")):
            dist = abs(i - mid)
            if dist < best_dist:
                best_dist = dist
                best = i
    if best is None:
        best = mid
    p1 = " ".join(words[:best]).strip()
    p2 = " ".join(words[best:]).strip()
    if not p1 or not p2:
        return [text]
    return [p1, p2]


def patch_book_tt(tt: dict, bmap: dict[str, str], gmap: dict[str, str], nmap: dict[str, str], dpmap: dict[str, str], widths: dict[int, float]):
    patched = 0
    total = 0
    split_count = 0
    dp_patched = 0
    for grid in tt["importGridList"]:
        rows = grid.get("rows", [])
        if not rows:
            continue
        hdr = rows[0]["strings"]
        if "Text" not in hdr:
            continue
        ij = hdr.index("Text")
        iv = hdr.index("Voice") if "Voice" in hdr else -1

        new_rows = [rows[0]]
        for row in rows[1:]:
            s = row["strings"]
            if len(s) >= 5 and s[0] == "SendMessageByName" and s[1] == "DatePlace":
                if s[3] in dpmap:
                    s[3] = dpmap[s[3]]
                    dp_patched += 1
                if s[4] in dpmap:
                    s[4] = dpmap[s[4]]
                    dp_patched += 1
            if len(s) > ij and s[ij]:
                total += 1
                en = bmap.get(s[ij]) or gmap.get(s[ij]) or nmap.get(re.sub(r"\s+", "", s[ij]))
                if en:
                    patched += 1
                    cmd = s[0] if s else ""
                    if cmd == "":
                        parts = split_long_dialogue(en, widths)
                    else:
                        parts = [en]
                    if len(parts) > 1:
                        split_count += 1
                        r1 = copy.deepcopy(row)
                        r1["strings"][ij] = parts[0]
                        r2 = copy.deepcopy(row)
                        r2["strings"][ij] = parts[1]
                        if iv >= 0 and len(r2["strings"]) > iv:
                            r2["strings"][iv] = ""
                        new_rows.append(r1)
                        new_rows.append(r2)
                        continue
                    s[ij] = parts[0]
            new_rows.append(row)

        if len(new_rows) != len(rows):
            for idx, r in enumerate(new_rows):
                r["rowIndex"] = idx
            grid["rows"] = new_rows
    return patched, total, split_count, dp_patched


def main():
    book_nodes = load_book_nodes()
    per_book, global_map, norm_map, dateplace_map = extract_all_pc_translations(book_nodes)
    print(f"Loaded {len(per_book)} PC books, {len(global_map)} JP->EN lines, {len(dateplace_map)} DatePlace entries")

    # 1. Patch sharedassets1.assets
    env_sa1 = UnityPy.load(os.path.join(BACKUP_DIR, "sharedassets1.assets"))
    widths = patch_fonts_and_get_widths(env_sa1)

    sa1_patched = 0
    sa1_total = 0
    sa1_splits = 0
    sa1_dp = 0
    for obj in env_sa1.objects:
        if obj.type.name == "MonoBehaviour" and obj.peek_name().endswith(".book"):
            name = obj.peek_name()
            tt = obj.read_typetree(book_nodes)
            p, t, sp, dp = patch_book_tt(tt, per_book.get(name, {}), global_map, norm_map, dateplace_map, widths)
            obj.save_typetree(tt, book_nodes)
            sa1_patched += p
            sa1_total += t
            sa1_splits += sp
            sa1_dp += dp

    out_sa1 = os.path.join(VITA_MEDIA, "sharedassets1.assets")
    with open(out_sa1, "wb") as f:
        f.write(env_sa1.file.save())
    print(f"sharedassets1.assets: patched {sa1_patched}/{sa1_total} rows ({sa1_splits} split, {sa1_dp} DatePlace) -> {out_sa1}")

    # 2. Patch all StreamingAssets/OREO/PSP2/*.chapter.asset bundles
    ab_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "PSP2", "*.chapter.asset")))
    ab_patched_files = 0
    for ab_path in ab_files:
        env_ab = UnityPy.load(ab_path)
        modified = False
        for obj in env_ab.objects:
            if obj.type.name == "MonoBehaviour" and obj.peek_name().endswith(".book"):
                name = obj.peek_name()
                tt = obj.read_typetree(book_nodes)
                p, t, sp, dp = patch_book_tt(tt, per_book.get(name, {}), global_map, norm_map, dateplace_map, widths)
                if p > 0 or dp > 0:
                    obj.save_typetree(tt)
                    modified = True
        if modified:
            out_ab = os.path.join(VITA_MEDIA, "StreamingAssets", "OREO", "PSP2", os.path.basename(ab_path))
            with open(out_ab, "wb") as f:
                f.write(env_ab.file.save())
            ab_patched_files += 1

    print(f"StreamingAssets/OREO/PSP2: patched {ab_patched_files} .chapter.asset bundles")


if __name__ == "__main__":
    main()
