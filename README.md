# Ebook2Audiobook

> One-click convert any ebook to a chaptered audiobook with natural AI voices. **Free**, **open source**, **no API key needed**.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

## Features

- **One click** - Drag, drop, convert. No CLI, no config files.
- **30+ natural voices** - Chinese (Mandarin/Cantonese/Taiwanese) & English (US/British)
- **Real-time progress** - Live percentage, ETA countdown, total elapsed time
- **Smart book analysis** - Auto-detect chapters, word count, estimated duration before conversion
- **Auto file organization** - Output as `BookTitle-Author/` with labeled files
- **Speed control** - Adjust reading rate from -25% to +50%
- **Cover embedding** - Extracts cover from epub and embeds into m4b
- **History tracking** - See all your past conversions with stats
- **M4B with chapters** - Real chapter markers, perfect for audiobook players
- **100% free** - Uses Microsoft Edge Neural TTS (no quota, no key)
- **Web UI** - Clean browser interface, runs locally on `127.0.0.1`

## Quick Start

### Windows

1. Install [Python 3.10+](https://www.python.org/downloads/) - **check "Add to PATH"** during install
2. Install [ffmpeg](https://ffmpeg.org/download.html) (or place `ffmpeg.exe` in `./ffmpeg/`)
3. Download this project (Code -> Download ZIP)
4. Double-click **`setup.cmd`** (one-time install, ~2 min)
5. Double-click **`start.cmd`** - browser opens automatically

### macOS / Linux

```bash
# Install ffmpeg first
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

git clone https://github.com/YOUR_USERNAME/Ebook2Audiobook.git
cd Ebook2Audiobook
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://127.0.0.1:7860
```

### Optional: Install Calibre (for PDF/DOCX/MOBI support)

[Calibre](https://calibre-ebook.com/download) provides best-in-class format conversion. Without it, only `.epub` and `.txt` are supported natively.

## Usage

1. Run `start.cmd` (Windows) or `python app.py`
2. Browser opens at `http://127.0.0.1:7860`
3. Drag & drop your ebook (or click to select)
4. View book overview: chapters, word count, estimated duration
5. Pick a voice and speed
6. Click "Start"
7. Watch real-time progress with ETA
8. Find output in `audiobooks/BookTitle-Author/`

```
audiobooks/
└── BookTitle-Author/
    ├── BookTitle-Author-原始.epub  (original source)
    ├── BookTitle-Author-音频.m4b   (audiobook with chapters)
    ├── BookTitle-Author-转换.txt   (extracted text)
    └── BookTitle-Author-封面.jpg   (cover image)
```

## Voice List

### Chinese
| Voice | Style |
|-------|-------|
| **Xiaoxiao** | Warm narrator, best for novels |
| **Yunyang** | Professional anchor, most natural |
| Xiaoyi | Lively, cartoon style |
| Yunxi | Sunny, novel style |
| HsiaoChen | Taiwanese Mandarin |
| HiuGaai | Cantonese |

### English
| Voice | Style |
|-------|-------|
| **Andrew** | Newest, most natural male |
| **Ava** | Newest, most natural female |
| Brian | Calm audiobook narrator |
| Jenny | Warm narrator |
| Aria | Professional |
| Ryan | British |

Run `python -m edge_tts --list-voices` to see all 60+ available.

## Recommended Audiobook Players

| Platform | Player | Link |
|----------|--------|------|
| Windows / Mac / Linux | VLC Media Player | https://www.videolan.org/vlc/ |
| Windows / Mac | foobar2000 | https://www.foobar2000.org/ |
| Mac / iOS | Apple Books (built-in) | Pre-installed |
| iOS | BookPlayer (free, open source) | https://apps.apple.com/app/bookplayer/id1138219998 |
| iOS | Prologue (premium) | https://apps.apple.com/app/prologue/id1459223267 |
| Android | Smart AudioBook Player | https://play.google.com/store/apps/details?id=ak.alizandro.smartaudiobookplayer |
| Android | Voice (free, open source) | https://github.com/PaulWoitaschek/Voice |

> Tip: M4B format is ideal - recognized as an audiobook by all major players, with proper chapter navigation and resume support.

## Tech Stack

- **Backend**: Python + Flask
- **TTS**: [edge-tts](https://github.com/rany2/edge-tts) (Microsoft Edge Neural TTS, free)
- **Audio**: ffmpeg (concat + AAC encoding + chapter metadata)
- **Format conversion**: Calibre (optional) + ebooklib for epub
- **Frontend**: Vanilla HTML/CSS/JS - no build step

## Build Standalone EXE (Optional)

Want to ship a single `.exe` so users don't need Python?

```bash
pip install pyinstaller
python build_exe.py
```

The EXE will be in `dist/Ebook2Audiobook.exe` (~50 MB).

> Note: ffmpeg must still be available either in PATH or in `./ffmpeg/ffmpeg.exe` next to the EXE.

## FAQ

**Q: Need internet?**
A: Yes - Edge TTS calls Microsoft's free service.

**Q: How long does conversion take?**
A: Roughly 1 minute per 10,000 characters. A 300-page novel (~150K chars) takes ~15 min.

**Q: PDF conversion not working?**
A: Install [Calibre](https://calibre-ebook.com/download).

**Q: Can I add more voices?**
A: Edit the `VOICES` dict in `app.py`. Run `python -m edge_tts --list-voices` for the full list.

**Q: Why m4b not mp3?**
A: M4B supports chapter markers - you can navigate chapters in any audiobook player. Choose mp3 in the UI if needed.

## Alternatives

- [audiblez](https://github.com/santinic/audiblez) - Uses Kokoro (local), supports multi-voice
- [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) - XTTS voice cloning, 16 formats
- [epub_to_audiobook](https://github.com/p0n1/epub_to_audiobook) - CLI focused, supports Azure/OpenAI TTS

## Contributing

PRs welcome. Ideas:
- [ ] Batch queue (multiple books)
- [ ] Pause/resume conversion
- [ ] Voice mixing (different characters different voices)
- [ ] Background music
- [ ] Mobile-friendly UI
- [ ] Docker image
- [ ] Local TTS (Kokoro/XTTS) as alternative

## License

MIT - Use freely for personal or commercial purposes.

## Credits

- [edge-tts](https://github.com/rany2/edge-tts) - TTS API wrapper
- [ebooklib](https://github.com/aerkalov/ebooklib) - epub parsing
- [Calibre](https://calibre-ebook.com) - format conversion
- Microsoft Edge Neural TTS - the actual voices
