# 🎙️ VoxBook · 电子书有声化工具

> **一键将电子书转成带章节的有声书** · One-click ebook to audiobook converter
>
> 80+ AI 音色 · 17 种语言 · 永久免费 · 无需 API Key · 支持断点续传
>
> 80+ AI voices · 17 languages · Free forever · No API key · Resume on interrupt

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=flat-square">
  <img alt="Free" src="https://img.shields.io/badge/Free-Personal%20%26%20Commercial-success?style=flat-square">
</p>

<p align="center">
  <a href="../../releases/latest"><b>📥 下载 / Download</b></a> ·
  <a href="#-亮点--features">亮点</a> ·
  <a href="#-使用方法--usage">使用方法</a> ·
  <a href="#-音色列表--voices">音色</a> ·
  <a href="#-faq">FAQ</a>
</p>

**关键词 / Keywords**: 电子书转有声书, ebook to audiobook, epub转mp3, txt转语音, AI朗读, 听书工具, TTS, edge-tts, 中文语音合成, 免费有声书制作

---

## ✨ 亮点 / Features

- 🚀 **零依赖一键运行** · 下载解压双击即用，无需安装 Python 或配置环境
- 🌍 **17 种语言、80+ 音色** · 中文（普通话 / 粤语 / 台湾）、英语（美 / 英）、日语、韩语、法语、德语、西班牙语、意大利语、葡萄牙语、俄语、阿拉伯语、印地语、越南语、泰语等
- 🔁 **断点续传** · 转换中途崩溃或关机？重启后自动接着上次进度继续
- 🎨 **4 种 UI 主题** · 明亮 / 暗黑 / 护眼纸 / 海洋
- 🎚️ **语速可调** · -25% 到 +50% 共 6 档
- 📚 **智能元数据** · 自动识别书名、作者、章节、字数、预估时长
- 🗂️ **自动归档** · 输出整齐分类，原始文件 / 音频 / 文本 / 封面 全部清晰命名
- 🖼️ **封面嵌入** · 从 epub 提取封面嵌入 M4B（播放器显示书籍封面）
- 📊 **实时进度** · 真实百分比 + 剩余时间 + 总耗时
- 🔇 **系统托盘运行** · 后台静默运行，关浏览器不影响转换
- 📜 **历史记录** · 保留最近 50 条转换记录，含字数、章节、用时
- 💯 **个人 / 商业均免费** · MIT 协议

---

## 🚀 使用方法 / Usage

### 方式 A — 直接下载使用（Windows 推荐）

1. 在 [Releases](../../releases) 下载 `VoxBook-v1.0-Windows.zip`
2. 解压到任意位置
3. 双击 `Run-启动.cmd`
4. 浏览器自动打开，开始使用

### 方式 B — 源码运行（任意平台）

```bash
git clone https://github.com/aimivv0/VoxBook.git
cd VoxBook

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

浏览器访问 `http://127.0.0.1:7860`

### 方式 C — 自己打包 EXE

```bash
pip install pyinstaller
python build_exe.py
# 输出在 dist/VoxBook/
```

---

## ⚠️ 重要温馨提示 / Important Notes

### 1. 关于"无法验证发布者"弹窗

首次运行 `Run-启动.cmd` 时，Windows 会弹出"**无法验证发布者**"安全警告。

> 这是 Windows 给所有未购买代码签名证书的应用的标准提示，**与软件本身的安全性无关**。
>
> ✅ 直接点 **运行(R)** 即可，不影响使用。
>
> 💡 如果不想每次都弹，可以右键 `Run-启动.cmd` → 属性 → 勾选 **解除锁定** → 确定。

### 2. 启动后的黑色命令窗口千万不要关

启动后会出现一个黑色的命令窗口（控制台），它是程序的"心脏"。

> ⚠️ **请保持窗口最小化但不要关闭它**，否则程序会立即退出，正在转换的任务会中断。
>
> ✅ 不过别担心，VoxBook **支持断点续传**：即使中断了，下次启动并重新选择同一本书，会从上次位置继续，不用重头开始。

### 3. 首次启动会自动下载 FFmpeg

VoxBook 需要 FFmpeg 处理音频。首次启动会自动下载约 50MB 的 FFmpeg 到用户目录，**仅一次**。

---

## 📖 输出结构 / Output Structure

