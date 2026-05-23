# 🎙️ VoxBook

> **Turn any ebook into a chaptered audiobook in one click.** 60+ AI voices, 17 languages, completely free, runs offline-friendly. No API keys, no quotas, no fuss.
>
> 一键将电子书转换为带章节的有声书。60+种AI音色，17种语言，永久免费，本地运行。

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=flat-square">
  <img alt="Free" src="https://img.shields.io/badge/Free-Personal%20%26%20Commercial-success?style=flat-square">
  <img alt="Downloads" src="https://img.shields.io/badge/Downloads-Get%20Started-brightgreen?style=flat-square">
</p>

<p align="center">
  <b>English</b> ·
  <a href="#chinese">简体中文</a> ·
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#voices">Voices</a> ·
  <a href="#players">Players</a>
</p>

---

## ✨ Why VoxBook?

There are many TTS tools, but VoxBook is the **only one** that combines:

- 🚀 **One-click EXE** — Download, extract, double-click. Zero setup, zero dependencies.
- 🔁 **Resume from interruption** — Computer crashed mid-conversion? Restart and pick up exactly where it stopped.
- 🌍 **17 languages, 80+ voices** — Chinese (Mandarin/Cantonese/Taiwanese), English (US/UK), Japanese, Korean, French, German, Spanish, Italian, Portuguese, Russian, Arabic, Hindi, Vietnamese, Thai, and more.
- 🎨 **4 beautiful themes** — Light, Dark, Sepia (paper), Ocean.
- 📚 **Smart metadata extraction** — Auto-detects title, author, chapters, word count, estimated duration before you commit.
- 🗂️ **Auto file organization** — Output is neatly organized into `BookTitle-Author/` folders with original/audio/text/cover all properly labeled.
- 🖼️ **Cover art embedded** — Pulls cover from epub and embeds it into the M4B (so audiobook players show the artwork).
- 📊 **Real-time progress** — Live percentage, chapter tracking, ETA countdown, total elapsed time.
- 🔇 **System tray app** — Runs silently in the background. Closing the browser doesn't stop the conversion.
- 📜 **Conversion history** — All your past conversions tracked with stats.
- 🔒 **No API key required** — Uses Microsoft Edge Neural TTS through `edge-tts`. Free forever.
- 💯 **Free for personal AND commercial use** — MIT licensed. Use it however you want.

## 🎬 Demo

> *(Add screenshots in `screenshots/` and embed them here)*

```
1. Drag your ebook → 2. Pick a voice → 3. Click Start → 4. Get a chaptered M4B
```

## 🚀 Quick Start

### Option A — Download EXE (Windows, recommended for non-developers)

1. Go to [Releases](../../releases) and download the latest `VoxBook-vX.X.zip`
2. Extract anywhere
3. Double-click **`Run-启动.cmd`** (or `VoxBook.exe`)
4. The browser opens automatically. Done.

> First run downloads FFmpeg (~50MB) automatically — only once.

### Option B — Run from source (any OS)

```bash
git clone https://github.com/aimivv0/VoxBook.git
cd VoxBook

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Browser opens at `http://127.0.0.1:7860`.

### Option C — Build your own EXE

```bash
pip install pyinstaller
python build_exe.py
# Output in dist/VoxBook/
```

## 📖 Usage

1. **Drop a file** — Drag any `.epub`, `.txt`, `.pdf`, `.docx`, or `.mobi` onto the window.
2. **Read the overview** — VoxBook shows you chapters, word count, and estimated audiobook duration.
3. **Pick voice & speed** — 17 languages, 80+ voices, speed from -25% to +50%.
4. **Click Start** — Watch real-time progress with ETA.
5. **Find your audiobook** — Saved to `~/Documents/Audiobooks/BookTitle-Author/` with everything labeled:

```
~/Documents/Audiobooks/
└── 三体-刘慈欣/                       (Domestic author)
    ├── 三体-刘慈欣-原始 Source.epub   (Original ebook)
    ├── 三体-刘慈欣-音频 Audio.m4b     (Audiobook with chapters)
    ├── 三体-刘慈欣-转换 Text.txt      (Extracted plain text)
    └── 三体-刘慈欣-封面 Cover.jpg     (Cover image)

└── Sapiens-Yuval Noah Harari[Israel]/   (Foreign author with country tag)
    ├── ...-原始 Source.epub
    ├── ...-音频 Audio.m4b
    └── ...
```

## 🎙️ Voices

