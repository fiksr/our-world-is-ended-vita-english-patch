# Our World Is Ended — PS Vita (`PCSG01076`) English Backport Patch

Ports the official English localization from the PC (Steam) release of **Our World Is Ended** to the Japanese PS Vita release (**`PCSG01076`**).

## What Is Translated
- **Story, Routes, Endings & Choices:** `39,783 / 40,700` `.book` rows (`99.9%` of main story, character endings, and SP chapters; excluding Vita-exclusive `SceneGift.book`). Long English dialogue lines (`541` rows) are automatically split across pages so text does not clip at the bottom of the 3-line Vita textbox.
- **Location & Date/Time Banners:** All `411` `DatePlace` (`SendMessageByName`) location and timestamp banners.
- **Fonts:** Proportional ASCII spacing + added `,` and `"` glyphs across all 4 Vita `_BMP` bitmap fonts (`TT_NNewRodin-B_BMP`, `TT_NNewRodin-B_Outline_BMP`, `TT_NewCinemaA-D_BMP`, `TT_NewCinemaA-D_Outline_BMP`).
- **Config Menu UI:** English labels and button graphics on `BG00` (`SysConfigBg`) and `UI00` (`SysButtonConfig*`). (Title, Save/Load, Gallery, Backlog, and Confirm buttons were already English in `PCSG01076`.)
- **System Popups:** `23` IL2CPP `global-metadata.dat` strings (demo save prompt, save/load/overwrite/reset/title/skip confirmations, toast messages, date format).
- **In-Game Screens & Title Cards:**
  - `screenpc.asset`: `30 / 33` English forum/PC sprites
  - `info.asset`: `15 / 15` English info sprites
  - `EpTitle` / `EpTitle_2` / `EpTitle_3`: `27 / 27` English chapter & ending title cards

## Known Limitations / Untranslated Content
- **`SceneGift.book` (`891` lines):** Vita-exclusive bonus/gift scenario not present in the PC version (left in Japanese).
- **`screentv2.asset` (`5` sprites):** No English `_en` variants exist in the PC release.
- **Gallery CG Titles (`global-metadata.dat`):** Internal/Gallery CG title strings (`[3100..3220]`) remain in Japanese.
- **Vita3K `OP.mp4` Video Crash:** Vita3K's stubbed `SceAvPlayer` / `libscemp4` decoder can crash (`EXCEPTION_ACCESS_VIOLATION`) when playing `OP.mp4` (an untouched original video). Skip `OP.mp4` immediately or load the autosave (`data0098.bin`) in Vita3K; real PS Vita hardware decodes `OP.mp4` natively.
- **Real PS Vita Hardware:** Tested on Vita3K so far; real hardware testing via `rePatch` (`ux0:rePatch/PCSG01076/Media/...`) is still needed.

## Installation (Copy-Paste `rePatch` — Recommended)

Download either zip from the **[Releases](https://github.com/fiksr/our-world-is-ended-vita-english-patch/releases)** page:
- **`OWIE_Vita_English_Patch_v0.1_rePatch_Full.zip` (`185.5 MB`):** Everything translated, including the 27 English chapter & ending title cards (`EpTitle`).
- **`OWIE_Vita_English_Patch_v0.1_rePatch_Lite.zip` (`13.0 MB`):** Everything translated *except* the 27 chapter/ending title cards (those stay Japanese).

Then extract and copy the `PCSG01076` folder:
- **Real PS Vita (`rePatch`):** Copy `PCSG01076` into `ux0:rePatch/` (requires the `rePatch` plugin).
- **Vita3K:** Copy `PCSG01076` into `ux0/app/` and overwrite existing files.

---

## How to Build the Patch From Source

### Requirements
- Decrypted Japanese PS Vita copy of **Our World Is Ended (`PCSG01076`)**
- PC (Steam) copy of **Our World Is Ended**
- Python 3.10+ with dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Steps
1. Update the paths at the top of `patch_all.py`, `patch_ui.py`, `patch_metadata.py`, `patch_dicing.py`, and `patch_eptitle.py` if your Vita3K / Steam folders are in a non-default location, and copy your original Vita files into `backup/`:
   - `backup/sharedassets1.assets`
   - `backup/sharedassets1.assets.resS`
   - `backup/resources.assets`
   - `backup/global-metadata.dat`
   - `backup/PSP2/` (`Media/StreamingAssets/OREO/PSP2/*`)
2. Run the patch scripts in order:
   ```bash
   python patch_all.py
   python patch_ui.py
   python patch_metadata.py
   python patch_dicing.py
   python patch_eptitle.py
   ```
3. For **real PS Vita (`rePatch`)**, copy the modified `Media\` files into `ux0:rePatch/PCSG01076/Media/`.
