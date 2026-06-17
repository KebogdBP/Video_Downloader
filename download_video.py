import yt_dlp
import os
import re
import subprocess
import shutil
import uuid
import time

def extract_video_url(url):
    """Извлекает ТОЛЬКО URL видео, удаляя параметры плейлистов и радио"""
    url = re.sub(r'[&?]list=[^&]+', '', url)
    url = re.sub(r'[&?]start_radio=[^&]+', '', url)
    url = re.sub(r'[&?]index=[^&]+', '', url)
    return url.strip()

def get_all_formats(url):
    """Получает все доступные форматы видео"""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            clean_url = extract_video_url(url)
            info = ydl.extract_info(clean_url, download=False)
            
            if not info:
                return None, None, 0
                
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            formats = info.get('formats', [])
            qualities = {}
            
            for f in formats:
                height = f.get('height')
                if height and f.get('vcodec') != 'none':
                    quality_key = f"{height}p"
                    fps = f.get('fps')
                    if fps and fps >= 50:
                        quality_key = f"{height}p{fps}"
                    
                    has_audio = f.get('acodec') != 'none'
                    quality_key += " ✓ со звуком" if has_audio else " ✗ только видео"
                    
                    if quality_key not in qualities:
                        qualities[quality_key] = {
                            'format_id': f['format_id'],
                            'height': height,
                            'has_audio': has_audio,
                            'filesize': f.get('filesize'),
                        }
            
            sorted_qualities = sorted(qualities.items(), key=lambda x: x[1]['height'])
            return sorted_qualities, info.get('title', 'Неизвестно'), info.get('duration', 0)
            
    except Exception as e:
        print(f"❌ Ошибка получения форматов: {e}")
        return None, None, 0

def display_all_formats(qualities):
    if not qualities:
        print("❌ Нет доступных форматов")
        return False
    
    print("\n📺 Доступные качества:")
    print("-" * 65)
    for i, (quality_name, info) in enumerate(qualities, 1):
        size_str = f" ({info['filesize'] / (1024 * 1024):.1f} MB)" if info.get('filesize') else ""
        print(f"{i:2}. {quality_name}{size_str}")
    print("-" * 65)
    print("0. Отмена")
    return True

def parse_time(time_str):
    if not time_str or not time_str.strip():
        return None
    time_str = time_str.strip()
    if time_str.isdigit():
        return int(time_str)
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    raise ValueError(f"Неверный формат времени: {time_str}")

def format_time(seconds):
    if seconds is None:
        return "???"
    h, m, s = int(seconds) // 3600, (int(seconds) % 3600) // 60, int(seconds) % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def estimate_audio_size(duration_seconds, bitrate_kbps):
    """Оценивает размер аудиофайла в MB"""
    size_mb = (bitrate_kbps * duration_seconds) / 8 / 1024
    return size_mb

