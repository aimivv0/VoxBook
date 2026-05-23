"""
AudioBookify - Convert ebooks to audiobooks
v2.0 - Zero-dependency edition with auto ffmpeg download, resume, system tray
"""
import os, sys, json, threading, subprocess, tempfile, shutil, re, time, asyncio, hashlib, urllib.request, zipfile
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file

# 显示启动信息
print("=" * 65)
print("VoxBook v1.0 - 电子书转有声书工具")
print("=" * 65)
print()
print("✓ 程序已启动，请勿关闭此窗口！")
print("✓ 转换过程中请保持此命令窗口打开")
print("✓ 浏览器将自动打开，如未打开请访问: http://127.0.0.1:7860")
print()
print("=" * 65)
print()

app = Flask(__name__)

# ============ 路径检测 (兼容 PyInstaller / 源码) ============
if getattr(sys, "frozen", False):
    # PyInstaller bundled
    APP_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else APP_DIR
else:
    APP_DIR = Path(__file__).parent
    BUNDLE_DIR = APP_DIR

# 用户数据目录(放配置/缓存/输出)
USER_DATA_DIR = Path(os.path.expanduser("~")) / "AudioBookify"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = USER_DATA_DIR / "config.json"
CACHE_DIR = USER_DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
TOOLS_DIR = USER_DATA_DIR / "tools"
TOOLS_DIR.mkdir(exist_ok=True)

# 默认输出位置 (用户首次运行可改)
DEFAULT_OUTPUT = Path(os.path.expanduser("~")) / "Documents" / "Audiobooks"

# ============ 配置加载 ============
def load_config():
    default = {
        "output_dir": str(DEFAULT_OUTPUT),
        "theme": "light",
        "language": "zh",
        "first_run": False
    }
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for k, v in default.items():
                cfg.setdefault(k, v)
            return cfg
        except: pass
    return default

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