转换完成后，所有相关文件会归到一个清晰命名的子文件夹中：

```
~/Documents/Audiobooks/
├── 三体-刘慈欣/                              （国内作者）
│   ├── 三体-刘慈欣-原始 Source.epub          原始电子书
│   ├── 三体-刘慈欣-音频 Audio.m4b            带章节的有声书
│   ├── 三体-刘慈欣-转换 Text.txt             提取的纯文本
│   └── 三体-刘慈欣-封面 Cover.jpg            封面图
│
└── Sapiens-Yuval Noah Harari[Israel]/        （国外作者会自动加国家标签）
    ├── ...-原始 Source.epub
    ├── ...-音频 Audio.m4b
    └── ...
```

---

## 🎙️ 音色列表 / Voices

| 语言 / Language | 音色数 | 推荐 |
|---|---|---|
| 🇨🇳 中文普通话 Chinese (Mandarin) | 15+ | 晓晓 Xiaoxiao（温暖叙述）、云扬 Yunyang（专业播音） |
| 🇨🇳 粤语 Cantonese | 3 | HiuGaai、HiuMaan、WanLung |
| 🇹🇼 台湾普通话 Taiwanese | 3 | HsiaoChen、HsiaoYu、YunJhe |
| 🇺🇸 英语（美）English (US) | 16 | Ava ★、Andrew ★（最新神经网络音色）、Jenny、Brian |
| 🇬🇧 英语（英）English (UK) | 5 | Sonia、Ryan、Libby、Maisie、Thomas |
| 🇯🇵 日本語 Japanese | 5 | Nanami、Aoi、Keita |
| 🇰🇷 한국어 Korean | 4 | SunHi、InJoon |
| 🇫🇷 法语 French | 5 | Vivienne、Remy、Denise |
| 🇩🇪 德语 German | 5 | Florian、Seraphina、Katja |
| 🇪🇸 西班牙语 Spanish | 5 | Ximena、Alvaro、Dalia |
| 🇮🇹 意大利语 Italian | 3 | Isabella、Diego |
| 🇵🇹 葡萄牙语 Portuguese | 4 | Francisca、Antonio |
| 🇷🇺 俄语 Russian | 2 | Svetlana、Dmitry |
| 🇸🇦 阿拉伯语 Arabic | 3 | Zariyah、Hamed、Salma |
| 🇮🇳 印地语 Hindi | 2 | Swara、Madhur |
| 🇻🇳 越南语 Vietnamese | 2 | HoaiMy、NamMinh |
| 🇹🇭 泰语 Thai | 2 | Premwadee、Niwat |

> ★ 标记的是最新的 **Multilingual** 多语言神经音色，效果最自然

---

## 🎵 推荐播放器 / Recommended Players

| 平台 | 播放器 | 链接 |
|---|---|---|
| 🪟 Windows / 🍎 Mac / 🐧 Linux | **VLC**（免费开源） | https://www.videolan.org/vlc/ |
| 🪟 Windows / 🍎 Mac | foobar2000 | https://www.foobar2000.org/ |
| 🍎 Mac / 📱 iOS | Apple 图书（系统自带） | 系统自带 |
| 📱 iOS | BookPlayer（免费开源） | https://apps.apple.com/app/bookplayer/id1138219998 |
| �� iOS | Prologue（付费） | https://apps.apple.com/app/prologue/id1459223267 |
| 🤖 Android | Smart AudioBook Player（免费） | https://play.google.com/store/apps/details?id=ak.alizandro.smartaudiobookplayer |
| 🤖 Android | Voice（免费开源） | https://github.com/PaulWoitaschek/Voice |

> 💡 **小贴士**：M4B 格式是有声书的标准格式，所有主流音频应用都能识别章节标记并自动记忆听到的位置。

---

## 🛠️ 工作流程 / How It Works

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌────────────┐
│  你的电子书  │ -> │  解析 + 分块    │ -> │  Edge 神经   │ -> │  FFmpeg    │
│ epub/pdf/.. │    │ ebooklib/calibre│    │  TTS 逐段合成│    │  合并+元数据│
└──────────────┘    └─────────────────┘    └──────────────┘    └────────────┘
                                                                      │
                                                                      v
                                            ┌─────────────────────────────┐
                                            │ 带章节 + 封面的 M4B 有声书 │
                                            └─────────────────────────────┘
