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

def main():
    print("=" * 50)
    print("🎬 Video Downloader v4.5")
    print("=" * 50)
    
    if not check_ffmpeg():
        print("\n⚠️ FFMPEG НЕ НАЙДЕН! Обрезка работать не будет.")
        print("Скачайте: https://ffmpeg.org/download.html\n")
    
    while True:
        print("\n📋 МЕНЮ:")
        print("1. 🎬 Видео с обрезкой (с выбором качества)")
        print("2. 📀 Плейлист (с выбором качества + звук)")
        print("3. 🎵 Аудио")
        print("4. 🚪 Выход")
        
        choice = input("\n👉 Выбор (1,2,3,4): ").strip()
        
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
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Ошибка: выберите 1, 2, 3 или 4")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана. До свидания!")