def cut_video_sync(input_path, output_path, start_time, end_time):
    """
    Обрезка видео с сохранением аудио и синхронизацией
    """
    print(f"\n✂️ Обрезка видео с сохранением потоков...")
    print(f"   Начало: {format_time(start_time) if start_time else '00:00'}")
    print(f"   Конец: {format_time(end_time) if end_time else 'конец'}")
    if start_time is not None and end_time is not None:
        print(f"   Длина: {format_time(end_time - start_time)}")
    
    dir_name = os.path.dirname(output_path) or "."
    temp_output = os.path.join(dir_name, f"temp_cut_{uuid.uuid4().hex[:8]}.mp4")
    
    # Строим команду FFmpeg
    cmd = ['ffmpeg', '-i', input_path]
    if start_time is not None:
        cmd.extend(['-ss', str(start_time)])
    if end_time is not None:
        cmd.extend(['-to', str(end_time)])
        
    cmd.extend([
        '-map', '0:v:0', '-map', '0:a:0',  # Явное указание видео и аудио потоков
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart', '-y', temp_output
    ])
    
    print("   🔄 Выполняется перекодировка...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0 and os.path.exists(temp_output) and os.path.getsize(temp_output) > 1024 * 1024:
            shutil.copy2(temp_output, output_path)
            print("   ✅ Видео успешно обрезано, звук сохранен!")
            os.remove(temp_output)
            return True
        else:
            print(f"   ❌ Ошибка FFmpeg (код: {result.returncode})")
            if result.stderr:
                print(f"   Детали: {' | '.join(result.stderr.strip().split('\n')[-3:])}")
            return False
    except FileNotFoundError:
        print("   ❌ FFmpeg не найден в системе!")
        return False
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def verify_download(ydl, info, output_path):
    """Проверяет, что файл реально скачался и имеет нормальный размер"""
    if not info:
        return False, "Не удалось получить информацию о видео"
    
    filename = ydl.prepare_filename(info)
    
    if not os.path.exists(filename):
        recent_files = [
            f for f in os.listdir(output_path) 
            if f.endswith('.mp4') and (time.time() - os.path.getmtime(os.path.join(output_path, f))) < 60
        ]
        if recent_files:
            filename = os.path.join(output_path, recent_files[0])
        else:
            return False, f"Файл не создан: {filename}"
    
    file_size = os.path.getsize(filename)
    if file_size < 1024 * 1024:
        return False, f"Файл поврежден (Размер: {file_size / 1024:.1f} KB)"
    
    return True, filename

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            percent = (downloaded / total) * 100
            speed = d.get('speed')
            speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "??"
            eta = d.get('eta')
            eta_str = f"{int(eta)//60}:{int(eta)%60:02d}" if eta else "??"
            print(f"\r📥 {percent:.1f}% | {speed_str} | ост. {eta_str}", end='', flush=True)
    elif d['status'] == 'finished':
        print("\n🔧 Обработка потоков...")

def download_video_with_quality_and_time(url, output_path="downloads"):
    """Опция 1: Скачивание видео с выбором качества и обрезкой"""
    clean_url = extract_video_url(url)
    print("\n🔍 Получаю информацию о видео...")
    result = get_all_formats(clean_url)
    
    if not result or not result[0]:
        print("⚠️ Не удалось получить форматы. Возможно, видео заблокировано.")
        return False
    
    qualities, video_title, duration = result
    print(f"\n📹 Видео: {video_title[:60]}{'...' if len(video_title) > 60 else ''}")
    print(f"⏱️ Длительность: {format_time(duration)}")
    display_all_formats(qualities)
    
    while True:
        try:
            choice = input(f"\n👉 Выберите качество (1-{len(qualities)} или 0): ").strip()
            if choice == '0': 
                return False
            choice_num = int(choice)
            if 1 <= choice_num <= len(qualities):
                quality_name, quality_info = qualities[choice_num - 1]
                print(f"\n✅ Выбрано: {quality_name}")
                break
            print(f"❌ Введите число от 1 до {len(qualities)}")
        except ValueError:
            print("❌ Пожалуйста, введите число")
    
    print("\n✂️ Обрезка (оставьте пустым для пропуска). Формат: 125 или 2:05 или 1:30:45")
    start_time, end_time = None, None
    
    for prompt, is_start in [("⏱️ Начальное время", True), ("⏱️ Конечное время", False)]:
        while True:
            val = input(f"{prompt} (0-{format_time(duration)}): ").strip()
            if not val: 
                break
            try:
                t = parse_time(val)
                if not (0 <= t <= duration):
                    print(f"❌ Время должно быть в диапазоне 0 - {format_time(duration)}")
                    continue
                if not is_start and start_time is not None and t <= start_time:
                    print("❌ Конечное время должно быть больше начального")
                    continue
                if is_start: 
                    start_time = t
                else: 
                    end_time = t
                break
            except ValueError as e:
                print(f"❌ {e}")
    
    need_cut = (start_time is not None and start_time > 0) or (end_time is not None and end_time < duration)
    if need_cut and start_time is not None and end_time is not None:
        print(f"\n📊 Будет вырезан отрезок: с {format_time(start_time)} по {format_time(end_time)}")
    
    os.makedirs(output_path, exist_ok=True)
    temp_template = os.path.join(output_path, f"temp_{uuid.uuid4().hex[:8]}.%(ext)s")
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title).strip()
    
    final_filename = f"{safe_title} [{format_time(start_time) if start_time else '00:00'}-{format_time(end_time) if end_time else 'конец'}].mp4" if need_cut else f"{safe_title}.mp4"
    final_path = os.path.join(output_path, final_filename)
    
    format_spec = f"{quality_info['format_id']}+bestaudio[ext=m4a]/bestaudio/best"
    
    download_opts = {
        'outtmpl': temp_template, 
        'format': format_spec, 
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook], 
        'quiet': True, 
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            print(f"\n📥 Скачиваю видео...\n")
            info = ydl.extract_info(clean_url, download=True)
            
        success, temp_path = verify_download(ydl, info, output_path)
        if not success:
            print(f"\n❌ Ошибка: {temp_path}")
            return False
        
        if need_cut:
            if cut_video_sync(temp_path, final_path, start_time, end_time):
                os.remove(temp_path)
            else:
                print("⚠️ Обрезка не удалась, сохраняю полное видео")
                shutil.move(temp_path, final_path)
        else:
            shutil.move(temp_path, final_path)
            
        print(f"\n✅ ГОТОВО!")
        print(f"📁 Путь: {os.path.abspath(final_path)}")
        print(f"📊 Размер: {os.path.getsize(final_path) / (1024 * 1024):.1f} MB")
        return True
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return False

