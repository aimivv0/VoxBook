"""
Ebook2Audiobook v1.0 - 完全重写版
- 直接使用 edge-tts (不依赖 epub2tts-edge.exe)
- 真实进度跟踪
- 章节级转换
- 自动Archive整理
"""
import os, sys, json, threading, subprocess, tempfile, shutil, re, time, asyncio
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file

app = Flask(__name__)

# ============ 配置 ============
import sys as _sys
if getattr(_sys, "frozen", False):
    BASE_DIR = Path(_sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
EBOOK_DIR = BASE_DIR / "ebooks"
OUTPUT_DIR = BASE_DIR / "output"
EBOOK_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

PYTHON_EXE = sys.executable
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
EBOOK_CONVERT = None
for p in [r"C:\Program Files\Calibre2\ebook-convert.exe", r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"]:
    if os.path.exists(p):
        EBOOK_CONVERT = p
        break

# ============ 状态 ============
status = {
    "running": False, "step": 0, "step_name": "",
    "real_pct": 0, "progress_detail": "",
    "chapters_done": 0, "chapters_total": 0,
    "output_file": "", "error": "",
    "book_info": None, "eta": "",
    "start_time": 0, "total_time": "",
    "rate": "+0%"
}

# ============ 语音列表 ============
VOICES = {
    "Chinese Female": {
        "zh-CN-XiaoxiaoNeural": "Xiaoxiao (warm narrator) ★",
        "zh-CN-XiaoyiNeural": "Xiaoyi (lively)",
        "zh-CN-liaoning-XiaobeiNeural": "Xiaobei (Northeast dialect)",
        "zh-CN-shaanxi-XiaoniNeural": "Xiaoni (Shaanxi dialect)",
        "zh-TW-HsiaoChenNeural": "HsiaoChen (Taiwan)",
        "zh-TW-HsiaoYuNeural": "HsiaoYu (Taiwan, gentle)",
        "zh-HK-HiuGaaiNeural": "HiuGaai (Cantonese)",
        "zh-HK-HiuMaanNeural": "HiuMaan (Cantonese, soft)",
    },
    "Chinese Male": {
        "zh-CN-YunyangNeural": "Yunyang (professional anchor) ★",
        "zh-CN-YunxiNeural": "Yunxi (sunny)",
        "zh-CN-YunjianNeural": "Yunjian (energetic)",
        "zh-CN-YunxiaNeural": "Yunxia (cute)",
        "zh-TW-YunJheNeural": "YunJhe (Taiwan)",
        "zh-HK-WanLungNeural": "WanLung (Cantonese)",
    },
    "English Female": {
        "en-US-AvaNeural": "Ava (newest, natural) ★Best",
        "en-US-JennyNeural": "Jenny (warm narrator)",
        "en-US-AriaNeural": "Aria (professional)",
        "en-US-EmmaNeural": "Emma (conversational)",
        "en-US-MichelleNeural": "Michelle (friendly)",
        "en-GB-SoniaNeural": "Sonia (British)",
        "en-GB-LibbyNeural": "Libby (British warm)",
    },
    "English Male": {
        "en-US-AndrewNeural": "Andrew (newest, natural) ★Best",
        "en-US-BrianNeural": "Brian (calm narrator)",
        "en-US-GuyNeural": "Guy (news)",
        "en-US-ChristopherNeural": "Christopher (clear)",
        "en-US-EricNeural": "Eric (mature)",
        "en-GB-RyanNeural": "Ryan (British)",
        "en-GB-ThomasNeural": "Thomas (British warm)",
    },
}
# ============ 工具函数 ============

def parse_filename_meta(filename):
    """从文件名Parse 书名(作者)"""
    name = Path(filename).stem
    info = {"title": name, "author": "", "country": ""}
    # 匹配 "书名 (作者)" 或 "书名（作者）"
    m = re.match(r'^(.+?)\s*[\(（]([^()（）]+)[\)）]', name)
    if m:
        title = m.group(1).strip()
        author = m.group(2).strip()
        # 清理常见噪音
        author = re.sub(r'(z-library|1lib|z-lib)\..*', '', author, flags=re.I).strip(' ,，.')
        if author and not re.search(r'(z-library|1lib|z-lib|library)', author, re.I):
            info["title"] = title
            info["author"] = author
    return info

def extract_text_and_chapters(filepath):
    """提取文本和章节信息。返回 [(chapter_title, text), ...]"""
    ext = Path(filepath).suffix.lower()
    chapters = []
    
    if ext == '.epub':
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            book = epub.read_epub(filepath)
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                # 找标题
                title = None
                for tag in ['h1', 'h2', 'h3']:
                    found = soup.find(tag)
                    if found:
                        title = found.get_text(strip=True)
                        break
                # 提取段落文本
                paras = []
                for p in soup.find_all(['p', 'div']):
                    t = p.get_text(separator=' ', strip=True)
                    if t and len(t) > 10:
                        paras.append(t)
                text = '\n\n'.join(paras)
                if text.strip():
                    chapters.append((title or f"Chapter {len(chapters)+1}", text))
            
            # 元数据
            meta = {"title": "", "author": ""}
            try:
                t = book.get_metadata('DC', 'title')
                if t: meta["title"] = t[0][0]
                a = book.get_metadata('DC', 'creator')
                if a: meta["author"] = a[0][0]
            except: pass
            return chapters, meta
        except Exception as e:
            print(f"epub parse error: {e}")
            return [], {}
    
    elif ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # 用章节标记分割
        parts = re.split(r'\n(?=(?:第[一二三四五六七八九十百千零\d]+[章节回]|Chapter\s+\d+|CHAPTER\s+\d+))', content)
        for part in parts:
            part = part.strip()
            if not part: continue
            lines = part.split('\n', 1)
            title = lines[0][:50] if len(lines) > 1 else f"Chapter {len(chapters)+1}"
            text = lines[1] if len(lines) > 1 else lines[0]
            if len(text.strip()) > 50:
                chapters.append((title, text))
        if not chapters:
            # 没有章节标记，按段落分块（每5000 chars一段）
            chunk_size = 5000
            for i in range(0, len(content), chunk_size):
                chapters.append((f"Part {i//chunk_size+1}", content[i:i+chunk_size]))
        return chapters, {}
    
    else:
        # 用 Calibre 转 txt
        if EBOOK_CONVERT:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
                txt_path = tmp.name
            try:
                subprocess.run(
                    [EBOOK_CONVERT, filepath, txt_path, "--txt-output-encoding=utf-8"],
                    capture_output=True, timeout=300
                )
                if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
                    return extract_text_and_chapters(txt_path)
            finally:
                try: os.unlink(txt_path)
                except: pass
        return [], {}

def split_text_for_tts(text, max_len=2000):
    """将长文本分割为TTS可处理的小块（按句子）"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    # 按段落分
    paras = text.split('\n\n')
    current = ""
    for para in paras:
        if len(current) + len(para) < max_len:
            current += "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > max_len:
                # 段落本身太长，按句子分
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
    """用 edge-tts 把文本生成MP3"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

def extract_cover(filepath):
    """从epub中提取封面图片"""
    if not str(filepath).lower().endswith(".epub"):
        return None
    try:
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(str(filepath))
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER or "cover" in (item.get_name() or "").lower():
                if item.media_type and item.media_type.startswith("image/"):
                    ext = ".jpg" if "jpeg" in item.media_type or "jpg" in item.media_type else ".png"
                    cover_path = os.path.join(tempfile.gettempdir(), f"cover_{int(time.time())}{ext}")
                    with open(cover_path, "wb") as f:
                        f.write(item.get_content())
                    return cover_path
        # 退而求其次：找任何图片
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            ext = ".jpg" if "jpeg" in (item.media_type or "") else ".png"
            cover_path = os.path.join(tempfile.gettempdir(), f"cover_{int(time.time())}{ext}")
            with open(cover_path, "wb") as f:
                f.write(item.get_content())
            return cover_path
    except Exception as e:
        print(f"Cover extract failed: {e}")
    return None

def format_time(secs):
    if secs < 60: return f"{int(secs)}秒"
    elif secs < 3600: return f"{int(secs//60)}分{int(secs%60)}秒"
    else: return f"{int(secs//3600)}时{int((secs%3600)//60)}分"

def update_status(**kwargs):
    global status
    for k, v in kwargs.items():
        status[k] = v
# ============ 主转换流程 ============

def run_conversion(filepath, voice, output_format="m4b", rate="+0%"):
    """主转换流程"""
    global status
    work_dir = None
    try:
        start_time = time.time()
        status["start_time"] = start_time
        
        # ===== 步骤1: Parse文件 =====
        update_status(step=1, step_name="Parse文件", real_pct=5, progress_detail="Reading ebook...")
        
        # Parse元数据
        meta_from_name = parse_filename_meta(Path(filepath).name)
        chapters, meta_from_book = extract_text_and_chapters(filepath)
        
        if not chapters:
            status["error"] = "无法Parse文件内容"
            status["running"] = False
            return
        
        # 合并元数据，文件名优先（更准确）
        book_info = {
            "title": meta_from_name.get("title") or meta_from_book.get("title", "Unknown"),
            "author": meta_from_name.get("author") or meta_from_book.get("author", ""),
            "country": meta_from_name.get("country", ""),
            "chapters": len(chapters),
            "chars": sum(len(c[1]) for c in chapters),
        }
        status["book_info"] = book_info
        
        update_status(real_pct=15, progress_detail=f"已Parse {len(chapters)}  chapters, {book_info['chars']}  chars", chapters_total=len(chapters))
        
        # ===== 步骤2: Generate（章节级）=====
        update_status(step=2, step_name="Generate", real_pct=15, progress_detail="Starting TTS...")
        
        # 临时英文工作目录
        work_dir = tempfile.mkdtemp(prefix="tts_")
        chapter_files = []
        
        # 计算总块数用于进度
        chunks_per_chapter = []
        for ch_title, ch_text in chapters:
            chunks_per_chapter.append(split_text_for_tts(ch_text))
        total_chunks = sum(len(c) for c in chunks_per_chapter)
        chunks_done = 0
        
        # 获取异步事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for ch_idx, ((ch_title, ch_text), chunks) in enumerate(zip(chapters, chunks_per_chapter)):
            ch_audio_files = []
            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                chunk_file = os.path.join(work_dir, f"ch{ch_idx:04d}_pt{chunk_idx:04d}.mp3")
                try:
                    loop.run_until_complete(tts_to_file(chunk, voice, chunk_file, rate=rate))
                    if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 100:
                        ch_audio_files.append(chunk_file)
                except Exception as e:
                    status["error"] = f"TTS failed: {e}"
                    print(f"TTS error on chunk {ch_idx}/{chunk_idx}: {e}")
                
                chunks_done += 1
                # 更新进度（15-90%范围）
                pct = 15 + int((chunks_done / max(1, total_chunks)) * 75)
                elapsed = time.time() - start_time
                if chunks_done > 0:
                    eta_secs = (elapsed / chunks_done) * (total_chunks - chunks_done)
                    eta_str = format_time(eta_secs)
                else:
                    eta_str = "Estimating..."
                update_status(
                    real_pct=pct,
                    chapters_done=ch_idx + 1,
                    progress_detail=f"Ch. {ch_idx+1}/{len(chapters)} 章: {ch_title[:30]}",
                    eta=eta_str
                )
            
            # 合并本章的所有片段为一个章节文件
            if ch_audio_files:
                ch_file = os.path.join(work_dir, f"chapter_{ch_idx:04d}.mp3")
                if len(ch_audio_files) == 1:
                    shutil.move(ch_audio_files[0], ch_file)
                else:
                    # 用ffmpeg concat
                    list_file = os.path.join(work_dir, f"list_{ch_idx}.txt")
                    with open(list_file, 'w', encoding='utf-8') as f:
                        for af in ch_audio_files:
                            f.write(f"file '{af}'\n")
                    subprocess.run(
                        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", ch_file],
                        capture_output=True
                    )
                    # 清理
                    for af in ch_audio_files:
                        try: os.unlink(af)
                        except: pass
                    try: os.unlink(list_file)
                    except: pass
                if os.path.exists(ch_file):
                    chapter_files.append((ch_title, ch_file))
        
        if not chapter_files:
            status["error"] = "No audio files generated"
            status["running"] = False
            return
        
        # ===== 步骤3: 合并并Archive =====
        update_status(step=3, step_name="合并Archive", real_pct=90, progress_detail="Merging chapters...")
        
        # 合并所有章节为一个mp3
        merged_mp3 = os.path.join(work_dir, "book.mp3")
        if len(chapter_files) == 1:
            shutil.copy2(chapter_files[0][1], merged_mp3)
        else:
            list_file = os.path.join(work_dir, "all_list.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                for _, cf in chapter_files:
                    f.write(f"file '{cf}'\n")
            result = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", merged_mp3], capture_output=True)
            if not os.path.exists(merged_mp3):
                err = result.stderr.decode("utf-8", errors="replace")[-300:] if result.stderr else "unknown"
                status["error"] = f"Audio merge failed: {err}"
                status["running"] = False
                return
        
        # 转换为目标Format
        update_status(real_pct=95, progress_detail="Packaging final file...")
        
        # 决定输出文件名：书名-作者[国家]
        title = book_info["title"]
        author = book_info["author"]
        country = book_info.get("country", "")
        if author:
            base_name = f"{title}-{author}[{country}]" if country else f"{title}-{author}"
        else:
            base_name = title
        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)[:120]
        
        # 创建Archive文件夹
        dest_dir = OUTPUT_DIR / base_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取封面
        cover_path = extract_cover(filepath)
        if cover_path and os.path.exists(cover_path):
            shutil.copy2(cover_path, str(dest_dir / f"{base_name}-封面{Path(cover_path).suffix}"))
        
        if output_format == "m4b":
            # 生成带章节的m4b
            audio_out = str(dest_dir / f"{base_name}-音频.m4b")
            # 生成章节元数据
            meta_file = os.path.join(work_dir, "chapters.txt")
            with open(meta_file, 'w', encoding='utf-8') as f:
                f.write(";FFMETADATA1\n")
                f.write(f"title={title}\n")
                if author: f.write(f"artist={author}\n")
                f.write(f"album={title}\n")
                # 章节标记
                cumulative_ms = 0
                for ch_title, ch_file in chapter_files:
                    # 获取时长
                    probe = subprocess.run([FFMPEG, "-i", ch_file], capture_output=True)
                    stderr_text = probe.stderr.decode("utf-8", errors="replace") if probe.stderr else ""
                    duration_match = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', stderr_text)
                    if duration_match:
                        h, m, s = duration_match.groups()
                        dur_ms = int((int(h)*3600 + int(m)*60 + float(s)) * 1000)
                    else:
                        dur_ms = 60000
                    f.write(f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={cumulative_ms}\nEND={cumulative_ms+dur_ms}\ntitle={ch_title}\n")
                    cumulative_ms += dur_ms
            
            # 构建ffmpeg命令，如果有封面则嵌入
            ff_cmd = [FFMPEG, "-y", "-i", merged_mp3, "-i", meta_file]
            if cover_path and os.path.exists(cover_path):
                ff_cmd += ["-i", cover_path, "-map", "0:a", "-map", "2:v", "-map_metadata", "1",
                           "-c:a", "aac", "-b:a", "64k", "-c:v", "copy", "-disposition:v", "attached_pic", audio_out]
            else:
                ff_cmd += ["-map_metadata", "1", "-c:a", "aac", "-b:a", "64k", audio_out]
            result = subprocess.run(ff_cmd, capture_output=True)
            if not os.path.exists(audio_out):
                # 简单转码不带章节
                subprocess.run(
                    [FFMPEG, "-y", "-i", merged_mp3, "-c:a", "aac", "-b:a", "64k", audio_out],
                    capture_output=True
                )
        else:
            # MP3
            audio_out = str(dest_dir / f"{base_name}-音频.mp3")
            shutil.copy2(merged_mp3, audio_out)
        
        # 复制原始文件 - 优先从电子书文件夹移出
        source_handled = False
        if EBOOK_DIR.exists():
            orig_stem = Path(filepath).stem
            for f in EBOOK_DIR.iterdir():
                if f.is_file() and f.stem == orig_stem:
                    ext = f.suffix
                    shutil.move(str(f), str(dest_dir / f"{base_name}-原始{ext}"))
                    source_handled = True
                    break
        if not source_handled:
            ext = Path(filepath).suffix
            shutil.copy2(filepath, str(dest_dir / f"{base_name}-原始{ext}"))
        
        # 保存提取的txt作为转换中间文件
        txt_out = dest_dir / f"{base_name}-转换.txt"
        with open(txt_out, 'w', encoding='utf-8') as f:
            for ch_title, ch_text in chapters:
                f.write(f"# {ch_title}\n\n{ch_text}\n\n")
        
        # 计算总用时
        total_seconds = int(time.time() - start_time)
        total_time_str = format_time(total_seconds)
        
        update_status(step=3, real_pct=100, progress_detail=f"Done! Saved to: {dest_dir}", eta="Complete", total_time=total_time_str)
        status["output_file"] = audio_out
        
        # 写入历史记录
        try:
            history_file = OUTPUT_DIR / ".history.json"
            history = []
            if history_file.exists():
                history = json.loads(history_file.read_text(encoding="utf-8"))
            history.insert(0, {
                "title": book_info["title"],
                "author": book_info["author"],
                "voice": voice,
                "chars": book_info["chars"],
                "chapters": book_info["chapters"],
                "duration": total_time_str,
                "output": audio_out,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            history = history[:50]  # 保留最近50条
            history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"History save failed: {e}")
        
    except Exception as e:
        import traceback
        status["error"] = f"Error: {e}"
        print(traceback.format_exc())
    finally:
        status["running"] = False
        if work_dir and os.path.exists(work_dir):
            try: shutil.rmtree(work_dir, ignore_errors=True)
            except: pass
# ============ Web UI ============

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>Ebook2Audiobook</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei','Segoe UI',sans-serif;background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);color:#2d3436;min-height:100vh;padding:24px}
.container{max-width:920px;margin:0 auto}
h1{text-align:center;margin-bottom:6px;color:#2d3436;font-size:28px;font-weight:700}
.subtitle{text-align:center;color:#636e72;margin-bottom:24px;font-size:13px}
.panel{background:#fff;border-radius:16px;padding:22px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,.06);border:1px solid #eef0f3}
.panel h2{color:#0984e3;margin-bottom:12px;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}
.drop-zone{border:2px dashed #dfe6e9;border-radius:12px;padding:36px 20px;text-align:center;cursor:pointer;transition:all .25s;background:#fafbfc}
.drop-zone:hover,.drop-zone.dragover{border-color:#0984e3;background:#f0f8ff}
.drop-zone .icon{font-size:36px;margin-bottom:8px}
.drop-zone p{color:#636e72;font-size:13px}
.drop-zone .filename{color:#00b894;font-size:13px;margin-top:8px;font-weight:600}
.formats{color:#74b9ff;font-size:11px;margin-top:8px;text-align:center;font-weight:500}
.form-group{margin-bottom:10px}
.form-group label{display:block;margin-bottom:4px;color:#636e72;font-size:12px;font-weight:500}
select,input{width:100%;padding:9px 11px;border-radius:8px;border:1px solid #dfe6e9;background:#fafbfc;color:#2d3436;font-size:13px;transition:border .2s}
select:focus,input:focus{outline:none;border-color:#0984e3}
.row{display:flex;gap:10px}.row .form-group{flex:1}
.btn{display:block;width:100%;padding:13px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;transition:all .2s}
.btn-convert{background:linear-gradient(135deg,#0984e3,#00b894);color:white}
.btn-convert:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 4px 16px rgba(9,132,227,.3)}
.btn-convert:disabled{background:#b2bec3;cursor:not-allowed}
.book-info{background:#f0f8ff;border-radius:10px;padding:12px 16px;margin-bottom:14px;display:none;border:1px solid #bee3f8}
.book-info.active{display:block}
.book-info h3{font-size:13px;color:#0984e3;margin-bottom:8px}
.book-info .stats{display:flex;gap:14px;flex-wrap:wrap}
.book-info .stat{font-size:12px;color:#2d3436}
.book-info .stat span{font-weight:600;color:#0984e3}
.progress-panel{display:none}.progress-panel.active{display:block}
.steps{display:flex;gap:6px;margin-bottom:14px}
.step{flex:1;padding:9px;border-radius:8px;background:#fafbfc;border:1px solid #eef0f3;text-align:center;font-size:11px;transition:all .25s}
.step.active{border-color:#0984e3;background:#f0f8ff;color:#0984e3}
.step.done{border-color:#00b894;background:#f0fff4;color:#00b894}
.step .num{font-size:17px;font-weight:700;margin-bottom:2px}
.step.active .num{color:#0984e3}.step.done .num{color:#00b894}
.progress-bar{height:6px;background:#eef0f3;border-radius:3px;overflow:hidden;margin:10px 0}
.progress-bar .fill{height:100%;background:linear-gradient(90deg,#0984e3,#00b894);transition:width .4s;border-radius:3px}
.progress-info{display:flex;justify-content:space-between;font-size:12px;color:#636e72}
.progress-detail{font-size:12px;color:#00b894;margin-top:6px}
.eta{font-size:12px;color:#6c5ce7;margin-top:4px;font-weight:500}
.result{margin-top:14px;padding:16px;border-radius:10px;background:#f0fff4;border:1px solid #00b894;display:none}
.result.active{display:block}.result h3{color:#00b894;margin-bottom:6px;font-size:14px}
.result p{color:#2d3436;font-size:13px;word-break:break-all}
.preview-btn{background:transparent;color:#0984e3;border:1px solid #0984e3;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;margin-top:6px}
.preview-btn:hover{background:#f0f8ff}
audio{width:100%;margin-top:6px;height:32px}
.tip{font-size:11px;color:#636e72;margin-top:6px;line-height:1.5}
</style></head><body><div class="container">
<h1>📖 Ebook2Audiobook</h1>
<p class="subtitle">Upload ebook → Convert → Auto-organize · Chinese & English · Free & Open Source</p>
<div style="text-align:center;margin-bottom:14px"><button class="preview-btn" onclick="toggleHistory()" style="font-size:11px">📚 History</button></div>
<div class="panel" id="historyPanel" style="display:none"><h2>📚 Conversion History</h2><div id="historyList" style="font-size:12px;color:#636e72"></div></div>

<div class="panel"><h2>📂 Import</h2>
<div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
<div class="icon">📁</div>
<p>Drag & drop file here, or click to browse</p>
<p class="filename" id="fileName"></p>
<input type="file" id="fileInput" accept=".epub,.txt,.pdf,.docx,.doc,.mobi,.azw3" style="display:none" onchange="handleFile(this)">
</div>
<p class="formats">Supported: epub · txt · pdf · docx · mobi · azw3</p>
<p class="tip">💡 .txt is converted directly; other formats are auto-converted to text first</p>
</div>

<div class="book-info" id="bookInfo">
<h3>📊 Book Overview</h3>
<div class="stats">
<div class="stat">Title: <span id="biTitle">-</span></div>
<div class="stat">Author: <span id="biAuthor">-</span></div>
<div class="stat">Chapters: <span id="biChapters">-</span></div>
<div class="stat">Characters: <span id="biChars">-</span></div>
<div class="stat">Est. Duration: <span id="biDuration">-</span></div>
</div></div>

<div class="panel"><h2>🎙️ Voice</h2>
<div class="row">
<div class="form-group"><label>Category</label><select id="voiceCategory" onchange="updateVoices()">
__VOICE_OPTIONS__
</select></div>
<div class="form-group"><label>Speaker</label><select id="voiceSelect"></select></div>
</div>
<div class="form-group" style="margin-top:10px"><label>Speed</label><select id="rateSelect">
<option value="-25%">Slow (-25%)</option>
<option value="-10%">Slower (-10%)</option>
<option value="+0%" selected>Normal (+0%)</option>
<option value="+10%">Faster (+10%)</option>
<option value="+25%">Fast (+25%)</option>
<option value="+50%">Very Fast (+50%)</option>
</select></div>
<button class="preview-btn" onclick="previewVoice()">▶ Preview</button>
<audio id="previewAudio" controls style="display:none"></audio>
</div>

<div class="panel"><h2>💾 Output</h2>
<div class="row">
<div class="form-group"><label>Format</label><select id="outputFormat">
<option value="m4b">M4B with chapters (recommended)</option>
<option value="mp3">MP3</option>
</select></div>
</div>
<p class="tip">输出位置: ./audiobooks/书名-作者/</p>
</div>

<button class="btn btn-convert" id="convertBtn" onclick="startConversion()">Start Conversion</button>

<div class="panel progress-panel" id="progressPanel">
<h2>⏳ Progress</h2>
<div class="steps">
<div class="step" id="step1"><div class="num">1</div>Parse</div>
<div class="step" id="step2"><div class="num">2</div>Generate</div>
<div class="step" id="step3"><div class="num">3</div>Archive</div>
</div>
<div class="progress-info"><span id="stepName">Waiting...</span><span id="pctText">0%</span></div>
<div class="progress-bar"><div class="fill" id="progressFill" style="width:0%"></div></div>
<p class="progress-detail" id="progressDetail"></p>
<p class="eta" id="etaText"></p>
<p class="eta" id="totalTimeText" style="color:#00b894"></p>
</div>

<div class="result" id="resultBox"><h3>✅ Done</h3><p id="resultText"></p><p id="resultTime" style="color:#6c5ce7;font-weight:600;margin-top:6px"></p></div>
</div>
<script>
const voices=__VOICES_JSON__;
let selectedFile=null;
function updateVoices(){const c=document.getElementById('voiceCategory').value,s=document.getElementById('voiceSelect');s.innerHTML='';for(const[id,name]of Object.entries(voices[c])){const o=document.createElement('option');o.value=id;o.textContent=name;s.appendChild(o)}}updateVoices();
const dz=document.getElementById('dropZone');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover')});
dz.addEventListener('dragleave',()=>dz.classList.remove('dragover'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');if(e.dataTransfer.files.length)handleFileObj(e.dataTransfer.files[0])});
function handleFile(i){if(i.files.length)handleFileObj(i.files[0])}
function handleFileObj(f){selectedFile=f;document.getElementById('fileName').textContent=f.name+' ('+(f.size>1048576?(f.size/1048576).toFixed(1)+' MB':(f.size/1024).toFixed(0)+' KB')+')';
const fd=new FormData();fd.append('file',f);
fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
if(d.success){const bi=d.info;document.getElementById('bookInfo').classList.add('active');
document.getElementById('biTitle').textContent=bi.title||'-';
document.getElementById('biAuthor').textContent=bi.author||'Unknown';
document.getElementById('biChapters').textContent=bi.chapters||'-';
document.getElementById('biChars').textContent=bi.chars?bi.chars.toLocaleString()+' chars':'-';
const mins=Math.round((bi.chars||0)/250);
document.getElementById('biDuration').textContent=mins>60?Math.floor(mins/60)+'h '+(mins%60)+'min':mins+'min';
}})}
function previewVoice(){const v=document.getElementById('voiceSelect').value;fetch('/preview?voice='+v).then(r=>r.blob()).then(b=>{const a=document.getElementById('previewAudio');a.src=URL.createObjectURL(b);a.style.display='block';a.play()})}
function startConversion(){if(!selectedFile){alert('Please select a file first');return}
const btn=document.getElementById('convertBtn'),pp=document.getElementById('progressPanel'),rs=document.getElementById('resultBox');
btn.disabled=true;btn.textContent='Converting...';pp.classList.add('active');rs.classList.remove('active');
document.querySelectorAll('.step').forEach(s=>s.classList.remove('active','done'));
const fd=new FormData();fd.append('file',selectedFile);fd.append('voice',document.getElementById('voiceSelect').value);fd.append('format',document.getElementById('outputFormat').value);fd.append('rate',document.getElementById('rateSelect').value);
fetch('/convert',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{if(d.success)pollStatus();else{alert(d.error);btn.disabled=false;btn.textContent='Start Conversion'}})}
function pollStatus(){fetch('/status').then(r=>r.json()).then(d=>{
const fill=document.getElementById('progressFill'),stepName=document.getElementById('stepName'),pct=document.getElementById('pctText'),detail=document.getElementById('progressDetail'),eta=document.getElementById('etaText');
for(let i=1;i<=3;i++){const el=document.getElementById('step'+i);el.classList.remove('active','done');if(i<d.step)el.classList.add('done');else if(i===d.step)el.classList.add('active')}
const realPct=d.real_pct||0;
fill.style.width=realPct+'%';pct.textContent=realPct+'%';
stepName.textContent=d.step_name||'处理中...';
detail.textContent=d.progress_detail||'';
eta.textContent=d.eta?'ETA: '+d.eta:'';
if(d.running){setTimeout(pollStatus,1500)}else{
const btn=document.getElementById('convertBtn');btn.disabled=false;btn.textContent='Start Conversion';
if(d.output_file){const rs=document.getElementById('resultBox');rs.classList.add('active');document.getElementById('resultText').textContent='Saved to: '+d.output_file;document.getElementById('resultTime').textContent='⏱️ Total time: '+(d.total_time||'-');document.getElementById('totalTimeText').textContent='⏱️ Total time: '+(d.total_time||'-');fill.style.width='100%';pct.textContent='100%';eta.textContent='Complete';document.querySelectorAll('.step').forEach(s=>{s.classList.remove('active');s.classList.add('done')})}
else if(d.error){detail.textContent='Error: '+d.error;eta.textContent=''}}})}

function toggleHistory(){const p=document.getElementById('historyPanel');if(p.style.display==='none'){p.style.display='block';loadHistory()}else p.style.display='none'}
function loadHistory(){fetch('/history').then(r=>r.json()).then(d=>{
const list=document.getElementById('historyList');
if(!d.length){list.innerHTML='<p style="color:#999;text-align:center;padding:20px">No history yet</p>';return}
list.innerHTML=d.map(h=>'<div style="padding:10px;border-bottom:1px solid #eee">'+
'<div style="font-weight:600;color:#2d3436">'+h.title+(h.author?' - '+h.author:'')+'</div>'+
'<div style="color:#636e72;margin-top:4px">'+h.chars.toLocaleString()+' chars · '+h.chapters+' chapters · '+h.duration+' · '+h.timestamp+'</div>'+
'</div>').join('')})}
</script></body></html>'''

@app.route('/')
def index():
    voice_options = ''.join(f'<option value="{c}">{c}</option>' for c in VOICES.keys())
    html = HTML.replace('__VOICE_OPTIONS__', voice_options).replace('__VOICES_JSON__', json.dumps(VOICES, ensure_ascii=False))
    return html

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
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

@app.route('/preview')
def preview():
    voice = request.args.get('voice', 'zh-CN-XiaoxiaoNeural')
    text = "Hello, this is a voice preview." if 'en-' in voice else "你好，这是Speaker试听。"
    tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    tmp.close()
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(tts_to_file(text, voice, tmp.name))
        return send_file(tmp.name, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/convert', methods=['POST'])
def convert():
    global status
    if status["running"]:
        return jsonify({"success": False, "error": "Conversion already running"})
    file = request.files.get('file')
    voice = request.form.get('voice', 'zh-CN-XiaoxiaoNeural')
    output_format = request.form.get('format', 'm4b')
    rate = request.form.get('rate', '+0%')
    if not file:
        return jsonify({"success": False, "error": "No file selected"})
    
    # 保存上传文件到临时目录(英文路径)
    upload_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
    file.save(upload_tmp.name)
    upload_tmp.close()
    
    # 把原始文件名保存为元数据
    setattr(sys.modules[__name__], '_orig_filename', file.filename)
    
    # 重置状态
    status.clear()
    status.update({
        "running": True, "step": 0, "step_name": "Starting...",
        "real_pct": 0, "progress_detail": "", "chapters_done": 0,
        "chapters_total": 0, "output_file": "", "error": "",
        "book_info": None, "eta": "", "start_time": time.time(),
        "_orig_name": file.filename
    })
    
    # 在新线程里运行转换，传入原始文件名信息
    def run_with_orig_name():
        # 把原始文件名加入路径供parse使用
        orig_path = os.path.join(tempfile.gettempdir(), file.filename)
        try:
            shutil.copy2(upload_tmp.name, orig_path)
            run_conversion(orig_path, voice, output_format, rate)
        finally:
            try: os.unlink(upload_tmp.name)
            except: pass
            try: os.unlink(orig_path)
            except: pass
    
    thread = threading.Thread(target=run_with_orig_name, daemon=True)
    thread.start()
    return jsonify({"success": True})

@app.route("/status")
def get_status():
    return jsonify(status)

@app.route("/history")
def get_history():
    history_file = OUTPUT_DIR / ".history.json"
    if not history_file.exists():
        return jsonify([])
    try:
        return jsonify(json.loads(history_file.read_text(encoding="utf-8")))
    except:
        return jsonify([])

if __name__ == '__main__':
    import webbrowser
    port = 7860
    print("=" * 50)
    print("  Ebook2Audiobook")
    print(f"  http://127.0.0.1:{port}")
    print(f"  ffmpeg: {FFMPEG}")
    print(f"  calibre: {EBOOK_CONVERT or 'NOT FOUND'}")
    print("=" * 50)
    webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)