| Language | Voices | Highlights |
|----------|--------|------------|
| 🇨🇳 **Chinese (Mandarin/普通话)** | 15+ | Xiaoxiao 晓晓 (warm narrator), Yunyang 云扬 (professional anchor) |
| 🇨🇳 **Cantonese 粤语** | 3 | HiuGaai, HiuMaan, WanLung |
| 🇹🇼 **Taiwanese 台湾** | 3 | HsiaoChen, HsiaoYu, YunJhe |
| 🇺🇸 **English (US)** | 16 | Ava ★, Andrew ★ (newest neural), Jenny, Brian, Aria |
| 🇬🇧 **English (UK)** | 5 | Sonia, Ryan, Libby, Maisie, Thomas |
| 🇯🇵 **Japanese 日本語** | 5 | Nanami, Aoi, Keita, Daichi |
| 🇰🇷 **Korean 한국어** | 4 | SunHi, InJoon, BongJin, Hyunsu |
| 🇫🇷 **French** | 5 | Vivienne, Remy, Denise, Henri |
| 🇩🇪 **German** | 5 | Florian, Seraphina, Katja, Conrad |
| 🇪🇸 **Spanish** | 5 | Ximena, Elvira, Alvaro, Dalia, Jorge |
| 🇮🇹 **Italian** | 3 | Isabella, Elsa, Diego |
| 🇵🇹 **Portuguese** | 4 | Francisca, Antonio, Raquel, Duarte |
| 🇷🇺 **Russian** | 2 | Svetlana, Dmitry |
| 🇸🇦 **Arabic** | 3 | Zariyah, Hamed, Salma |
| 🇮🇳 **Hindi** | 2 | Swara, Madhur |
| 🇻🇳 **Vietnamese** | 2 | HoaiMy, NamMinh |
| 🇹🇭 **Thai** | 2 | Premwadee, Niwat |

> **★ = Newest "Multilingual" neural voices** — these can speak across multiple languages naturally.

## 🎵 Recommended Audiobook Players