def download_playlist(url, output_path="downloads"):
    """
    Опция 2: Скачивание плейлиста с выбором качества и ЗВУКОМ
    """
    if 'list=' not in url:
        print("❌ Это не ссылка на плейлист")
        return False
    
    os.makedirs(output_path, exist_ok=True)
    
    print("\n🎯 Качество для плейлиста:")
    print("1. Лучшее (видео+аудио)")
    print("2. 1080p + аудио")
    print("3. 720p + аудио")
    print("4. 480p + аудио")
    
    quality_choice = input("\n👉 Выбор (1-4): ").strip()
    
    # ИСПРАВЛЕННЫЕ форматы с принудительным добавлением аудио
    quality_map = {
        '1': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=webm]+bestaudio[ext=webm]/best',
        '2': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=webm][height<=1080]+bestaudio[ext=webm]/best[height<=1080]',
        '3': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/bestvideo[ext=webm][height<=720]+bestaudio[ext=webm]/best[height<=720]',
        '4': 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/bestvideo[ext=webm][height<=480]+bestaudio[ext=webm]/best[height<=480]',
    }
    
    format_spec = quality_map.get(quality_choice, quality_map['1'])
    
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(playlist_title)s', '%(title)s.%(ext)s'),
        'format': format_spec,
        'merge_output_format': 'mp4',
        'ignoreerrors': True,
        'quiet': False,
        'noplaylist': False,
        'postprocessors': [{  # Добавляем постпроцессор для гарантии MP4
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n📀 Скачиваю плейлист...")
            info = ydl.extract_info(url, download=True)
            playlist_title = info.get('playlist_title', 'Playlist')
            
            # Считаем успешно скачанные видео
            entries = info.get('entries', [])
            successful = sum(1 for e in entries if e is not None)
            
            print(f"\n✅ Готово! Скачано {successful} из {len(entries)} видео")
            print(f"📁 Папка: {output_path}/{playlist_title}")
            print(f"🔊 Все видео содержат аудиодорожку (объединены в MP4)")
            return True
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def get_best_audio_format(url):
    """Получает информацию о лучшем аудио формате"""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            clean_url = extract_video_url(url)
            info = ydl.extract_info(clean_url, download=False)
            
            formats = info.get('formats', [])
            best_audio = None
            best_bitrate = 0
            
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    bitrate = f.get('abr', 0) or f.get('tbr', 0)
                    if bitrate > best_bitrate:
                        best_bitrate = bitrate
                        best_audio = {
                            'format_id': f['format_id'],
                            'ext': f.get('ext', 'unknown'),
                            'bitrate': bitrate,
                            'filesize': f.get('filesize'),
                        }
            
            return best_audio, info.get('title', 'audio'), info.get('duration', 0)
            
    except Exception as e:
        print(f"❌ Ошибка получения аудио формата: {e}")
        return None, None, 0

def download_audio_best_quality(url, output_path="downloads/music"):
    """Опция 3: Скачивание аудио в лучшем качестве"""
    clean_url = extract_video_url(url)
    os.makedirs(output_path, exist_ok=True)
    
    best_audio, title, duration = get_best_audio_format(clean_url)
    
    if not best_audio:
        print("⚠️ Не удалось получить информацию об аудио")
        return False
    
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    
    print(f"\n📹 {title[:50]}")
    print(f"⏱️ {format_time(duration)}")
    
    size_320 = estimate_audio_size(duration, 320)
    size_192 = estimate_audio_size(duration, 192)
    size_128 = estimate_audio_size(duration, 128)
    
    orig_size = best_audio.get('filesize', 0)
    if orig_size:
        orig_size_mb = orig_size / (1024 * 1024)
        orig_bitrate = best_audio.get('bitrate', 0)
    else:
        orig_size_mb = size_192 * 1.5
        orig_bitrate = 160
    
    print("\n" + "=" * 45)
    print("🎵 ВЫБЕРИТЕ КАЧЕСТВО АУДИО")
    print("=" * 45)
    
    print(f"\n  🎧 1.  ОРИГИНАЛ")
    print(f"      {orig_bitrate:.0f} kbps  •  {orig_size_mb:.1f} MB  •  {best_audio['ext'].upper()}")
    
    print(f"\n  🎵 2.  MP3 ВЫСОКОЕ")
    print(f"      320 kbps  •  {size_320:.1f} MB")
    
    print(f"\n  🎵 3.  MP3 ХОРОШЕЕ (рекомендуется)")
    print(f"      192 kbps  •  {size_192:.1f} MB")
    
    print(f"\n  🎵 4.  MP3 СРЕДНЕЕ")
    print(f"      128 kbps  •  {size_128:.1f} MB")
    
    print("\n" + "-" * 45)
    print("  0.  НАЗАД")
    print("=" * 45)
    
    quality_choice = input("\n👉 ВАШ ВЫБОР: ").strip()
    
    if quality_choice == '0':
        return False
    
    if quality_choice == '1':
        print(f"\n📥 Скачиваю оригинал ({best_audio['ext'].upper()}, {orig_bitrate:.0f} kbps)...")
        
        final_path = os.path.join(output_path, f"{safe_title}_best.{best_audio['ext']}")
        
        ydl_opts = {
            'outtmpl': final_path,
            'format': best_audio['format_id'],
            'quiet': False,
            'noplaylist': True,
            'ignoreerrors': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(clean_url, download=True)
            
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path) / (1024 * 1024)
                print(f"\n✅ ГОТОВО!")
                print(f"📁 {output_path}")
                print(f"🎵 {os.path.basename(final_path)}")
                print(f"📊 {file_size:.1f} MB  •  {orig_bitrate:.0f} kbps")
                return True
            else:
                print(f"\n❌ Ошибка: файл не создан")
                return False
                
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            return False
    
    elif quality_choice in ['2', '3', '4']:
        mp3_map = {'2': '320', '3': '192', '4': '128'}
        mp3_quality = mp3_map[quality_choice]
        
        size_map = {'2': size_320, '3': size_192, '4': size_128}
        estimated_size = size_map[quality_choice]
        
        print(f"\n📥 Скачиваю MP3 {mp3_quality} kbps (~{estimated_size:.1f} MB)...")
        
        final_path = os.path.join(output_path, f"{safe_title}.mp3")
        
        ydl_opts = {
            'outtmpl': final_path,
            'format': 'bestaudio/best',
            'quiet': False,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': mp3_quality,
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(clean_url, download=True)
            
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path) / (1024 * 1024)
                print(f"\n✅ ГОТОВО!")
                print(f"📁 {output_path}")
                print(f"🎵 {os.path.basename(final_path)}")
                print(f"📊 {file_size:.1f} MB  •  {mp3_quality} kbps")
                return True
            else:
                print(f"\n❌ Ошибка скачивания")
                return False
                
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            return False
    
    else:
        print("❌ Неверный выбор")
        return False

def download_audio(url, output_path="downloads/music"):
    """Опция 3: Скачивание аудио"""
    return download_audio_best_quality(url, output_path)

def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ FFmpeg готов")
            return True
    except FileNotFoundError:
        pass
    return False
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_direct_audio_links(url):
    """
    Универсальный парсер: ищет прямые ссылки на mp3 И извлекает названия треков.
    Возвращает список словарей: [{'url': ..., 'title': ..., 'filename': ...}, ...]
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': url,
    }
    
    try:
        print(f"\n🔍 Анализирую страницу {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # === ШАГ 1: Извлекаем общее название трека/страницы ===
        page_title = None
        
        # Ищем в <h1>
        h1 = soup.find('h1')
        if h1:
            page_title = h1.get_text(strip=True)
        
        # Если нет — берём из <title>
        if not page_title:
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text(strip=True)
                # Чистим от мусора типа " - сайт.com"
                for sep in [' - ', ' | ', ' :: ', ' — ']:
                    if sep in page_title:
                        page_title = page_title.split(sep)[0].strip()
                        break
        
        # Если нет — ищем в мета-тегах
        if not page_title:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                page_title = og_title.get('content', '').strip()
        
        if not page_title:
            page_title = "audio_track"
        
        # Чистим название от недопустимых символов
        page_title_clean = re.sub(r'[<>:"/\\|?*]', '_', page_title)[:80].strip()
        print(f"📌 Название страницы: {page_title_clean}")
        
        # === ШАГ 2: Ищем ссылки на аудиофайлы ===
        audio_links = []
        seen_urls = set()
        
        # Паттерны для поиска URL аудиофайлов в HTML/JS
        patterns = [
            r'(https?://[^\s"\'<>]+\.mp3(?:\?[^\s"\'<>]*)?)',
            r'(https?://[^\s"\'<>]+\.m4a(?:\?[^\s"\'<>]*)?)',
            r'(https?://[^\s"\'<>]+\.ogg(?:\?[^\s"\'<>]*)?)',
            r'data-(?:src|url|audio|file|mp3)=["\']([^"\']+\.(?:mp3|m4a|ogg|wav))["\']',
            r'file:\s*["\']([^"\']+\.(?:mp3|m4a|ogg|wav))["\']',
            r'source:\s*["\']([^"\']+\.(?:mp3|m4a|ogg|wav))["\']',
            r'"(\/[^"]+\.mp3[^"]*)"',
            r"'(\/[^']+\.mp3[^']*)'",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                full_url = match if match.startswith('http') else urljoin(url, match)
                # Убираем query-параметры для уникализации
                base_url = full_url.split('?')[0]
                if base_url not in seen_urls:
                    seen_urls.add(base_url)
                    audio_links.append(full_url)
        
        # Также ищем в тегах <audio> и <source>
        for audio in soup.find_all(['audio', 'source']):
            src = audio.get('src') or audio.get('data-src')
            if src:
                full_url = urljoin(url, src)
                base_url = full_url.split('?')[0]
                if base_url not in seen_urls:
                    seen_urls.add(base_url)
                    audio_links.append(full_url)
        
        # === ШАГ 3: Формируем список с названиями ===
        result = []
        
        # Пытаемся найти названия для каждого трека в HTML
        # Ищем элементы с классами, содержащими "title", "name", "song", "track"
        title_candidates = []
        for tag in soup.find_all(['div', 'span', 'p', 'h2', 'h3', 'a']):
            classes = ' '.join(tag.get('class', []))
            if any(word in classes.lower() for word in ['title', 'name', 'song', 'track', 'artist']):
                text = tag.get_text(strip=True)
                if text and 3 < len(text) < 100 and text != page_title:
                    title_candidates.append(text)
        
        # Если нашли кандидатов — сопоставляем с треками
        if len(title_candidates) == len(audio_links) and len(audio_links) > 1:
            # Идеальный случай: названий столько же, сколько треков
            for i, link in enumerate(audio_links):
                filename_from_url = os.path.basename(urlparse(link).path)
                result.append({
                    'url': link,
                    'title': title_candidates[i],
                    'filename': re.sub(r'[<>:"/\\|?*]', '_', title_candidates[i])[:80] + '.mp3'
                })
        else:
            # Используем название страницы
            if len(audio_links) == 1:
                # Один трек — используем название страницы
                result.append({
                    'url': audio_links[0],
                    'title': page_title_clean,
                    'filename': page_title_clean + '.mp3'
                })
            else:
                # Несколько треков — добавляем номера
                for i, link in enumerate(audio_links, 1):
                    filename_from_url = os.path.basename(urlparse(link).path)
                    name_without_ext = os.path.splitext(filename_from_url)[0]
                    
                    # Если имя файла выглядит как ID/дата — используем название страницы + номер
                    if name_without_ext.isdigit() or len(name_without_ext) > 15:
                        track_title = f"{page_title_clean} - Трек {i}"
                    else:
                        track_title = name_without_ext
                    
                    result.append({
                        'url': link,
                        'title': track_title,
                        'filename': re.sub(r'[<>:"/\\|?*]', '_', track_title)[:80] + '.mp3'
                    })
        
        return result, page_title_clean
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка доступа к сайту: {e}")
        return [], None
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()
        return [], None


def download_audio_from_generic_site(url, output_path="downloads/music"):
    """
    Опция 4: Скачивание аудио с ЛЮБОГО сайта через прямой парсинг.
    Теперь с нормальными названиями треков!
    """
    os.makedirs(output_path, exist_ok=True)
    
    audio_data, page_title = get_direct_audio_links(url)
    
    if not audio_data:
        print("\n⚠️ Не удалось найти аудиофайлы на странице.")
        print("💡 Возможные причины:")
        print("   • Сайт использует защиту от парсинга")
        print("   • Аудио загружается динамически через JavaScript")
        print("   • Файлы имеют нестандартное расширение")
        print("\n💡 Решение: откройте страницу в браузере,")
        print("   нажмите F12 → вкладка Network → отфильтруйте по 'Media'")
        print("   и скопируйте прямую ссылку на mp3 файл.")
        
        manual_url = input("\n🔗 Или вставьте прямую ссылку на mp3 вручную (или Enter для отмены): ").strip()
        if manual_url:
            filename = os.path.basename(urlparse(manual_url).path) or "audio.mp3"
            audio_data = [{'url': manual_url, 'title': filename, 'filename': filename}]
            page_title = "manual_download"
        else:
            return False
    
    print(f"\n✅ Найдено аудиофайлов: {len(audio_data)}")
    
    # --- ОДИН ФАЙЛ ---
    if len(audio_data) == 1:
        track = audio_data[0]
        print(f"\n🎵 Название: {track['title']}")
        print(f"   URL: {track['url'][:70]}...")
        return download_single_audio_file_named(track['url'], track['filename'], output_path)
    
    # --- НЕСКОЛЬКО ФАЙЛОВ ---
    print("\n" + "=" * 65)
    print(f"📋 СПИСОК ТРЕКОВ (альбом: {page_title}):")
    print("=" * 65)
    
    for i, track in enumerate(audio_data, 1):
        print(f"{i:3}. 🎵 {track['title'][:60]}")
        print(f"     📁 {track['filename'][:60]}")
    
    print("=" * 65)
    print("💡 Форматы выбора:")
    print("  • all        — скачать все файлы")
    print("  • 1,3,5      — скачать конкретные номера")
    print("  • 1-5        — скачать диапазон")
    print("  • 0          — отмена")
    print("=" * 65)
    
    while True:
        choice = input("\n👉 Ваш выбор (all / номера / 0): ").strip()
        if choice == '0':
            print("❌ Отменено.")
            return False
        indices = parse_selection(choice, len(audio_data))
        if indices is not None and len(indices) > 0:
            break
        print("❌ Неверный ввод. Попробуйте снова.")
    
    # Создаём подпапку по имени альбома/страницы
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', page_title or 'audio')[:60]
    album_dir = os.path.join(output_path, safe_title)
    os.makedirs(album_dir, exist_ok=True)
    
    print(f"\n📥 Буду скачивать {len(indices)} трек(ов) в папку: {album_dir}")
    
    success_count = 0
    failed_count = 0
    
    for idx in indices:
        track = audio_data[idx]
        file_path = os.path.join(album_dir, track['filename'])
        
        print(f"\n[{success_count + failed_count + 1}/{len(indices)}] 🎵 {track['title'][:50]}...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url,
            }
            response = requests.get(track['url'], headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            print(f"\r   📥 {percent:.1f}% ({downloaded_size / 1024 / 1024:.1f} MB)", end='', flush=True)
            
            print()
            if os.path.exists(file_path) and os.path.getsize(file_path) > 10 * 1024:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   ✅ Готово ({size_mb:.1f} MB)")
                success_count += 1
            else:
                print(f"   ⚠️ Файл слишком маленький")
                failed_count += 1
                
        except Exception as e:
            print(f"\n   ❌ Ошибка: {str(e)[:100]}")
            failed_count += 1
    
    print("\n" + "=" * 65)
    print(f"✅ ГОТОВО! Успешно: {success_count} | Ошибок: {failed_count}")
    print(f"📁 Папка: {os.path.abspath(album_dir)}")
    print("=" * 65)
    return success_count > 0


def download_single_audio_file_named(url, filename, output_path):
    """Скачивает один аудиофайл с заданным именем"""
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)[:80]
    file_path = os.path.join(output_path, safe_filename)
    
    print(f"\n📥 Скачиваю: {safe_filename}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
        }
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        percent = (downloaded_size / total_size) * 100
                        print(f"\r📥 {percent:.1f}% ({downloaded_size / 1024 / 1024:.1f} MB)", end='', flush=True)
        
        print()
        if os.path.exists(file_path) and os.path.getsize(file_path) > 10 * 1024:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"\n✅ ГОТОВО!")
            print(f"📁 Путь: {os.path.abspath(file_path)}")
            print(f"📊 Размер: {size_mb:.1f} MB")
            return True
        else:
            print(f"\n❌ Файл повреждён или пуст")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False


def parse_selection(input_str, total_count):
    """
    Парсит выбор пользователя: 'all', '1,3,5', '1-5', '2'.
    Возвращает список индексов (0-based) или None при ошибке.
    """
    input_str = input_str.strip().lower()
    if input_str == 'all':
        return list(range(total_count))
    if input_str == '0':
        return None
    
    indices = []
    parts = input_str.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                s, e = int(start), int(end)
                if 1 <= s <= e <= total_count:
                    indices.extend(range(s - 1, e))
                else:
                    print(f"❌ Диапазон {part} вне границ (1-{total_count})")
                    return None
            except ValueError:
                print(f"❌ Неверный диапазон: {part}")
                return None
        else:
            try:
                num = int(part)
                if 1 <= num <= total_count:
                    indices.append(num - 1)
                else:
                    print(f"❌ Номер {num} вне границ (1-{total_count})")
                    return None
            except ValueError:
                print(f"❌ Неверный номер: {part}")
                return None
    return indices

def main():
    print("=" * 50)
    print("🎬 Video Downloader v4.6")
    print("=" * 50)
    if not check_ffmpeg():
        print("\n⚠️ FFMPEG НЕ НАЙДЕН! Обрезка работать не будет.")
        print("Скачайте: https://ffmpeg.org/download.html\n")

    while True:
        print("\n📋 МЕНЮ:")
        print("1. 🎬 Видео с обрезкой (с выбором качества)")
        print("2. 📀 Плейлист (с выбором качества + звук)")
        print("3. 🎵 Аудио (YouTube, SoundCloud и др.)")
        print("4. 🎧 Аудио с ЛЮБОГО сайта (парсер)")
        print("5. 🚪 Выход")
        
        choice = input("\n👉 Выбор (1-5): ").strip()
        
        if choice == '1':
            url = input("🔗 Ссылка: ").strip()
            if url:
                download_video_with_quality_and_time(url)
        elif choice == '2':
            url = input("🔗 Ссылка на плейлист: ").strip()
            if url:
                download_playlist(url)
        elif choice == '3':
            url = input("🔗 Ссылка: ").strip()
            if url:
                download_audio(url)
        elif choice == '4':
            url = input("🔗 Ссылка на страницу с аудио: ").strip()
            if url:
                download_audio_from_generic_site(url)
        elif choice == '5':
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Ошибка: выберите от 1 до 5")


def get_audio_entries(url):
    """
    Получает список аудио-треков со страницы.
    Возвращает: (list_of_entries, is_playlist, title, total_duration)
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': False,  # Важно: разрешаем извлекать плейлисты
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(extract_video_url(url), download=False)
            if not info:
                return None, False, None, 0

            # Проверяем, это плейлист/альбом или одиночный трек
            if 'entries' in info and info['entries']:
                entries = [e for e in info['entries'] if e is not None]
                if len(entries) > 1:
                    total_dur = sum(e.get('duration', 0) or 0 for e in entries)
                    return entries, True, info.get('title', 'Альбом/Плейлист'), total_dur

            # Одиночный трек
            return [info], False, info.get('title', 'Трек'), info.get('duration', 0)

    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        return None, False, None, 0


def parse_selection(input_str, total_count):
    """
    Парсит выбор пользователя: 'all', '1,3,5', '1-5', '2'.
    Возвращает список индексов (0-based) или None при ошибке.
    """
    input_str = input_str.strip().lower()
    if input_str == 'all':
        return list(range(total_count))
    if input_str == '0':
        return None

    indices = []
    parts = input_str.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                s, e = int(start), int(end)
                if 1 <= s <= e <= total_count:
                    indices.extend(range(s - 1, e))
                else:
                    print(f"❌ Диапазон {part} вне границ (1-{total_count})")
                    return None
            except ValueError:
                print(f"❌ Неверный диапазон: {part}")
                return None
        else:
            try:
                num = int(part)
                if 1 <= num <= total_count:
                    indices.append(num - 1)
                else:
                    print(f"❌ Номер {num} вне границ (1-{total_count})")
                    return None
            except ValueError:
                print(f"❌ Неверный номер: {part}")
                return None
    return indices


def download_audio_from_site(url, output_path="downloads/music"):
    """
    Скачивание аудио с сайтов, поддерживающих альбомы/плейлисты.
    Автоматически определяет: один трек или несколько.
    """
    clean_url = extract_video_url(url)
    os.makedirs(output_path, exist_ok=True)

    print("\n Анализирую страницу...")
    entries, is_playlist, title, total_duration = get_audio_entries(clean_url)

    if not entries:
        print("⚠️ Не удалось получить аудиофайлы. Возможно, ссылка не поддерживается.")
        return False

    print(f"\n Название: {title[:60]}")
    print(f"📊 Найдено треков: {len(entries)}")
    if total_duration:
        print(f"⏱️ Общая длительность: {format_time(total_duration)}")

    # --- ОДИНОЧНЫЙ ТРЕК ---
    if not is_playlist or len(entries) == 1:
        print("\n✅ Это одиночный трек. Использую стандартное скачивание MP3.")
        return download_audio_best_quality(url, output_path)

    # --- НЕСКОЛЬКО ТРЕКОВ ---
    print("\n" + "=" * 65)
    print("📋 СПИСОК ТРЕКОВ:")
    print("=" * 65)

    for i, entry in enumerate(entries, 1):
        track_title = entry.get('title', f'Трек {i}')[:50]
        dur = format_time(entry.get('duration', 0))
        filesize = entry.get('filesize') or entry.get('filesize_approx')
        size_str = f" ({filesize / (1024 * 1024):.1f} MB)" if filesize else ""
        print(f"{i:3}. {track_title}  [{dur}]{size_str}")

    print("=" * 65)
    print("💡 Форматы выбора:")
    print("  • all        — скачать все треки")
    print("  • 1,3,5      — скачать конкретные номера")
    print("  • 1-5        — скачать диапазон")
    print("  • 1-3,7,9-11 — комбинированный выбор")
    print("  • 0          — отмена")
    print("=" * 65)

    while True:
        choice = input(f"\n Ваш выбор (all / номера / 0): ").strip()
        if choice == '0':
            print("❌ Отменено.")
            return False
        indices = parse_selection(choice, len(entries))
        if indices is not None and len(indices) > 0:
            break
        print("❌ Неверный ввод. Попробуйте снова.")

    print(f"\n📥 Буду скачивать {len(indices)} трек(ов)...")

    # Настройки для скачивания MP3
    print("\n Качество MP3 для всех треков:")
    print("1. 320 kbps")
    print("2. 192 kbps (рекомендуется)")
    print("3. 128 kbps")
    quality_choice = input("👉 Выбор (1-3): ").strip()
    mp3_quality = {'1': '320', '2': '192', '3': '128'}.get(quality_choice, '192')

    # Создаём подпапку для альбома/плейлиста
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50].strip()
    album_dir = os.path.join(output_path, safe_title)
    os.makedirs(album_dir, exist_ok=True)

    success_count = 0
    failed_count = 0

    for idx in indices:
        entry = entries[idx]
        track_title = entry.get('title', f'track_{idx + 1}')
        track_url = entry.get('webpage_url') or entry.get('url') or clean_url
        safe_track = re.sub(r'[<>:"/\\|?*]', '_', track_title)[:50].strip()
        track_path = os.path.join(album_dir, f"{safe_track}.mp3")

        print(f"\n[{success_count + failed_count + 1}/{len(indices)}] 📥 {track_title[:50]}...")

        ydl_opts = {
            'outtmpl': track_path,
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'ignoreerrors': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': mp3_quality,
            }],
        }
        if COOKIES_FILE_EXISTS():
            ydl_opts['cookiefile'] = 'cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(track_url, download=True)

            if os.path.exists(track_path) and os.path.getsize(track_path) > 100 * 1024:
                size_mb = os.path.getsize(track_path) / (1024 * 1024)
                print(f"   ✅ Готово ({size_mb:.1f} MB)")
                success_count += 1
            else:
                print(f"   ⚠️ Файл слишком маленький или не создан")
                failed_count += 1
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)[:100]}")
            failed_count += 1

    print("\n" + "=" * 65)
    print(f"✅ ГОТОВО! Успешно: {success_count} | Ошибок: {failed_count}")
    print(f"📁 Папка: {os.path.abspath(album_dir)}")
    print(f"🎧 Качество: {mp3_quality} kbps")
    print("=" * 65)
    return success_count > 0


def COOKIES_FILE_EXISTS():
    """Проверка наличия cookies.txt"""
    return os.path.exists('cookies.txt')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана. До свидания!")