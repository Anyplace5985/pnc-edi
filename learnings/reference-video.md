# Capturing reference video

How to capture and read a play-through recording. Largely historical - the sprite assets replaced
this method, and §88 closed the last use for it: `code/refvideo.py` *renders* a video per scene
straight out of the shipped clips, so a reference video whose timing is the game's no longer needs
a recording at all. Capture is only for something that is not in the assets.

**Read this when:** a scene cannot be measured from the assets and a recording is the only source

**Keywords:** capture, dwell, menu detection, audio onset, ROI, brazier flicker

---

- **Uniform dwell (~10 s per scene) is the single thing that matters.** It makes scene
  boundaries findable and verifiable. Variable dwell was why the first capture
  mis-attributed measurements.
- Menus are reliably found by **template-matching the menu background** (bookshelf +
  checkerboard borders, centre masked out) — better than cut detection or stillness.
- **Read the character name at the menu's *end***, just before entry. Mid-menu frames may
  still show the previous character.
- Audio is only useful if the game's music is off. Where it worked (`D1`) it gave the most
  precise period of the whole project via impact-onset spacing — but audio led video by
  ~130 ms, so use **audio for period, video for phase**.
- Colour matters: extracting grayscale loses the ability to mask **brazier/torch flicker**,
  which is the highest-variance thing on screen and hijacks ROI selection. Mask warm
  pixels (`R-B > 45 & R > 110`, dilated) and the UI borders.

---

**This method has been superseded for almost everything.** Sprite animations mean the exact frame
sequence, period and motion come out of the shipped assets - see `asset-inspection.md` and
`funscript-proxies.md`. Reach for a capture only when a scene genuinely is not in the assets.
