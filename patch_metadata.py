"""Patch IL2CPP global-metadata.dat system popups and UI strings for PCSG01076."""
import os
import struct

BACKUP_META = r"C:\Users\Nikola\Desktop\AI PROJECTS\OurWorldIsEnded\backup\global-metadata.dat"
OUT_META = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01076\Media\Metadata\global-metadata.dat"

# Exact stringLiteral index -> English replacement (UTF-8 byte length <= original)
REPLACEMENTS = {
    1907: "H':'m':'s",
    1910: "yyyy'/'M'/'d",
    2989: "No Quick Save data found.",
    3013: "Quick Load complete.",
    3398: "Quick Save complete.",
    3399: "Game saved.",
    3405: "Auto save data is corrupted.",
    3406: "Quick save data is corrupted.",
    3407: "System save data is corrupted.",
    3408: "Slot {0} save data is corrupted.",
    3416: "Our World Is Ended.",
    3417: "Save Data",
    3418: "System Data",
    3419: "System Save Data",
    3459: "Skip to the next choice or chapter?\\n(Unread text will not be skipped.)",
    3849: "Exit Gallery and return to the title screen?",
    3853: "Demo save data found.\nTransfer save data?",
    3854: "Return to the title screen?\\nAre you sure?",
    3855: "Reset config settings to default?\\nAre you sure?",
    3856: "Load this save data?\\nAny unsaved progress will be lost.",
    3859: "Save game data?\\nAre you sure?",
    3860: "Overwrite this save data?\\nAre you sure?",
    3862: "Save data loaded.",
}


def main():
    with open(BACKUP_META, "rb") as f:
        data = bytearray(f.read())

    sl_off, sl_size, sld_off, sld_size = struct.unpack_from("<IIII", data, 8)
    patched = 0
    for idx, en in REPLACEMENTS.items():
        orig_len, doff = struct.unpack_from("<II", data, sl_off + idx * 8)
        en_bytes = en.encode("utf-8")
        if len(en_bytes) > orig_len:
            raise ValueError(f"Index {idx} too long: {len(en_bytes)} > {orig_len}")
        pos = sld_off + doff
        data[pos : pos + orig_len] = en_bytes + b"\x00" * (orig_len - len(en_bytes))
        struct.pack_into("<I", data, sl_off + idx * 8, len(en_bytes))
        patched += 1

    with open(OUT_META, "wb") as f:
        f.write(data)
    print(f"Patched {patched} system strings in {OUT_META}")


if __name__ == "__main__":
    main()
