"""Port English EpTitle, EpTitle_2, EpTitle_3 DicingTextures from PC resources.assets to Vita resources.assets + .resS."""
import hashlib
import math
import os
import UnityPy
from UnityPy.enums import TextureFormat
from UnityPy.export import Texture2DConverter
from PIL import Image
from patch_dicing import decode_dicing_sprite, paste_cell_to_atlas

BACKUP_RES = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup\resources.assets"
VITA_RES = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\resources.assets"
VITA_RESS = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\resources.assets.resS"
PC_RES = r"C:\Program Files (x86)\Steam\steamapps\common\Our World Is Ended\OurWorldIsEnded_Data\resources.assets"
DICE_TT_AB = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup\PSP2\texture\sprite\screenpc.asset"
INSPECT_DIR = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\ui_inspect"


def tile_key(tile: Image.Image, quant_shift: int) -> bytes:
    if quant_shift == 0:
        return hashlib.md5(tile.tobytes()).digest()
    raw = tile.tobytes()
    q = bytes((b >> quant_shift) for b in raw)
    return hashlib.md5(q).digest()


def pack_single_atlas(
    tv: dict,
    tp: dict,
    pc_atlases: dict[str, Image.Image],
    pc_by_name: dict,
    atlas_name: str,
) -> tuple[Image.Image, int]:
    cs, pad = tv["cellSize"], tv["padding"]
    inner = cs - 2 * pad
    cap = (2048 // cs) * (2048 // cs)  # 1024

    # Try exact hash first (quant_shift=0), then gentle quantization if > 1023 unique tiles
    for qshift in (0, 3, 4, 5, 6, 7):
        atlas_img = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
        hashes = {}
        next_idx = 1
        overflow = False
        new_lists = []

        for td_v in tv["textureDataList"]:
            en_key = f"en/{td_v['name']}_en"
            td_p = pc_by_name[en_key]
            img = decode_dicing_sprite(td_p, pc_atlases, tp["cellSize"], tp["padding"])
            img = img.resize((td_v["width"], td_v["height"]), Image.Resampling.LANCZOS)

            nx = math.ceil(td_v["width"] / inner)
            ny = math.ceil(td_v["height"] / inner)
            canvas = Image.new("RGBA", (nx * inner, ny * inner), (0, 0, 0, 0))
            canvas.paste(img, (0, 0))

            indices = []
            for gy_idx in range(ny):
                gy = ny - 1 - gy_idx
                for gx in range(nx):
                    t = canvas.crop((gx * inner, gy * inner, (gx + 1) * inner, (gy + 1) * inner))
                    if t.getbbox() is None:
                        indices.append(0)
                        continue
                    h = tile_key(t, qshift)
                    if h in hashes:
                        indices.append(hashes[h])
                    else:
                        if next_idx >= cap:
                            overflow = True
                            break
                        cidx = next_idx
                        next_idx += 1
                        hashes[h] = cidx
                        paste_cell_to_atlas(t, atlas_img, cidx, cs, pad)
                        indices.append(cidx)
                if overflow:
                    break
            if overflow:
                break
            new_lists.append(indices)

        if not overflow:
            for td_v, indices in zip(tv["textureDataList"], new_lists):
                td_v["atlasName"] = atlas_name
                td_v["transparentIndex"] = 0
                td_v["cellIndexList"] = indices
            return atlas_img, next_idx

    raise RuntimeError(f"Could not fit {atlas_name} within {cap} cells")


def main():
    env_tt = UnityPy.load(DICE_TT_AB)
    dicing_nodes = next(
        o.serialized_type.nodes
        for o in env_tt.objects
        if o.type.name == "MonoBehaviour" and o.peek_name() == "ScreenPc"
    )
    env_p = UnityPy.load(PC_RES)
    env_v = UnityPy.load(BACKUP_RES)

    # Read Texture2D stream offsets in Vita resources.assets
    tex_streams = {}
    for o in env_v.objects:
        if o.type.name == "Texture2D" and o.peek_name() in ("EpTitle_Atlas0", "EpTitle_2_Atlas0", "EpTitle_3_Atlas0"):
            d = o.read()
            tex_streams[d.m_Name] = (d.m_StreamData.offset, d.m_StreamData.size)

    with open(VITA_RESS, "r+b") as f_ress:
        for mname, atlas_name in (
            ("EpTitle", "EpTitle_Atlas0"),
            ("EpTitle_2", "EpTitle_2_Atlas0"),
            ("EpTitle_3", "EpTitle_3_Atlas0"),
        ):
            pc_atlases = {
                o.peek_name(): o.read().image
                for o in env_p.objects
                if o.type.name == "Texture2D" and o.peek_name().startswith(mname + "_Atlas")
            }
            tp = next(
                o.read_typetree(dicing_nodes)
                for o in env_p.objects
                if o.type.name == "MonoBehaviour" and o.peek_name() == mname
            )
            pc_by_name = {td["name"]: td for td in tp["textureDataList"]}

            v_obj = next(
                o for o in env_v.objects if o.type.name == "MonoBehaviour" and o.peek_name() == mname
            )
            tv = v_obj.read_typetree(dicing_nodes)

            atlas_img, used = pack_single_atlas(tv, tp, pc_atlases, pc_by_name, atlas_name)
            v_obj.save_typetree(tv, dicing_nodes)

            raw, fmt = Texture2DConverter.image_to_texture2d(atlas_img, TextureFormat.DXT5, flip=True)
            off, sz = tex_streams[atlas_name]
            if len(raw) != sz:
                raise ValueError(f"{atlas_name}: expected {sz}, got {len(raw)}")
            f_ress.seek(off)
            f_ress.write(raw)
            print(f"{mname}: ported {len(tv['textureDataList'])} English title cards ({used}/1024 cells) -> {atlas_name} at {off}")

    with open(VITA_RES, "wb") as f:
        f.write(env_v.file.save())
    print(f"Saved {VITA_RES}")


if __name__ == "__main__":
    main()