| Platform | Player | Type |
|----------|--------|------|
| 🪟 Windows / 🍎 Mac / 🐧 Linux | [VLC](https://www.videolan.org/vlc/) | Free, all formats |
| 🪟 Windows / 🍎 Mac | [foobar2000](https://www.foobar2000.org/) | Free, audiophile |
| 🍎 Mac / 📱 iOS | Apple Books | Built-in |
| 📱 iOS | [BookPlayer](https://apps.apple.com/app/bookplayer/id1138219998) | Free, open-source |
| 📱 iOS | [Prologue](https://apps.apple.com/app/prologue/id1459223267) | Premium |
| 🤖 Android | [Smart AudioBook Player](https://play.google.com/store/apps/details?id=ak.alizandro.smartaudiobookplayer) | Free |
| 🤖 Android | [Voice](https://github.com/PaulWoitaschek/Voice) | Free, open-source |

> 💡 **Tip:** Use M4B format — all audiobook players recognize chapter markers and remember your listening position.

## 🛠️ How It Works

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌────────────┐
│  Your ebook  │ -> │ Parse + chunk   │ -> │ Edge Neural  │ -> │ FFmpeg     │
│  epub/pdf/.. │    │ ebooklib/calibre│    │ TTS per chunk│    │ merge+meta │
└──────────────┘    └─────────────────┘    └──────────────┘    └────────────┘
                                                  │
                                                  v
                                  ┌────────────────────────────┐
                                  │ M4B with chapters + cover  │
                                  └────────────────────────────┘
```

- **No cloud upload** — all processing happens locally; only TTS chunks are streamed through Microsoft Edge.
- **Resume on crash** — every chapter is cached. If conversion is interrupted, restarting picks up at the last completed chapter.
- **Smart chunking** — text is split by paragraphs and sentences (max 2000 chars/chunk) for optimal TTS quality.
- **Metadata extraction** — title, author, cover, chapters all auto-detected from epub.

## ❓ FAQ

<details>
<summary><b>Does it need internet?</b></summary>

Yes — Edge TTS calls Microsoft's free voice service. Your text is sent to MS for synthesis (same as the browser's built-in "Read aloud"). For sensitive content, see "Roadmap" for upcoming local TTS support.
</details>

<details>
<summary><b>How long does conversion take?</b></summary>

Roughly **1 minute per 10,000 characters**. A 300-page novel (~150K chars) takes ~15 minutes. Conversion is parallelized per chunk for speed.
</details>

<details>
<summary><b>What if it crashes mid-conversion?</b></summary>

Just restart and reload the same file. VoxBook caches every chapter and resumes automatically — you won't lose progress.
</details>

<details>
<summary><b>How do I add more voices?</b></summary>

Run `python -m edge_tts --list-voices` to see all 60+ voices. Edit the `VOICES` dict in `app.py` to add custom entries.
</details>

<details>
<summary><b>PDF/DOCX conversion fails?</b></summary>

Install [Calibre](https://calibre-ebook.com/download). It's used as the format converter. Without it, only `.epub` and `.txt` are supported natively.
</details>

<details>
<summary><b>Can I run it on a server / NAS?</b></summary>

Yes. Edit the `host="127.0.0.1"` to `host="0.0.0.0"` in `app.py`, then access from any device on your network.
</details>

<details>
<summary><b>Where are my settings/cache stored?</b></summary>

`~/Ebook2Audiobook/` (will be renamed to `~/VoxBook/` in next release):
- `config.json` — your preferences
- `cache/` — resume data (deleted after successful conversion)
- `tools/` — auto-downloaded ffmpeg
- `app.log` — debug log
</details>

## 🗺️ Roadmap

- [x] Multi-language voices (17 languages)
- [x] Resume on interrupt
- [x] Cover embedding in m4b
- [x] System tray
- [x] 4 themes
- [ ] Batch queue (convert multiple books)
- [ ] Local TTS engine (Kokoro/XTTS) — for full offline + privacy
- [ ] Voice mixing (different characters use different voices via LLM)
- [ ] Background music mixing
- [ ] Mobile-friendly UI
- [ ] Docker image
- [ ] CLI mode
- [ ] Browser extension (right-click any web article → audiobook)

Vote / suggest features in [Issues](../../issues)!

## 🤝 Contributing

PRs are very welcome. Areas that need help:

- 🐛 **Bug reports** — Especially edge-case ebook formats
- 🌐 **Translations** — UI is currently bilingual (EN/中文); other languages welcome
- 🎨 **Themes** — Add more color themes
- 📝 **Voice mappings** — Suggest custom voice display names for your language

```bash
git clone https://github.com/aimivv0/VoxBook.git
cd VoxBook
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 🆚 Comparison

| Feature | VoxBook | [audiblez](https://github.com/santinic/audiblez) | [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) | [epub_to_audiobook](https://github.com/p0n1/epub_to_audiobook) |
|---------|---------|----------|--------------------|--------------------|
| Web GUI | ✅ | ❌ CLI | ✅ | ❌ CLI |
| Free voices | ✅ Edge TTS | ✅ Kokoro | ✅ XTTS | ❌ Azure/OpenAI |
| Languages | **17** | 7 | 100+ | depends on TTS |
| Resume on crash | ✅ | ❌ | ❌ | ❌ |
| One-click EXE | ✅ | ❌ | ❌ | ❌ |
| System tray | ✅ | ❌ | ❌ | ❌ |
| Themes | ✅ 4 | ❌ | ❌ | ❌ |
| Auto file organization | ✅ | ❌ | ⚠️ | ⚠️ |
| Cover embedding | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Internet needed | ⚠️ Yes | ❌ Local | ❌ Local | ⚠️ Yes |

## 📜 License

[MIT](LICENSE) — **Free for personal AND commercial use.**
个人和商业用途均免费使用。

## 🙏 Credits

- [edge-tts](https://github.com/rany2/edge-tts) — TTS API wrapper
- [ebooklib](https://github.com/aerkalov/ebooklib) — epub parsing
- [Calibre](https://calibre-ebook.com) — format conversion
- [pystray](https://github.com/moses-palmer/pystray) — system tray
- Microsoft Edge Neural TTS — the actual voices
- All the audiobook lovers who tested early versions ❤️

---

<a name="chinese"></a>

## 🇨🇳 中文说明

VoxBook 是一款**一键将电子书转换为有声书**的工具。

### 特色亮点

- 🚀 **零依赖** — 下载即用，无需配置环境
- 🌍 **17种语言、80+音色** — 中文(普通话/粤语/台湾)、英文、日韩法德西意俄等
- �� **断点续传** — 大书中途崩溃，重启自动接着转
- 🎨 **4种主题** — 明亮/暗黑/护眼纸/海洋
- 📚 **智能解析** — 自动识别书名、作者、章节、字数、预估时长
- 🗂️ **自动归档** — 输出整齐分类: `书名-作者/` 文件夹包含原始/音频/文本/封面
- 🖼️ **封面嵌入** — 从 epub 提取封面嵌入 M4B
- 📊 **实时进度** — 真实百分比 + ETA + 总耗时
- 🔇 **系统托盘** — 后台静默运行，关浏览器不影响转换
- �� **历史记录** — 所有转换记录可查
- 💯 **个人/商业均免费** — MIT 协议

### 快速开始

**方式1 (Windows推荐)：** 在 [Releases](../../releases) 下载 zip → 解压 → 双击 `Run-启动.cmd`

**方式2 (源码)：**
```bash
git clone https://github.com/aimivv0/VoxBook.git
cd VoxBook
pip install -r requirements.txt
python app.py
```

### 使用流程

1. 拖入电子书 (epub/pdf/txt/docx/mobi)
2. 查看书籍概览
3. 选语音和语速
4. 点击开始
5. 文件保存到 `~/Documents/Audiobooks/书名-作者/`

详细信息请看上方英文版。

---

<p align="center">
  <b>If VoxBook saves you time, consider giving it a ⭐ star!</b><br>
  <i>如果 VoxBook 对你有帮助，请点个 ⭐ 支持一下！</i>
</p>