```

- **本地处理** · 解析、分章、归档全在你电脑上完成；只有 TTS 文本块通过 Edge TTS 服务合成
- **断点续传** · 每章独立缓存，中断时下次自动续转
- **智能分块** · 按段落和句子智能切分，每块最大 2000 字符，保证 TTS 质量
- **元数据自动提取** · 标题、作者、封面、章节从 epub 自动识别

---

## ❓ FAQ

<details>
<summary><b>需要联网吗？</b></summary>

需要。Edge TTS 调用微软的免费在线服务（与浏览器自带的"朗读功能"是同一个服务）。如果对内容隐私敏感，可以等下个版本支持本地 TTS（Kokoro / XTTS）。
</details>

<details>
<summary><b>转换需要多久？</b></summary>

大约 **每 1 万字 1 分钟**。一本 30 万字的小说约 30 分钟。
</details>

<details>
<summary><b>转换中途崩溃怎么办？</b></summary>

不用担心。VoxBook 会缓存每一章节，重启后选择同一本书，会自动从上次中断处接着转。
</details>

<details>
<summary><b>PDF / DOCX / MOBI 怎么处理？</b></summary>

需要安装 [Calibre](https://calibre-ebook.com/download)（免费），它会作为格式转换器。如果不安装，目前仅支持 `.epub` 和 `.txt` 直接转换。
</details>

<details>
<summary><b>怎么添加自定义音色？</b></summary>

运行 `python -m edge_tts --list-voices` 查看全部 60+ 音色，然后在 `app.py` 的 `VOICES` 字典里添加你想要的音色。
</details>

<details>
<summary><b>能在 NAS / 服务器上运行吗？</b></summary>

可以。把 `app.py` 里的 `host="127.0.0.1"` 改成 `host="0.0.0.0"`，然后从局域网任意设备访问 `http://你的服务器IP:7860`。
</details>

<details>
<summary><b>用户数据保存在哪？</b></summary>

`~/Ebook2Audiobook/` 目录：
- `config.json` — 你的设置（输出路径、主题等）
- `cache/` — 断点续传缓存（成功后自动清理）
- `tools/` — 自动下载的 FFmpeg
- `app.log` — 调试日志
</details>

<details>
<summary><b>Need internet?</b></summary>

Yes — Edge TTS calls Microsoft's free voice service. Your text is sent to MS for synthesis (same as browser's "Read aloud").
</details>

<details>
<summary><b>How long does conversion take?</b></summary>

About **1 minute per 10,000 characters**. A 300-page novel (~150K chars) takes ~15 min.
</details>

<details>
<summary><b>What if it crashes mid-conversion?</b></summary>

VoxBook caches every chapter. Restart and reload the same file — it picks up automatically.
</details>

---

## 🆚 对比 / Comparison

| 功能 / Feature | VoxBook | [audiblez](https://github.com/santinic/audiblez) | [ebook2audiobook](https://github.com/DrewThomasson/ebook2audiobook) | [epub_to_audiobook](https://github.com/p0n1/epub_to_audiobook) |
|---|---|---|---|---|
| Web 图形界面 | ✅ | ❌ CLI | ✅ | ❌ CLI |
| 免费音色 | ✅ Edge TTS | ✅ Kokoro | ✅ XTTS | ❌ Azure/OpenAI |
| 支持语言 | **17** | 7 | 100+ | 取决于 TTS |
| 断点续传 | ✅ | ❌ | ❌ | ❌ |
| 一键 EXE | ✅ | ❌ | ❌ | ❌ |
| 系统托盘 | ✅ | ❌ | ❌ | ❌ |
| 主题切换 | ✅ 4 种 | ❌ | ❌ | ❌ |
| 自动归档命名 | ✅ | ❌ | ⚠️ | ⚠️ |
| 封面嵌入 | ✅ | ⚠️ | ⚠️ | ⚠️ |
| 中文界面 | ✅ | ❌ | ❌ | ❌ |

---

## 📜 License / 许可

[MIT](LICENSE) — **个人和商业用途均免费使用** · Free for personal AND commercial use

---

<p align="center">
  <b>如果 VoxBook 帮你节省了时间，请点 ⭐ 支持一下</b><br>
  <i>If VoxBook saves you time, please give it a ⭐</i>
</p>