config = load_config()
OUTPUT_DIR = Path(config["output_dir"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============ FFmpeg 自动下载 ============
FFMPEG_URL = "https://github.com/GyanD/codexffmpeg/releases/download/2024-12-30-git-cb1a2cdc36/ffmpeg-2024-12-30-git-cb1a2cdc36-essentials_build.zip"
FFMPEG_LOCAL = TOOLS_DIR / "ffmpeg.exe"
FFPROBE_LOCAL = TOOLS_DIR / "ffprobe.exe"

ffmpeg_status = {"downloading": False, "progress": 0, "error": ""}

def get_ffmpeg():
    """获取 ffmpeg 路径，优先级: 同目录 > PATH > 用户目录 > 自动下载"""
    # 1. 同目录
    local = APP_DIR / "ffmpeg.exe"
    if local.exists(): return str(local)
    # 2. PATH
    pth = shutil.which("ffmpeg")
    if pth: return pth
    # 3. 用户目录已下载
    if FFMPEG_LOCAL.exists(): return str(FFMPEG_LOCAL)
    return None

def download_ffmpeg():
    """下载并解压 ffmpeg essentials build"""
    global ffmpeg_status
    ffmpeg_status["downloading"] = True
    ffmpeg_status["progress"] = 0
    try:
        zip_path = TOOLS_DIR / "ffmpeg.zip"
        def reporthook(blocks, blocksize, total):
            if total > 0:
                ffmpeg_status["progress"] = int(blocks * blocksize * 100 / total)
        urllib.request.urlretrieve(FFMPEG_URL, str(zip_path), reporthook=reporthook)
        # 解压
        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.endswith("/ffmpeg.exe") or name.endswith("/ffprobe.exe"):
                    info = z.getinfo(name)
                    info.filename = Path(name).name
                    z.extract(info, str(TOOLS_DIR))
        zip_path.unlink()
        ffmpeg_status["downloading"] = False
        return True
    except Exception as e:
        ffmpeg_status["error"] = str(e)
        ffmpeg_status["downloading"] = False
        return False

# 初始化 ffmpeg
FFMPEG = get_ffmpeg()
# ============ 语音库 (扩展版: 30+种语言) ============
VOICES = {
    "中文女声 Chinese Female": {
        "zh-CN-XiaoxiaoNeural": "晓晓 Xiaoxiao - 温暖叙述 ★推荐",
        "zh-CN-XiaoyiNeural": "晓伊 Xiaoyi - 活泼可爱",
        "zh-CN-liaoning-XiaobeiNeural": "晓北 Xiaobei - 东北方言",
        "zh-CN-shaanxi-XiaoniNeural": "晓妮 Xiaoni - 陕西方言",
        "zh-TW-HsiaoChenNeural": "晓臻 HsiaoChen - 台湾",
        "zh-TW-HsiaoYuNeural": "晓雨 HsiaoYu - 台湾温柔",
        "zh-HK-HiuGaaiNeural": "晓佳 HiuGaai - 粤语",
        "zh-HK-HiuMaanNeural": "晓曼 HiuMaan - 粤语柔和",
    },
    "中文男声 Chinese Male": {
        "zh-CN-YunyangNeural": "云扬 Yunyang - 专业播音 ★推荐",
        "zh-CN-YunxiNeural": "云希 Yunxi - 阳光小说",
        "zh-CN-YunjianNeural": "云健 Yunjian - 激情体育",
        "zh-CN-YunxiaNeural": "云夏 Yunxia - 可爱卡通",
        "zh-CN-YunfengNeural": "云枫 Yunfeng - 沉稳",
        "zh-CN-YunhaoNeural": "云皓 Yunhao - 男声广告",
        "zh-CN-YunzeNeural": "云泽 Yunze - 中年沧桑",
        "zh-TW-YunJheNeural": "云哲 YunJhe - 台湾",
        "zh-HK-WanLungNeural": "万龙 WanLung - 粤语",
    },
    "English (US) Female": {
        "en-US-AvaMultilingualNeural": "Ava - Newest, Multilingual ★Best",
        "en-US-EmmaMultilingualNeural": "Emma - Multilingual",
        "en-US-AvaNeural": "Ava - Natural",
        "en-US-JennyNeural": "Jenny - Warm narrator",
        "en-US-AriaNeural": "Aria - Professional",
        "en-US-EmmaNeural": "Emma - Conversational",
        "en-US-MichelleNeural": "Michelle - Friendly",
        "en-US-AnaNeural": "Ana - Young/Child",
    },
    "English (US) Male": {
        "en-US-AndrewMultilingualNeural": "Andrew - Newest, Multilingual ★Best",
        "en-US-BrianMultilingualNeural": "Brian - Multilingual",
        "en-US-AndrewNeural": "Andrew - Natural",
        "en-US-BrianNeural": "Brian - Calm narrator",
        "en-US-GuyNeural": "Guy - News anchor",
        "en-US-ChristopherNeural": "Christopher - Clear",
        "en-US-EricNeural": "Eric - Mature",
        "en-US-RogerNeural": "Roger - Senior",
        "en-US-SteffanNeural": "Steffan - Friendly",
    },
    "English (UK)": {
        "en-GB-SoniaNeural": "Sonia - British female",
        "en-GB-LibbyNeural": "Libby - British warm",
        "en-GB-MaisieNeural": "Maisie - British young",
        "en-GB-RyanNeural": "Ryan - British male",
        "en-GB-ThomasNeural": "Thomas - British warm",
    },
    "日本語 Japanese": {
        "ja-JP-NanamiNeural": "Nanami - Female warm",
        "ja-JP-AoiNeural": "Aoi - Female young",
        "ja-JP-MayuNeural": "Mayu - Female",
        "ja-JP-KeitaNeural": "Keita - Male",
        "ja-JP-DaichiNeural": "Daichi - Male warm",
    },
    "한국어 Korean": {
        "ko-KR-SunHiNeural": "SunHi - Female",
        "ko-KR-InJoonNeural": "InJoon - Male",
        "ko-KR-BongJinNeural": "BongJin - Male",
        "ko-KR-HyunsuNeural": "Hyunsu - Male young",
    },
    "Français French": {
        "fr-FR-VivienneMultilingualNeural": "Vivienne - Multilingual",
        "fr-FR-RemyMultilingualNeural": "Remy - Multilingual",
        "fr-FR-DeniseNeural": "Denise - Female",
        "fr-FR-EloiseNeural": "Eloise - Female young",
        "fr-FR-HenriNeural": "Henri - Male",
    },
    "Deutsch German": {
        "de-DE-FlorianMultilingualNeural": "Florian - Multilingual",
        "de-DE-SeraphinaMultilingualNeural": "Seraphina - Multilingual",
        "de-DE-KatjaNeural": "Katja - Female",
        "de-DE-AmalaNeural": "Amala - Female",
        "de-DE-ConradNeural": "Conrad - Male",
    },
    "Español Spanish": {
        "es-ES-XimenaNeural": "Ximena - Female",
        "es-ES-ElviraNeural": "Elvira - Female",
        "es-ES-AlvaroNeural": "Alvaro - Male",
        "es-MX-DaliaNeural": "Dalia - Mexican female",
        "es-MX-JorgeNeural": "Jorge - Mexican male",
    },
    "Italiano Italian": {
        "it-IT-IsabellaNeural": "Isabella - Female",
        "it-IT-ElsaNeural": "Elsa - Female",
        "it-IT-DiegoNeural": "Diego - Male",
    },
    "Português Portuguese": {
        "pt-BR-FranciscaNeural": "Francisca - Brazilian female",
        "pt-BR-AntonioNeural": "Antonio - Brazilian male",
        "pt-PT-RaquelNeural": "Raquel - Portugal female",
        "pt-PT-DuarteNeural": "Duarte - Portugal male",
    },
    "Русский Russian": {
        "ru-RU-SvetlanaNeural": "Svetlana - Female",
        "ru-RU-DmitryNeural": "Dmitry - Male",
    },
    "العربية Arabic": {
        "ar-SA-ZariyahNeural": "Zariyah - Female (Saudi)",
        "ar-SA-HamedNeural": "Hamed - Male (Saudi)",
        "ar-EG-SalmaNeural": "Salma - Female (Egypt)",
    },
    "हिन्दी Hindi": {
        "hi-IN-SwaraNeural": "Swara - Female",
        "hi-IN-MadhurNeural": "Madhur - Male",
    },
    "Tiếng Việt Vietnamese": {
        "vi-VN-HoaiMyNeural": "HoaiMy - Female",
        "vi-VN-NamMinhNeural": "NamMinh - Male",
    },
    "ภาษาไทย Thai": {
        "th-TH-PremwadeeNeural": "Premwadee - Female",
        "th-TH-NiwatNeural": "Niwat - Male",
    },
}

# ============ 状态 ============
status = {
    "running": False, "step": 0, "step_name": "",
    "real_pct": 0, "progress_detail": "",
    "chapters_done": 0, "chapters_total": 0,
    "output_file": "", "error": "",
    "book_info": None, "eta": "",
    "start_time": 0, "total_time": "",
    "rate": "+0%", "resumable": False,
    "current_book_id": ""
}
# ============ 工具函数 ============
def parse_filename_meta(filename):
    name = Path(filename).stem
    info = {"title": name, "author": "", "country": ""}
    m = re.match(r'^(.+?)\s*[\(（]([^()（）]+)[\)）]', name)
    if m:
        title = m.group(1).strip()
        author = m.group(2).strip()
        author = re.sub(r'(z-library|1lib|z-lib)\..*', '', author, flags=re.I).strip(' ,，.')
        if author and not re.search(r'(z-library|1lib|z-lib|library)', author, re.I):
            info["title"] = title
            info["author"] = author
    return info

def book_id(filepath):
    """生成书的唯一ID用于断点续传"""
    h = hashlib.md5()
    h.update(str(Path(filepath).name).encode("utf-8"))
    h.update(str(os.path.getsize(filepath)).encode("utf-8"))
    return h.hexdigest()[:16]

def extract_text_and_chapters(filepath):
    ext = Path(filepath).suffix.lower()
    chapters = []
    if ext == ".epub":
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            book = epub.read_epub(str(filepath))
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                title = None
                for tag in ["h1", "h2", "h3"]:
                    found = soup.find(tag)
                    if found:
                        title = found.get_text(strip=True)
                        break
                paras = []
                for p in soup.find_all(["p", "div"]):
                    t = p.get_text(separator=" ", strip=True)
                    if t and len(t) > 10:
                        paras.append(t)
                text = "\n\n".join(paras)
                if text.strip():
                    chapters.append((title or f"Chapter {len(chapters)+1}", text))
            meta = {"title": "", "author": ""}
            try:
                t = book.get_metadata("DC", "title")
                if t: meta["title"] = t[0][0]
                a = book.get_metadata("DC", "creator")
                if a: meta["author"] = a[0][0]
            except: pass
            return chapters, meta
        except Exception as e:
            print(f"epub parse error: {e}")
            return [], {}
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        parts = re.split(r'\n(?=(?:第[一二三四五六七八九十百千零\d]+[章节回]|Chapter\s+\d+|CHAPTER\s+\d+))', content)
        for part in parts:
            part = part.strip()
            if not part: continue
            lines = part.split("\n", 1)
            title = lines[0][:50] if len(lines) > 1 else f"Chapter {len(chapters)+1}"
            text = lines[1] if len(lines) > 1 else lines[0]
            if len(text.strip()) > 50:
                chapters.append((title, text))
        if not chapters:
            chunk_size = 5000
            for i in range(0, len(content), chunk_size):
                chapters.append((f"Part {i//chunk_size+1}", content[i:i+chunk_size]))
        return chapters, {}
    else:
        return [], {}

def split_text_for_tts(text, max_len=2000):
    if len(text) <= max_len:
        return [text]
    chunks = []
    paras = text.split("\n\n")
    current = ""
    for para in paras:
        if len(current) + len(para) < max_len:
            current += "\n\n" + para if current else para
        else:
            if current: chunks.append(current)
            if len(para) > max_len:
                sentences = re.split(r'(?<=[。！？.!?])\s*', para)
                cur = ""
                for s in sentences:
                    if len(cur) + len(s) < max_len:
                        cur += s
                    else:
                        if cur: chunks.append(cur)
                        cur = s
                if cur: chunks.append(cur)
                current = ""
            else:
                current = para
    if current: chunks.append(current)
    return chunks

async def tts_to_file(text, voice, output_path, rate="+0%"):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

def extract_cover(filepath):
    if not str(filepath).lower().endswith(".epub"): return None
    try:
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(str(filepath))
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER or "cover" in (item.get_name() or "").lower():
                if item.media_type and item.media_type.startswith("image/"):
                    ext = ".jpg" if "jpeg" in item.media_type or "jpg" in item.media_type else ".png"
                    cover_path = os.path.join(tempfile.gettempdir(), f"cover_{int(time.time())}{ext}")
                    with open(cover_path, "wb") as f: f.write(item.get_content())
                    return cover_path
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            ext = ".jpg" if "jpeg" in (item.media_type or "") else ".png"
            cover_path = os.path.join(tempfile.gettempdir(), f"cover_{int(time.time())}{ext}")
            with open(cover_path, "wb") as f: f.write(item.get_content())
            return cover_path
    except: pass
    return None

def format_time(secs):
    if secs < 60: return f"{int(secs)}s"
    elif secs < 3600: return f"{int(secs//60)}m{int(secs%60)}s"
    else: return f"{int(secs//3600)}h{int((secs%3600)//60)}m"

def update_status(**kwargs):
    global status
    for k, v in kwargs.items():
        status[k] = v
# ============ 主转换流程 (支持断点续传) ============
def run_conversion(filepath, voice, output_format="m4b", rate="+0%"):
    global status, FFMPEG
    work_dir = None
    try:
        start_time = time.time()
        status["start_time"] = start_time
        
        # 检查 ffmpeg
        if not FFMPEG:
            FFMPEG = get_ffmpeg()
        if not FFMPEG:
            status["error"] = "FFmpeg not found. Please wait for download or install manually."
            status["running"] = False
            return
        
        bid = book_id(filepath)
        status["current_book_id"] = bid
        
        update_status(step=1, step_name="Parsing / 解析", real_pct=5, progress_detail="Reading...")
        
        meta_from_name = parse_filename_meta(Path(filepath).name)
        chapters, meta_from_book = extract_text_and_chapters(filepath)
        
        if not chapters:
            status["error"] = "Could not parse file content / 无法解析文件"
            status["running"] = False
            return
        
        book_info = {
            "title": meta_from_name.get("title") or meta_from_book.get("title", "Unknown"),
            "author": meta_from_name.get("author") or meta_from_book.get("author", ""),
            "country": meta_from_name.get("country", ""),
            "chapters": len(chapters),
            "chars": sum(len(c[1]) for c in chapters),
        }
        status["book_info"] = book_info
        update_status(real_pct=10, progress_detail=f"{len(chapters)} chapters, {book_info['chars']} chars", chapters_total=len(chapters))
        
        # 用书ID做工作目录,支持断点续传
        work_dir = CACHE_DIR / bid
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存进度状态文件
        progress_file = work_dir / "progress.json"
        completed_chapters = set()
        if progress_file.exists():
            try:
                p = json.loads(progress_file.read_text(encoding="utf-8"))
                completed_chapters = set(p.get("completed", []))
                if completed_chapters:
                    update_status(progress_detail=f"Resuming... {len(completed_chapters)} chapters already done")
            except: pass
        
        update_status(step=2, step_name="Generating Audio / 生成音频", real_pct=15)
        
        # 生成每章音频
        chunks_per_chapter = [split_text_for_tts(t) for _, t in chapters]
        total_chunks = sum(len(c) for c in chunks_per_chapter)
        chunks_done = sum(len(chunks_per_chapter[i]) for i in range(len(chapters)) if i in completed_chapters)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        chapter_files = []
        for ch_idx, ((ch_title, ch_text), chunks) in enumerate(zip(chapters, chunks_per_chapter)):
            ch_file = work_dir / f"chapter_{ch_idx:04d}.mp3"
            if ch_idx in completed_chapters and ch_file.exists():
                chapter_files.append((ch_title, str(ch_file)))
                continue
            
            ch_audio_files = []
            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip(): continue
                chunk_file = str(work_dir / f"ch{ch_idx:04d}_pt{chunk_idx:04d}.mp3")
                # 如果该chunk已存在且非空，跳过
                if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 100:
                    ch_audio_files.append(chunk_file)
                    chunks_done += 1
                    pct = 15 + int(chunks_done / max(1, total_chunks) * 75)
                    update_status(real_pct=pct, chapters_done=ch_idx + 1)
                    continue
                # 重试3次
                success = False
                for attempt in range(3):
                    try:
                        loop.run_until_complete(tts_to_file(chunk, voice, chunk_file, rate=rate))
                        if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 100:
                            ch_audio_files.append(chunk_file)
                            success = True
                            break
                    except Exception as e:
                        if attempt < 2:
                            time.sleep(2)
                            continue
                        print(f"TTS failed ch{ch_idx} chunk{chunk_idx}: {e}")
                if not success:
                    print(f"Skipping failed chunk")
                
                chunks_done += 1
                pct = 15 + int(chunks_done / max(1, total_chunks) * 75)
                elapsed = time.time() - start_time
                eta_str = format_time((elapsed / max(1, chunks_done)) * (total_chunks - chunks_done)) if chunks_done > 0 else "..."
                update_status(
                    real_pct=pct,
                    chapters_done=ch_idx + 1,
                    progress_detail=f"Chapter {ch_idx+1}/{len(chapters)}: {ch_title[:30]}",
                    eta=eta_str
                )
            
            # 合并本章
            if ch_audio_files:
                if len(ch_audio_files) == 1:
                    shutil.move(ch_audio_files[0], str(ch_file))
                else:
                    list_file = work_dir / f"list_{ch_idx}.txt"
                    list_file.write_text("\n".join(f"file '{f}'" for f in ch_audio_files), encoding="utf-8")
                    subprocess.run(
                        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(ch_file)],
                        capture_output=True
                    )
                    for af in ch_audio_files:
                        try: os.unlink(af)
                        except: pass
                    try: list_file.unlink()
                    except: pass
                if ch_file.exists():
                    chapter_files.append((ch_title, str(ch_file)))
                    completed_chapters.add(ch_idx)
                    progress_file.write_text(json.dumps({"completed": list(completed_chapters)}), encoding="utf-8")
        
        if not chapter_files:
            status["error"] = "No audio generated"
            status["running"] = False
            return
        
        # 合并归档
        update_status(step=3, step_name="Finalizing / 归档", real_pct=92, progress_detail="Merging chapters...")
        
        merged_mp3 = str(work_dir / "merged.mp3")
        if len(chapter_files) == 1:
            shutil.copy2(chapter_files[0][1], merged_mp3)
        else:
            list_file = work_dir / "all_list.txt"
            list_file.write_text("\n".join(f"file '{cf}'" for _, cf in chapter_files), encoding="utf-8")
            subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", merged_mp3], capture_output=True)
            try: list_file.unlink()
            except: pass
        
        if not os.path.exists(merged_mp3):
            status["error"] = "Merge failed"
            status["running"] = False
            return
        
        # 输出文件夹
        title = book_info["title"]
        author = book_info["author"]
        country = book_info.get("country", "")
        if author:
            base_name = f"{title}-{author}[{country}]" if country else f"{title}-{author}"
        else:
            base_name = title
        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)[:120]
        
        dest_dir = OUTPUT_DIR / base_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取封面
        cover_path = extract_cover(filepath)
        if cover_path and os.path.exists(cover_path):
            shutil.copy2(cover_path, str(dest_dir / f"{base_name}-封面 Cover{Path(cover_path).suffix}"))
        
        # 输出m4b/mp3
        update_status(real_pct=96, progress_detail="Encoding final audio...")
        
        if output_format == "m4b":
            audio_out = str(dest_dir / f"{base_name}-音频 Audio.m4b")
            # 章节元数据
            meta_file = work_dir / "chapters.txt"
            with open(meta_file, "w", encoding="utf-8") as f:
                f.write(";FFMETADATA1\n")
                f.write(f"title={title}\n")
                if author: f.write(f"artist={author}\n")
                f.write(f"album={title}\n")
                cumulative_ms = 0
                for ch_title, ch_f in chapter_files:
                    probe = subprocess.run([FFMPEG, "-i", ch_f], capture_output=True)
                    stderr_text = probe.stderr.decode("utf-8", errors="replace") if probe.stderr else ""
                    duration_match = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', stderr_text)
                    if duration_match:
                        h, m, s = duration_match.groups()
                        dur_ms = int((int(h)*3600 + int(m)*60 + float(s)) * 1000)
                    else:
                        dur_ms = 60000
                    f.write(f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={cumulative_ms}\nEND={cumulative_ms+dur_ms}\ntitle={ch_title}\n")
                    cumulative_ms += dur_ms
            
            ff_cmd = [FFMPEG, "-y", "-i", merged_mp3, "-i", str(meta_file)]
            if cover_path and os.path.exists(cover_path):
                ff_cmd += ["-i", cover_path, "-map", "0:a", "-map", "2:v", "-map_metadata", "1",
                           "-c:a", "aac", "-b:a", "64k", "-c:v", "copy", "-disposition:v", "attached_pic", audio_out]
            else:
                ff_cmd += ["-map_metadata", "1", "-c:a", "aac", "-b:a", "64k", audio_out]
            subprocess.run(ff_cmd, capture_output=True)
        else:
            audio_out = str(dest_dir / f"{base_name}-音频 Audio.mp3")
            shutil.copy2(merged_mp3, audio_out)
        
        # 复制原始文件
        ext = Path(filepath).suffix
        shutil.copy2(filepath, str(dest_dir / f"{base_name}-原始 Source{ext}"))
        
        # 保存提取txt
        txt_out = dest_dir / f"{base_name}-转换 Text.txt"
        with open(txt_out, "w", encoding="utf-8") as f:
            for ch_title, ch_text in chapters:
                f.write(f"# {ch_title}\n\n{ch_text}\n\n")
        
        total_seconds = int(time.time() - start_time)
        total_time_str = format_time(total_seconds)
        
        update_status(step=3, real_pct=100, progress_detail=f"Complete! Saved to: {dest_dir}", eta="Done", total_time=total_time_str)
        status["output_file"] = audio_out
        
        # 历史记录
        try:
            history_file = USER_DATA_DIR / "history.json"
            history = []
            if history_file.exists():
                history = json.loads(history_file.read_text(encoding="utf-8"))
            history.insert(0, {
                "title": book_info["title"], "author": book_info["author"],
                "voice": voice, "chars": book_info["chars"], "chapters": book_info["chapters"],
                "duration": total_time_str, "output": audio_out,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            history = history[:50]
            history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except: pass
        
        # 转换成功后清理缓存
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except: pass
        
    except Exception as e:
        import traceback
        status["error"] = f"Error: {e}"
        traceback.print_exc()
    finally:
        status["running"] = False
# ============ Web UI ============
HTML = r'''<!DOCTYPE html>
<html lang="zh-CN" data-theme="light"><head><meta charset="UTF-8"><title>AudioBookify</title>
<style>
:root { --bg-grad: linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%); --panel: #fff; --text: #2d3436; --sub: #636e72; --primary: #0984e3; --accent: #00b894; --border: #eef0f3; --input-bg: #fafbfc; --info-bg: #f0f8ff; --info-border: #bee3f8; --hint: #74b9ff; --tag-color: #6c5ce7; }
[data-theme="dark"] { --bg-grad: linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%); --panel: #1f1f35; --text: #eee; --sub: #a0a0b0; --primary: #74b9ff; --accent: #2ed573; --border: #2a2a4a; --input-bg: #16162a; --info-bg: #1a2438; --info-border: #2a4a7a; --hint: #88c0ff; --tag-color: #c490ff; }
[data-theme="sepia"] { --bg-grad: linear-gradient(135deg,#f5e8d3 0%,#e8d5a8 100%); --panel: #fdf6e3; --text: #5c4a2a; --sub: #8a7050; --primary: #b58900; --accent: #859900; --border: #ebe0c5; --input-bg: #faf3df; --info-bg: #f5edd5; --info-border: #c8b88a; --hint: #c8a456; --tag-color: #6c71c4; }
[data-theme="ocean"] { --bg-grad: linear-gradient(135deg,#0c4a6e 0%,#0e7490 100%); --panel: #ecfeff; --text: #164e63; --sub: #155e75; --primary: #0891b2; --accent: #06b6d4; --border: #cffafe; --input-bg: #f0fdff; --info-bg: #e0f7fa; --info-border: #67e8f9; --hint: #0e7490; --tag-color: #0369a1; }
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei','Segoe UI',sans-serif;background:var(--bg-grad);color:var(--text);min-height:100vh;padding:24px;transition:all .3s}
.container{max-width:920px;margin:0 auto}
h1{text-align:center;margin-bottom:6px;color:var(--text);font-size:28px;font-weight:700}
.subtitle{text-align:center;color:var(--sub);margin-bottom:14px;font-size:13px}
.theme-bar{text-align:center;margin-bottom:18px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap}
.theme-btn{padding:5px 12px;border:1px solid var(--border);background:var(--panel);color:var(--sub);border-radius:16px;font-size:11px;cursor:pointer;transition:all .2s}
.theme-btn:hover,.theme-btn.active{border-color:var(--primary);color:var(--primary);background:var(--info-bg)}
.panel{background:var(--panel);border-radius:16px;padding:22px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,.06);border:1px solid var(--border)}
.panel h2{color:var(--primary);margin-bottom:12px;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}
.drop-zone{border:2px dashed var(--border);border-radius:12px;padding:36px 20px;text-align:center;cursor:pointer;transition:all .25s;background:var(--input-bg)}
.drop-zone:hover,.drop-zone.dragover{border-color:var(--primary);background:var(--info-bg)}
.drop-zone .icon{font-size:36px;margin-bottom:8px}
.drop-zone p{color:var(--sub);font-size:13px}
.drop-zone .filename{color:var(--accent);font-size:13px;margin-top:8px;font-weight:600}
.formats{color:var(--hint);font-size:11px;margin-top:8px;text-align:center;font-weight:500}
.tip{font-size:11px;color:var(--sub);margin-top:6px;line-height:1.5;opacity:.85}
.form-group{margin-bottom:10px}
.form-group label{display:block;margin-bottom:4px;color:var(--sub);font-size:12px;font-weight:500}
select,input{width:100%;padding:9px 11px;border-radius:8px;border:1px solid var(--border);background:var(--input-bg);color:var(--text);font-size:13px;transition:border .2s}
select:focus,input:focus{outline:none;border-color:var(--primary)}
.row{display:flex;gap:10px}.row .form-group{flex:1}
.btn{display:block;width:100%;padding:13px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;transition:all .2s}
.btn-convert{background:linear-gradient(135deg,var(--primary),var(--accent));color:white}
.btn-convert:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 4px 16px rgba(9,132,227,.3)}
.btn-convert:disabled{opacity:.5;cursor:not-allowed}
.book-info{background:var(--info-bg);border-radius:10px;padding:12px 16px;margin-bottom:14px;display:none;border:1px solid var(--info-border)}
.book-info.active{display:block}
.book-info h3{font-size:13px;color:var(--primary);margin-bottom:8px}
.book-info .stats{display:flex;gap:14px;flex-wrap:wrap}
.book-info .stat{font-size:12px;color:var(--text)}
.book-info .stat span{font-weight:600;color:var(--primary)}
.progress-panel{display:none}.progress-panel.active{display:block}
.steps{display:flex;gap:6px;margin-bottom:14px}
.step{flex:1;padding:9px;border-radius:8px;background:var(--input-bg);border:1px solid var(--border);text-align:center;font-size:11px;transition:all .25s}
.step.active{border-color:var(--primary);background:var(--info-bg);color:var(--primary)}
.step.done{border-color:var(--accent);background:var(--info-bg);color:var(--accent)}
.step .num{font-size:17px;font-weight:700;margin-bottom:2px}
.step.active .num{color:var(--primary)}.step.done .num{color:var(--accent)}
.progress-bar{height:6px;background:var(--border);border-radius:3px;overflow:hidden;margin:10px 0}
.progress-bar .fill{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent));transition:width .4s;border-radius:3px}
.progress-info{display:flex;justify-content:space-between;font-size:12px;color:var(--sub)}
.progress-detail{font-size:12px;color:var(--accent);margin-top:6px}
.eta{font-size:12px;color:var(--tag-color);margin-top:4px;font-weight:500}
.result{margin-top:14px;padding:16px;border-radius:10px;background:var(--info-bg);border:1px solid var(--accent);display:none}
.result.active{display:block}.result h3{color:var(--accent);margin-bottom:6px;font-size:14px}
.result p{color:var(--text);font-size:13px;word-break:break-all}
.preview-btn{background:transparent;color:var(--primary);border:1px solid var(--primary);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;margin-top:6px}
.preview-btn:hover{background:var(--info-bg)}
audio{width:100%;margin-top:6px;height:32px}
.modal-bg{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:100;align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:var(--panel);border-radius:16px;padding:30px;max-width:500px;width:90%}
.modal h2{color:var(--primary);margin-bottom:14px}
.modal p{color:var(--sub);font-size:13px;margin-bottom:10px;line-height:1.6}
.modal .archive-rule{background:var(--info-bg);padding:12px;border-radius:8px;font-size:12px;font-family:monospace;margin:10px 0;color:var(--text)}
.banner{background:#fff3cd;color:#856404;padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:12px;display:none}
.banner.show{display:block}
[data-theme="dark"] .banner{background:#3d3520;color:#ffd966}
</style></head><body><div class="container">
<h1>📖 AudioBookify</h1>
<p class="subtitle">Drag, Drop, Convert · 拖入 → 自动转换 · Multi-language Voices</p>
<div class="theme-bar">
<button class="theme-btn" data-t="light">☀️ Light</button>
<button class="theme-btn" data-t="dark">🌙 Dark</button>
<button class="theme-btn" data-t="sepia">📜 Sepia</button>
<button class="theme-btn" data-t="ocean">🌊 Ocean</button>
<button class="theme-btn" onclick="toggleHistory()">📚 History</button>
<button class="theme-btn" onclick="openSettings()">⚙️ Settings</button>
</div>

<div class="banner" id="ffmpegBanner">⚙️ Setting up FFmpeg... <span id="ffmpegProgress">0%</span></div>

<div class="panel"><h2>📂 Import / 导入</h2>
<div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
<div class="icon">📁</div>
<p>Drag & drop file here, or click to browse / 拖拽或点击选择</p>
<p class="filename" id="fileName"></p>
<input type="file" id="fileInput" accept=".epub,.txt,.pdf,.docx,.doc,.mobi,.azw3" style="display:none" onchange="handleFile(this)">
</div>
<p class="formats">Supported / 支持: epub · txt · pdf · docx · mobi · azw3</p>
<p class="tip">💡 .txt converts directly. Other formats are converted to text first, then to audio. / .txt直接转换；其他格式先转文本再转音频</p>
</div>

<div class="book-info" id="bookInfo">
<h3>📊 Book Overview / 书籍概览</h3>
<div class="stats">
<div class="stat">Title: <span id="biTitle">-</span></div>
<div class="stat">Author: <span id="biAuthor">-</span></div>
<div class="stat">Chapters: <span id="biChapters">-</span></div>
<div class="stat">Words: <span id="biChars">-</span></div>
<div class="stat">Est. Duration: <span id="biDuration">-</span></div>
</div></div>

<div class="panel"><h2>🎙️ Voice / 语音</h2>
<div class="row">
<div class="form-group"><label>Language / 语言</label><select id="voiceCategory" onchange="updateVoices()">__VOICE_OPTIONS__</select></div>
<div class="form-group"><label>Speaker / 音色</label><select id="voiceSelect"></select></div>
</div>
<div class="form-group" style="margin-top:6px"><label>Speed / 语速</label><select id="rateSelect">
<option value="-25%">Slow -25% / 慢速</option>
<option value="-10%">Slower -10% / 略慢</option>
<option value="+0%" selected>Normal / 正常</option>
<option value="+10%">Faster +10% / 略快</option>
<option value="+25%">Fast +25% / 快速</option>
<option value="+50%">Very Fast +50% / 极快</option>
</select></div>
<button class="preview-btn" onclick="previewVoice()">▶ Preview / 试听</button>
<audio id="previewAudio" controls style="display:none"></audio>
</div>

<div class="panel"><h2>💾 Output / 输出</h2>
<div class="form-group"><label>Format / 格式</label><select id="outputFormat">
<option value="m4b">M4B with chapters (recommended) / 带章节(推荐)</option>
<option value="mp3">MP3</option>
</select></div>
<p class="tip" id="outputDirHint">📂 Save to: ...</p>
</div>

<button class="btn btn-convert" id="convertBtn" onclick="startConversion()">▶ Start / 开始转换</button>

<div class="panel progress-panel" id="progressPanel">
<h2>⏳ Progress / 进度</h2>
<div class="steps">
<div class="step" id="step1"><div class="num">1</div>Parse</div>
<div class="step" id="step2"><div class="num">2</div>Audio</div>
<div class="step" id="step3"><div class="num">3</div>Archive</div>
</div>
<div class="progress-info"><span id="stepName">Waiting...</span><span id="pctText">0%</span></div>
<div class="progress-bar"><div class="fill" id="progressFill" style="width:0%"></div></div>
<p class="progress-detail" id="progressDetail"></p>
<p class="eta" id="etaText"></p>
</div>

<div class="result" id="resultBox"><h3>✅ Complete!</h3><p id="resultText"></p><p id="resultTime" style="color:var(--tag-color);font-weight:600;margin-top:6px"></p></div>

<div class="panel" id="historyPanel" style="display:none"><h2>📚 History</h2><div id="historyList" style="font-size:12px;color:var(--sub)"></div></div>
</div>

<div class="modal-bg" id="welcomeModal"><div class="modal">
<h2>👋 Welcome / 欢迎使用</h2>
<p>AudioBookify converts your ebooks into chaptered audiobooks. / 将电子书转换为带章节的有声书。</p>
<p><b>Output Location / 输出位置:</b></p>
<div style="display:flex;gap:8px;margin-bottom:10px"><input type="text" id="setupOutputDir" style="flex:1"><button class="theme-btn" onclick="browseFolderForSetup()" style="white-space:nowrap;padding:8px 14px">📁 Browse / 浏览</button></div>
<p><b>Files Will Be Organized As / 文件将按以下结构归档:</b></p>
<div class="archive-rule">📁 BookTitle-Author/<br>　├── BookTitle-Author-原始 Source.epub<br>　├── BookTitle-Author-音频 Audio.m4b<br>　├── BookTitle-Author-转换 Text.txt<br>　└── BookTitle-Author-封面 Cover.jpg</div>
<p style="font-size:11px">For non-domestic authors / 国外作者会自动添加国家: <code>BookTitle-Author[Country]</code></p>
<button class="btn btn-convert" onclick="finishSetup()" style="margin-top:14px">Get Started / 开始使用</button>
</div></div>

<div class="modal-bg" id="settingsModal"><div class="modal">
<h2>⚙️ Settings / 设置</h2>
<div class="form-group"><label>Output Directory / 输出目录</label><div style="display:flex;gap:8px"><input type="text" id="settingsOutput" style="flex:1"><button class="theme-btn" onclick="browseFolderForSettings()" style="white-space:nowrap;padding:8px 14px">📁 Browse / 浏览</button></div></div>
<button class="btn btn-convert" onclick="saveSettings()">Save / 保存</button>
<button class="theme-btn" onclick="closeSettings()" style="margin-top:10px;width:100%">Cancel / 取消</button>
</div></div>
'''
HTML_JS = r'''
<script>
const voices=__VOICES_JSON__;
const cfg=__CONFIG_JSON__;
let selectedFile=null;
// Init theme
document.documentElement.setAttribute("data-theme",cfg.theme||"light");
document.querySelectorAll(".theme-btn[data-t]").forEach(b=>{
  if(b.dataset.t===(cfg.theme||"light"))b.classList.add("active");
  b.addEventListener("click",()=>{
    document.documentElement.setAttribute("data-theme",b.dataset.t);
    document.querySelectorAll(".theme-btn[data-t]").forEach(x=>x.classList.remove("active"));
    b.classList.add("active");
    fetch("/setting",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({theme:b.dataset.t})});
  });
});
// First run setup
// Welcome modal disabled - user can configure via Settings if needed
if(false&&cfg.first_run){document.getElementById("setupOutputDir").value=cfg.output_dir;document.getElementById("welcomeModal").classList.add("show")}
function finishSetup(){const v=document.getElementById("setupOutputDir").value.trim();fetch("/setting",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({output_dir:v,first_run:false})}).then(()=>{document.getElementById("welcomeModal").classList.remove("show");loadHint()})}
function browseFolderForSetup(){fetch("/browse_folder").then(r=>r.json()).then(d=>{if(d.path)document.getElementById("setupOutputDir").value=d.path})}
function browseFolderForSettings(){fetch("/browse_folder").then(r=>r.json()).then(d=>{if(d.path)document.getElementById("settingsOutput").value=d.path})}
function openSettings(){document.getElementById("settingsOutput").value=cfg.output_dir;document.getElementById("settingsModal").classList.add("show")}
function pickFolderSetup(){fetch("/pick_folder",{method:"POST"}).then(r=>r.json()).then(d=>{if(d.success&&d.path)document.getElementById("setupOutputDir").value=d.path})}
function pickFolderSettings(){fetch("/pick_folder",{method:"POST"}).then(r=>r.json()).then(d=>{if(d.success&&d.path)document.getElementById("settingsOutput").value=d.path})}
function closeSettings(){document.getElementById("settingsModal").classList.remove("show")}
function saveSettings(){const v=document.getElementById("settingsOutput").value.trim();fetch("/setting",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({output_dir:v})}).then(()=>{cfg.output_dir=v;closeSettings();loadHint()})}
function loadHint(){document.getElementById("outputDirHint").textContent="📂 Save to / 保存到: "+cfg.output_dir+"/[BookTitle-Author]/"}
loadHint();
function updateVoices(){const c=document.getElementById("voiceCategory").value,s=document.getElementById("voiceSelect");s.innerHTML="";for(const[id,name]of Object.entries(voices[c])){const o=document.createElement("option");o.value=id;o.textContent=name;s.appendChild(o)}}updateVoices();
const dz=document.getElementById("dropZone");
dz.addEventListener("dragover",e=>{e.preventDefault();dz.classList.add("dragover")});
dz.addEventListener("dragleave",()=>dz.classList.remove("dragover"));
dz.addEventListener("drop",e=>{e.preventDefault();dz.classList.remove("dragover");if(e.dataTransfer.files.length)handleFileObj(e.dataTransfer.files[0])});
function handleFile(i){if(i.files.length)handleFileObj(i.files[0])}
function handleFileObj(f){selectedFile=f;document.getElementById("fileName").textContent=f.name+" ("+(f.size>1048576?(f.size/1048576).toFixed(1)+" MB":(f.size/1024).toFixed(0)+" KB")+")";
const fd=new FormData();fd.append("file",f);
fetch("/analyze",{method:"POST",body:fd}).then(r=>r.json()).then(d=>{
if(d.success){const bi=d.info;document.getElementById("bookInfo").classList.add("active");
document.getElementById("biTitle").textContent=bi.title||"-";
document.getElementById("biAuthor").textContent=bi.author||"Unknown";
document.getElementById("biChapters").textContent=bi.chapters||"-";
document.getElementById("biChars").textContent=bi.chars?bi.chars.toLocaleString():"-";
const mins=Math.round((bi.chars||0)/250);
document.getElementById("biDuration").textContent=mins>60?Math.floor(mins/60)+"h "+mins%60+"m":mins+" min";
}})}
function previewVoice(){const v=document.getElementById("voiceSelect").value;fetch("/preview?voice="+v).then(r=>r.blob()).then(b=>{const a=document.getElementById("previewAudio");a.src=URL.createObjectURL(b);a.style.display="block";a.play()})}
function startConversion(){if(!selectedFile){showToast("Please select a file first / 请先选择文件");return}
const btn=document.getElementById("convertBtn"),pp=document.getElementById("progressPanel"),rs=document.getElementById("resultBox");
btn.disabled=true;btn.textContent="Converting... / 转换中...";pp.classList.add("active");rs.classList.remove("active");
document.querySelectorAll(".step").forEach(s=>s.classList.remove("active","done"));
const fd=new FormData();fd.append("file",selectedFile);fd.append("voice",document.getElementById("voiceSelect").value);fd.append("format",document.getElementById("outputFormat").value);fd.append("rate",document.getElementById("rateSelect").value);
fetch("/convert",{method:"POST",body:fd}).then(r=>r.json()).then(d=>{if(d.success)pollStatus();else{showToast(d.error);btn.disabled=false;btn.textContent="▶ Start / 开始转换"}})}
function pollStatus(){fetch("/status").then(r=>r.json()).then(d=>{
const fill=document.getElementById("progressFill"),stepName=document.getElementById("stepName"),pct=document.getElementById("pctText"),detail=document.getElementById("progressDetail"),eta=document.getElementById("etaText");
for(let i=1;i<=3;i++){const el=document.getElementById("step"+i);el.classList.remove("active","done");if(i<d.step)el.classList.add("done");else if(i===d.step)el.classList.add("active")}
const realPct=d.real_pct||0;
fill.style.width=realPct+"%";pct.textContent=realPct+"%";
stepName.textContent=d.step_name||"Processing...";
detail.textContent=d.progress_detail||"";
eta.textContent=d.eta?"ETA: "+d.eta:"";
if(d.running){setTimeout(pollStatus,1500)}else{
const btn=document.getElementById("convertBtn");btn.disabled=false;btn.textContent="▶ Start / 开始转换";
if(d.output_file){const rs=document.getElementById("resultBox");rs.classList.add("active");document.getElementById("resultText").textContent="Saved / 已保存: "+d.output_file;document.getElementById("resultTime").textContent="⏱️ Total time / 总耗时: "+(d.total_time||"-");fill.style.width="100%";pct.textContent="100%";eta.textContent="Done";document.querySelectorAll(".step").forEach(s=>{s.classList.remove("active");s.classList.add("done")})}
else if(d.error){detail.textContent="Error: "+d.error;eta.textContent=""}}})}

function showToast(msg){let t=document.getElementById("vbToast");if(!t){t=document.createElement("div");t.id="vbToast";t.style.cssText="position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#ff7675;color:#fff;padding:12px 22px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.2);z-index:9999;font-size:14px;font-weight:500;transition:opacity .3s";document.body.appendChild(t)}t.textContent=msg;t.style.opacity="1";clearTimeout(t._tm);t._tm=setTimeout(()=>{t.style.opacity="0"},3500)}
function toggleHistory(){const p=document.getElementById("historyPanel");if(p.style.display==="none"){p.style.display="block";loadHistory()}else p.style.display="none"}
function loadHistory(){fetch("/history").then(r=>r.json()).then(d=>{
const list=document.getElementById("historyList");
if(!d.length){list.innerHTML='<p style="color:#999;text-align:center;padding:20px">No history yet / 暂无记录</p>';return}
list.innerHTML=d.map(h=>'<div style="padding:10px;border-bottom:1px solid var(--border)">'+'<div style="font-weight:600;color:var(--text)">'+h.title+(h.author?" - "+h.author:"")+"</div>"+'<div style="color:var(--sub);margin-top:4px">'+h.chars.toLocaleString()+" chars · "+h.chapters+" chapters · "+h.duration+" · "+h.timestamp+"</div></div>").join("")})}
// Check ffmpeg status
function checkFFmpeg(){fetch("/ffmpeg_status").then(r=>r.json()).then(d=>{
if(d.downloading){document.getElementById("ffmpegBanner").classList.add("show");document.getElementById("ffmpegProgress").textContent=d.progress+"%";setTimeout(checkFFmpeg,1000)}
else if(d.error){document.getElementById("ffmpegBanner").innerHTML='⚠️ FFmpeg setup failed: '+d.error;document.getElementById("ffmpegBanner").classList.add("show")}
else{document.getElementById("ffmpegBanner").classList.remove("show")}
})}
checkFFmpeg();
</script></body></html>'''
# ============ Flask 路由 ============
@app.route("/")
def index():
    voice_options = "".join(f'<option value="{c}">{c}</option>' for c in VOICES.keys())
    page = HTML.replace("__VOICE_OPTIONS__", voice_options)
    page += HTML_JS.replace("__VOICES_JSON__", json.dumps(VOICES, ensure_ascii=False)).replace("__CONFIG_JSON__", json.dumps(config, ensure_ascii=False))
    return page

@app.route("/browse_folder")
def browse_folder():
    """打开本地文件夹选择对话框"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="Select Output Folder / 选择输出目录")
        root.destroy()
        return jsonify({"path": folder or ""})
    except Exception as e:
        return jsonify({"path": "", "error": str(e)})

@app.route("/setting", methods=["POST"])
def setting():
    global config, OUTPUT_DIR
    data = request.json or {}
    config.update(data)
    if "output_dir" in data and data["output_dir"]:
        OUTPUT_DIR = Path(data["output_dir"])
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_config(config)
    return jsonify({"success": True})

@app.route("/ffmpeg_status")
def ffmpeg_st():
    global FFMPEG
    FFMPEG = get_ffmpeg() if not FFMPEG else FFMPEG
    return jsonify({"downloading": ffmpeg_status["downloading"], "progress": ffmpeg_status["progress"], "error": ffmpeg_status["error"], "ready": bool(FFMPEG)})

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("file")
    if not file: return jsonify({"success": False})
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
    file.save(tmp.name)
    tmp.close()
    try:
        meta = parse_filename_meta(file.filename)
        chapters, book_meta = extract_text_and_chapters(tmp.name)
        info = {
            "title": meta.get("title") or book_meta.get("title", "Unknown"),
            "author": meta.get("author") or book_meta.get("author", ""),
            "chapters": len(chapters),
            "chars": sum(len(c[1]) for c in chapters),
        }
        return jsonify({"success": True, "info": info})
    finally:
        try: os.unlink(tmp.name)
        except: pass

@app.route("/preview")
def preview():
    voice = request.args.get("voice", "zh-CN-XiaoxiaoNeural")
    if "zh-" in voice: text = "你好，这是音色试听。"
    elif "ja-" in voice: text = "こんにちは、これは音声プレビューです。"
    elif "ko-" in voice: text = "안녕하세요, 이것은 음성 미리보기입니다."
    elif "fr-" in voice: text = "Bonjour, ceci est un aperçu de la voix."
    elif "de-" in voice: text = "Hallo, dies ist eine Sprachvorschau."
    elif "es-" in voice: text = "Hola, esta es una vista previa."
    elif "it-" in voice: text = "Ciao, questa è un'anteprima vocale."
    elif "pt-" in voice: text = "Olá, esta é uma prévia de voz."
    elif "ru-" in voice: text = "Привет, это превью голоса."
    elif "ar-" in voice: text = "مرحبا، هذه معاينة صوتية."
    elif "hi-" in voice: text = "नमस्ते, यह एक आवाज़ पूर्वावलोकन है।"
    elif "vi-" in voice: text = "Xin chào, đây là bản xem trước giọng nói."
    elif "th-" in voice: text = "สวัสดี นี่คือตัวอย่างเสียง"
    else: text = "Hello, this is a voice preview."
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(tts_to_file(text, voice, tmp.name))
        return send_file(tmp.name, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/convert", methods=["POST"])
def convert():
    global status
    if status["running"]:
        return jsonify({"success": False, "error": "A conversion is running / 已有任务运行中"})
    if not FFMPEG:
        return jsonify({"success": False, "error": "FFmpeg not ready, please wait..."})
    file = request.files.get("file")
    voice = request.form.get("voice", "zh-CN-XiaoxiaoNeural")
    output_format = request.form.get("format", "m4b")
    rate = request.form.get("rate", "+0%")
    if not file:
        return jsonify({"success": False, "error": "No file"})
    
    # 保存到临时
    upload_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
    file.save(upload_tmp.name)
    upload_tmp.close()
    
    status.clear()
    status.update({
        "running": True, "step": 0, "step_name": "Starting...",
        "real_pct": 0, "progress_detail": "", "chapters_done": 0,
        "chapters_total": 0, "output_file": "", "error": "",
        "book_info": None, "eta": "", "start_time": time.time(),
        "total_time": "", "rate": rate, "current_book_id": ""
    })
    
    def run_with_orig_name():
        orig_path = os.path.join(tempfile.gettempdir(), file.filename)
        try:
            shutil.copy2(upload_tmp.name, orig_path)
            run_conversion(orig_path, voice, output_format, rate)
        finally:
            try: os.unlink(upload_tmp.name)
            except: pass
            try: os.unlink(orig_path)
            except: pass
    
    threading.Thread(target=run_with_orig_name, daemon=True).start()
    return jsonify({"success": True})

@app.route("/status")
def get_status():
    return jsonify(status)


@app.route("/pick_folder", methods=["POST"])
def pick_folder():
    """打开本地文件夹选择对话框"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="Select Output Folder / 选择输出目录")
        root.destroy()
        if path:
            return jsonify({"success": True, "path": path})
        return jsonify({"success": False, "path": ""})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/history")
def get_history():
    history_file = USER_DATA_DIR / "history.json"
    if not history_file.exists():
        return jsonify([])
    try:
        return jsonify(json.loads(history_file.read_text(encoding="utf-8")))
    except:
        return jsonify([])

# ============ 启动 ============
def open_browser_delayed():
    time.sleep(1.5)
    import webbrowser
    webbrowser.open("http://127.0.0.1:7860")

def ensure_ffmpeg_async():
    """后台下载 ffmpeg"""
    global FFMPEG
    if FFMPEG: return
    threading.Thread(target=lambda: (download_ffmpeg(), setattr(sys.modules[__name__], "FFMPEG", get_ffmpeg())), daemon=True).start()

def _start_flask_in_thread(port):
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)

def _setup_tray():
    """系统托盘图标"""
    try:
        import pystray
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    
    img = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 12, 56, 56], radius=4, fill=(9, 132, 227, 255))
    d.rounded_rectangle([14, 18, 50, 50], radius=2, fill=(255, 255, 255, 255))
    
    def open_app(icon, item):
        import webbrowser
        webbrowser.open("http://127.0.0.1:7860")
    
    def open_folder(icon, item):
        try:
            os.startfile(str(USER_DATA_DIR))
        except: pass
    
    def open_output(icon, item):
        try:
            os.startfile(str(OUTPUT_DIR))
        except: pass
    
    def quit_app(icon, item):
        icon.stop()
        os._exit(0)
    
    menu = pystray.Menu(
        pystray.MenuItem("Open Panel / 打开面板", open_app, default=True),
        pystray.MenuItem("Open Output Folder / 输出文件夹", open_output),
        pystray.MenuItem("Open Data Folder / 数据目录", open_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit / 退出", quit_app)
    )
    return pystray.Icon("AudioBookify", img, "AudioBookify", menu)

if __name__ == "__main__":
    port = 7860
    
    # 后台下载 ffmpeg
    ensure_ffmpeg_async()
    
    # 自动打开浏览器
    threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    # 直接在主线程运行Flask（不使用系统托盘）
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print("\n✓ Flask 服务已启动，访问地址: http://127.0.0.1:7860")
    print("✓ 请勿关闭此窗口\n")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)