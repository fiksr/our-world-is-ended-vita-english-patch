[b]Our World Is Ended (PCSG01076) — PS Vita English Backport Patch (v0.1-beta)[/b]

Ports the official English localization from the PC (Steam) release to the Japanese PS Vita version ([b]PCSG01076[/b]).

[b]Download (Copy-Paste rePatch Zips):[/b]
https://github.com/fiksr/our-world-is-ended-vita-english-patch/releases

[list]
[*][b]Full (`185.5 MB`):[/b] `OWIE_Vita_English_Patch_v0.1_rePatch_Full.zip` — Everything translated, including the 27 English chapter & ending title cards.
[*][b]Lite (`13.0 MB`):[/b] `OWIE_Vita_English_Patch_v0.1_rePatch_Lite.zip` — Everything translated except the 27 chapter/ending title cards (which remain Japanese).
[/list]

[b]Installation:[/b]
[list]
[*][b]Real PS Vita:[/b] Extract and copy the [code]PCSG01076[/code] folder into [code]ux0:rePatch/[/code] (requires rePatch plugin).
[*][b]Vita3K:[/b] Extract and copy the [code]PCSG01076[/code] folder into [code]ux0/app/[/code] and overwrite.
[/list]

[b]What's Translated:[/b]
[list]
[*][b]Main Story, Routes, Endings & Choices:[/b] 39,783 / 40,700 rows (99.9% of non-Vita-exclusive content), with 541 long lines auto-split across pages so text doesn't clip at the bottom of the 3-line textbox.
[*][b]Location & Date/Time Banners:[/b] All 411 [code]DatePlace[/code] banners translated.
[*][b]Proportional Fonts & Punctuation:[/b] Updated ASCII spacing and added missing [code],[/code] and [code]"[/code] glyphs to all 4 Vita bitmap fonts.
[*][b]Config Menu & System Popups:[/b] English Config screen labels/buttons and 23 system/save/load/confirm dialogs in [code]global-metadata.dat[/code].
[*][b]In-Game Screens & Chapter Title Cards:[/b] 30/33 forum/PC screen sprites ([code]screenpc.asset[/code]), 15/15 info sprites ([code]info.asset[/code]), and 27/27 chapter/ending title cards ([code]EpTitle[/code] — Full zip only).
[/list]

[b]Known Issues / Not Translated:[/b]
[list]
[*][b]SceneGift (891 lines):[/b] Vita-exclusive bonus scenario not present on PC — left in Japanese.
[*][b]Vita3K Opening Video (OP.mp4) Crash:[/b] Vita3K's stubbed [code]SceAvPlayer[/code] crashes when playing/closing the untouched [code]OP.mp4[/code] video. Skip the video immediately or load the autosave right before it to continue in Vita3K.
[*][b]Real Vita Hardware:[/b] Built and smoke-tested in Vita3K; real PS Vita [code]rePatch[/code] feedback is welcome!
[/list]

[b]GitHub Source & Patcher Scripts:[/b]
https://github.com/fiksr/our-world-is-ended-vita-english-patch
