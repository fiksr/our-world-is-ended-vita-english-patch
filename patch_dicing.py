"""Port English DicingTextures (ScreenPc, Info) from PC resources.assets to Vita AssetBundles.
Re-packs all tiles cleanly with per-atlas deduplication and updates cellIndexList via TypeTree.
"""
import hashlib
import math
import os
import UnityPy
from PIL import Image

BACKUP_SPRITE_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup\PSP2\texture\sprite"
VITA_SPRITE_DIR = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\StreamingAssets\OREO\PSP2\texture\sprite"
PC_RES = r"C:\Program Files (x86)\Steam\steamapps\common\Our World Is Ended\OurWorldIsEnded_Data\resources.assets"
INSPECT_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\ui_inspect"


def decode_dicing_sprite(td: dict, atlases: dict[str, Image.Image], cs: int, pad: int) -> Image.Image:
    atlas = atlases[td["atlasName"]]
    inner = cs - 2 * pad
    w, h = td["width"], td["height"]
    nx = math.ceil(w / inner)
    ny = math.ceil(h / inner)
    acols = atlas.width // cs
    out = Image.new("RGBA", (nx * inner, ny * inner), (0, 0, 0, 0))
    for i, cidx in enumerate(td["cellIndexList"]):
        if cidx == td["transparentIndex"] or cidx < 0:
            continue
        gx = i % nx
        gy = ny - 1 - (i // nx)
        ax = (cidx % acols) * cs
        ay = atlas.height - ((cidx // acols) + 1) * cs
        tile = atlas.crop((ax + pad, ay + pad, ax + cs - pad, ay + cs - pad))
        out.paste(tile, (gx * inner, gy * inner))
    return out.crop((0, 0, w, h))


def paste_cell_to_atlas(tile_inner: Image.Image, atlas: Image.Image, cidx: int, cs: int, pad: int):
    inner = cs - 2 * pad
    acols = atlas.width // cs
    cell = Image.new("RGBA", (cs, cs), (0, 0, 0, 0))
    cell.paste(tile_inner, (pad, pad))
    top_row = tile_inner.crop((0, 0, inner, 1))
    bot_row = tile_inner.crop((0, inner - 1, inner, inner))
    for p in range(pad):
        cell.paste(top_row, (pad, p))
        cell.paste(bot_row, (pad, pad + inner + p))
    left_col = cell.crop((pad, 0, pad + 1, cs))
    right_col = cell.crop((pad + inner - 1, 0, pad + inner, cs))
    for p in range(pad):
        cell.paste(left_col, (p, 0))
        cell.paste(right_col, (pad + inner + p, 0))
    ax = (cidx % acols) * cs
    ay = atlas.height - ((cidx // acols) + 1) * cs
    atlas.paste(cell, (ax, ay))


def repack_dicing_bundle(env_v, mono_name: str, pc_tt: dict, pc_atlases: dict[str, Image.Image], pc_by_name: dict):
    v_tex_objs = {}
    v_atlases_orig = {}
    v_mono_obj = None
    v_tt = None
    for o in env_v.objects:
        if o.type.name == "Texture2D":
            d = o.read()
            v_tex_objs[d.m_Name] = d
            v_atlases_orig[d.m_Name] = d.image
        elif o.type.name == "MonoBehaviour" and o.peek_name() == mono_name:
            v_mono_obj = o
            v_tt = o.read_typetree()

    cs, pad = v_tt["cellSize"], v_tt["padding"]
    inner = cs - 2 * pad
    atlas_names = sorted(v_tex_objs.keys())
    cap_per_atlas = (2048 // cs) * (2048 // cs)  # 1024

    # Prepare fresh atlases; reserve cell 0 as transparentIndex
    new_atlases = {an: Image.new("RGBA", (2048, 2048), (0, 0, 0, 0)) for an in atlas_names}
    atlas_state = {an: {"next_idx": 1, "hashes": {}} for an in atlas_names}

    replaced = 0
    for td_v in v_tt["textureDataList"]:
        en_key = f"en/{td_v['name']}_en"
        if en_key in pc_by_name:
            img = decode_dicing_sprite(pc_by_name[en_key], pc_atlases, pc_tt["cellSize"], pc_tt["padding"])
            img = img.resize((td_v["width"], td_v["height"]), Image.Resampling.LANCZOS)
            replaced += 1
        else:
            img = decode_dicing_sprite(td_v, v_atlases_orig, cs, pad)

        nx = math.ceil(td_v["width"] / inner)
        ny = math.ceil(td_v["height"] / inner)
        canvas = Image.new("RGBA", (nx * inner, ny * inner), (0, 0, 0, 0))
        canvas.paste(img, (0, 0))

        # Slice tiles in Unity cellIndexList order (bottom-to-top rows, left-to-right)
        tiles = []
        for gy_idx in range(ny):
            gy = ny - 1 - gy_idx
            for gx in range(nx):
                t = canvas.crop((gx * inner, gy * inner, (gx + 1) * inner, (gy + 1) * inner))
                if t.getbbox() is None:
                    tiles.append((None, None))
                else:
                    tiles.append((t, hashlib.md5(t.tobytes()).digest()))

        # Pick first atlas that can fit this sprite's new unique tiles
        chosen = None
        for an in atlas_names:
            st = atlas_state[an]
            new_unique = {h for t, h in tiles if h is not None and h not in st["hashes"]}
            if st["next_idx"] + len(new_unique) <= cap_per_atlas:
                chosen = an
                break
        if chosen is None:
            raise RuntimeError(f"Not enough atlas space for {td_v['name']} in {mono_name}")

        st = atlas_state[chosen]
        atlas_img = new_atlases[chosen]
        new_indices = []
        for t, h in tiles:
            if h is None:
                new_indices.append(0)
            elif h in st["hashes"]:
                new_indices.append(st["hashes"][h])
            else:
                cidx = st["next_idx"]
                st["next_idx"] += 1
                st["hashes"][h] = cidx
                paste_cell_to_atlas(t, atlas_img, cidx, cs, pad)
                new_indices.append(cidx)

        td_v["atlasName"] = chosen
        td_v["transparentIndex"] = 0
        td_v["cellIndexList"] = new_indices

    v_mono_obj.save_typetree(v_tt)
    for an, d in v_tex_objs.items():
        d.image = new_atlases[an]
        d.save()
        print(f"  {an}: used {atlas_state[an]['next_idx']}/{cap_per_atlas} cells")
    return replaced, len(v_tt["textureDataList"])


def main():
    env_tt = UnityPy.load(os.path.join(BACKUP_SPRITE_DIR, "screenpc.asset"))
    dicing_nodes = next(
        o.serialized_type.nodes
        for o in env_tt.objects
        if o.type.name == "MonoBehaviour" and o.peek_name() == "ScreenPc"
    )
    env_p = UnityPy.load(PC_RES)

    for ab_name, mono_name, atlas_prefix in (
        ("screenpc.asset", "ScreenPc", "ScreenPc_Atlas"),
        ("info.asset", "Info", "Info_Atlas"),
    ):
        pc_atlases = {}
        pc_tt = None
        for o in env_p.objects:
            if o.type.name == "Texture2D" and o.peek_name().startswith(atlas_prefix):
                d = o.read()
                pc_atlases[d.m_Name] = d.image
            elif o.type.name == "MonoBehaviour" and o.peek_name() == mono_name:
                pc_tt = o.read_typetree(dicing_nodes)

        pc_by_name = {td["name"]: td for td in pc_tt["textureDataList"]}
        env_v = UnityPy.load(os.path.join(BACKUP_SPRITE_DIR, ab_name))
        rep, tot = repack_dicing_bundle(env_v, mono_name, pc_tt, pc_atlases, pc_by_name)
        out_path = os.path.join(VITA_SPRITE_DIR, ab_name)
        with open(out_path, "wb") as f:
            f.write(env_v.file.save())
        print(f"{ab_name}: repacked {rep}/{tot} English sprites -> {out_path}")

    # Round-trip decode PcScreen_01 from saved Vita screenpc.asset for visual verification
    env_chk = UnityPy.load(os.path.join(VITA_SPRITE_DIR, "screenpc.asset"))
    chk_atlases = {o.peek_name(): o.read().image for o in env_chk.objects if o.type.name == "Texture2D"}
    chk_tt = next(o.read_typetree() for o in env_chk.objects if o.type.name == "MonoBehaviour" and o.peek_name() == "ScreenPc")
    td0 = next(x for x in chk_tt["textureDataList"] if x["name"] == "PcScreen_01")
    decode_dicing_sprite(td0, chk_atlases, chk_tt["cellSize"], chk_tt["padding"]).save(
        os.path.join(INSPECT_DIR, "Vita_PcScreen_01_verify.png")
    )
    print("Saved Vita_PcScreen_01_verify.png")


if __name__ == "__main__":
    main()
