import yt_dlp
import os
import re
import subprocess
import shutil
import uuid

def extract_video_url(url):
    """Извлекает ТОЛЬКО URL видео"""
    if 'list=' in url:
        url = re.sub(r'[&?]list=[^&]+', '', url)
    if 'start_radio=' in url:
        url = re.sub(r'[&?]start_radio=[^&]+', '', url)
    if 'index=' in url:
        url = re.sub(r'[&?]index=[^&]+', '', url)
    return url

def get_all_formats(url):
    """Получает все доступные форматы видео"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            clean_url = extract_video_url(url)
            info = ydl.extract_info(clean_url, download=False)
            
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
                    if has_audio:
                        quality_key += " ✓ со звуком"
                    else:
                        quality_key += " ✗ только видео"
                    
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
        print(f"❌ Ошибка: {e}")
        return None, None, 0

def display_all_formats(qualities):
    """Отображает все доступные форматы"""
    if not qualities:
        print("❌ Нет доступных форматов")
        return False
    
    print("\n📺 Доступные качества:")
    print("-" * 65)
    
    for i, (quality_name, info) in enumerate(qualities, 1):
        size_str = ""
        if info.get('filesize'):
            size_mb = info['filesize'] / (1024 * 1024)
            size_str = f" ({size_mb:.1f} MB)"
        
        print(f"{i:2}. {quality_name}{size_str}")
    
    print("-" * 65)
    print("0. Отмена")
    return True

def parse_time(time_str):
    """Преобразует строку времени в секунды"""
    if time_str is None or time_str.strip() == "":
        return None
    
    time_str = time_str.strip()
    
    if time_str.isdigit():
        return int(time_str)
    
    parts = time_str.split(':')
    
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        raise ValueError(f"Неверный формат: {time_str}")

def format_time(seconds):
    """Преобразует секунды в формат MM:SS или HH:MM:SS"""
    if seconds is None:
        return "???"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def cut_video_sync(input_path, output_path, start_time, end_time):
    """
    Обрезка видео с ПРАВИЛЬНОЙ синхронизацией аудио и видео
    Используется точное перекодирование
    """
    print(f"\n✂️ Обрезка видео с синхронизацией...")
    print(f"   Начало: {format_time(start_time) if start_time else '00:00'}")
    print(f"   Конец: {format_time(end_time) if end_time else 'конец'}")
    
    if start_time is not None and end_time is not None:
        cut_duration = end_time - start_time
        print(f"   Длина: {format_time(cut_duration)}")
    
    # Получаем директорию
    dir_name = os.path.dirname(input_path)
    if not dir_name:
        dir_name = "."
    
    # Временный файл для обработки
    temp_output = os.path.join(dir_name, f"temp_cut_{uuid.uuid4().hex[:8]}.mp4")
    
    # Строим команду FFmpeg для точной обрезки с перекодированием
    # Важно: -ss ставим ДО -i для точного поиска
    # -avoid_negative_ts make_zero - исправляет временные метки
    # -async 1 - синхронизирует аудио
    # -vsync cfr - синхронизирует видео
    
    if start_time is not None and end_time is not None:
        duration = end_time - start_time
        cmd = (
            f'ffmpeg -ss {start_time} -i "{input_path}" '
            f'-t {duration} '
            f'-c:v libx264 -preset medium -crf 18 '
            f'-c:a aac -b:a 192k '
            f'-avoid_negative_ts make_zero '
            f'-async 1 -vsync cfr '
            f'-movflags +faststart '
            f'-y "{temp_output}"'
        )
    elif start_time is not None:
        cmd = (
            f'ffmpeg -ss {start_time} -i "{input_path}" '
            f'-c:v libx264 -preset medium -crf 18 '
            f'-c:a aac -b:a 192k '
            f'-avoid_negative_ts make_zero '
            f'-async 1 -vsync cfr '
            f'-movflags +faststart '
            f'-y "{temp_output}"'
        )
    elif end_time is not None:
        cmd = (
            f'ffmpeg -i "{input_path}" '
            f'-t {end_time} '
            f'-c:v libx264 -preset medium -crf 18 '
            f'-c:a aac -b:a 192k '
            f'-avoid_negative_ts make_zero '
            f'-async 1 -vsync cfr '
            f'-movflags +faststart '
            f'-y "{temp_output}"'
        )
    else:
        return False
    
    print(f"   🔄 Выполняется точная обрезка (может занять время)...")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            # Копируем результат в целевой файл
            shutil.copy2(temp_output, output_path)
            print("   ✅ Видео успешно обрезано и синхронизировано!")
            
            # Удаляем временный файл
            try:
                os.remove(temp_output)
            except:
                pass
            return True
        else:
            print(f"   ❌ Ошибка FFmpeg")
            if result.stderr:
                print(f"   Ошибка: {result.stderr[:300]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False

def download_video_with_quality_and_time(url, output_path="downloads"):
    """Скачивание видео с выбором качества и точной обрезкой"""
    
    clean_url = extract_video_url(url)
    
    # Получаем информацию о видео
    print("\n🔍 Получаю информацию о видео...")
    result = get_all_formats(clean_url)
    
    if not result or not result[0]:
        print("⚠️ Не удалось получить список качеств.")
        return False
    
    qualities, video_title, duration = result
    
    print(f"\n📹 Видео: {video_title[:60]}")
    print(f"⏱️ Длительность: {format_time(duration)}")
    
    # Выбор качества
    display_all_formats(qualities)
    
    selected_format_id = None
    selected_quality_name = None
    selected_has_audio = None
    
    while True:
        try:
            choice = input(f"\n👉 Выберите качество (1-{len(qualities)} или 0): ").strip()
            
            if choice == '0':
                print("❌ Отменено")
                return False
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(qualities):
                selected = qualities[choice_num - 1]
                selected_quality_name, quality_info = selected
                selected_format_id = quality_info['format_id']
                selected_has_audio = quality_info['has_audio']
                print(f"\n✅ Выбрано: {selected_quality_name}")
                break
            else:
                print(f"❌ Введите число от 1 до {len(qualities)}")
        except ValueError:
            print("❌ Введите число")
    
    # Запрос времени
    print("\n✂️ Обрезка видео")
    print("Форматы:")
    print("  • Секунды: 125")
    print("  • Минуты:секунды: 2:05")
    print("  • Часы:минуты:секунды: 1:30:45")
    print("  • Оставьте пустым для пропуска")
    
    start_time = None
    end_time = None
    
    # Начальное время
    while True:
        start_input = input(f"\n⏱️ Начальное время (0-{format_time(duration)}): ").strip()
        if start_input == "":
            break
        try:
            start_time = parse_time(start_input)
            if start_time < 0:
                print("❌ Не может быть отрицательным")
                continue
            if start_time > duration:
                print(f"❌ Не может быть больше {format_time(duration)}")
                continue
            break
        except ValueError as e:
            print(f"❌ {e}")
    
    # Конечное время
    while True:
        end_input = input(f"⏱️ Конечное время (0-{format_time(duration)}): ").strip()
        if end_input == "":
            break
        try:
            end_time = parse_time(end_input)
            if end_time < 0:
                print("❌ Не может быть отрицательным")
                continue
            if end_time > duration:
                print(f"❌ Не может быть больше {format_time(duration)}")
                continue
            if start_time is not None and end_time <= start_time:
                print("❌ Конечное время должно быть больше начального")
                continue
            break
        except ValueError as e:
            print(f"❌ {e}")
    
    # Проверка: нужно ли обрезать
    need_cut = (start_time is not None and start_time > 0) or (end_time is not None and end_time < duration)
    
    if need_cut and start_time is not None and end_time is not None:
        print(f"\n📊 Будет вырезан отрезок:")
        print(f"   С {format_time(start_time)} по {format_time(end_time)}")
        print(f"   Длина: {format_time(end_time - start_time)}")
    elif need_cut:
        print(f"\n📊 Будет обрезано видео")
    
    # Создаём папку
    os.makedirs(output_path, exist_ok=True)
    
    # Используем временное имя для скачивания
    temp_id = uuid.uuid4().hex[:8]
    temp_filename = f"temp_video_{temp_id}.mp4"
    temp_path = os.path.join(output_path, temp_filename)
    
    # Финальное имя
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
    if need_cut:
        time_start = format_time(start_time) if start_time else "00:00"
        time_end = format_time(end_time) if end_time else "конец"
        final_filename = f"{safe_title} [{time_start}-{time_end}].mp4"
    else:
        final_filename = f"{safe_title}.mp4"
    
    final_path = os.path.join(output_path, final_filename)
    
    # Формат для скачивания
    if selected_has_audio:
        format_spec = selected_format_id
    else:
        print("\n⚠️ Выбранный формат без звука, добавляю аудиодорожку...")
        format_spec = f'{selected_format_id}+bestaudio/best'
    
    download_opts = {
        'outtmpl': temp_path,
        'format': format_spec,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': False,
        'noplaylist': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            print(f"\n📥 Скачиваю видео...\n")
            ydl.extract_info(clean_url, download=True)
        
        # Проверяем, существует ли временный файл
        if not os.path.exists(temp_path):
            # Ищем любой mp4 файл во временной папке
            for file in os.listdir(output_path):
                if file.endswith('.mp4') and 'temp_video' in file:
                    temp_path = os.path.join(output_path, file)
                    break
            else:
                print(f"❌ Не найден скачанный файл")
                return False
        
        if need_cut and os.path.exists(temp_path):
            # Обрезка с синхронизацией
            success = cut_video_sync(temp_path, final_path, start_time, end_time)
            
            if success and os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                # Удаляем временный файл
                try:
                    os.remove(temp_path)
                except:
                    pass
                print(f"\n✅ ГОТОВО! Видео успешно обрезано и синхронизировано!")
            else:
                print(f"\n⚠️ Обрезка не удалась, сохраняю полное видео")
                if os.path.exists(temp_path):
                    shutil.copy2(temp_path, final_path)
        else:
            # Просто переименовываем
            if temp_path != final_path and os.path.exists(temp_path):
                shutil.copy2(temp_path, final_path)
            print(f"\n✅ ГОТОВО! Видео скачано полностью!")
        
        # Удаляем временный файл
        try:
            if os.path.exists(temp_path) and temp_path != final_path:
                os.remove(temp_path)
        except:
            pass
        
        print(f"📁 Папка: {output_path}")
        print(f"📹 Файл: {final_filename}")
        
        if os.path.exists(final_path):
            file_size = os.path.getsize(final_path) / (1024 * 1024)
            print(f"📊 Размер: {file_size:.1f} MB")
        
        return True
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def download_video_best_quality(url, output_path="downloads"):
    """Быстрое скачивание в лучшем качестве"""
    clean_url = extract_video_url(url)
    os.makedirs(output_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': False,
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n📥 Скачиваю в лучшем качестве...\n")
            ydl.extract_info(clean_url, download=True)
            print(f"\n✅ Готово!")
            return True
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def download_playlist(url, output_path="downloads"):
    """Скачивание плейлиста"""
    clean_url = extract_video_url(url)
    os.makedirs(output_path, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(playlist_title)s', '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'ignoreerrors': True,
        'quiet': False,
        'noplaylist': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n📀 Скачиваю плейлист...")
            ydl.extract_info(clean_url, download=True)
            print(f"\n✅ Готово!")
            return True
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def download_audio(url, output_path="downloads/music"):
    """Скачивание аудио в MP3"""
    clean_url = extract_video_url(url)
    os.makedirs(output_path, exist_ok=True)
    
    print("\n🎵 Качество MP3:")
    print("1. 320 kbps")
    print("2. 192 kbps (рекомендуется)")
    print("3. 128 kbps")
    
    quality_choice = input("👉 Выбор (1-3): ").strip()
    mp3_quality = {'1': '320', '2': '192', '3': '128'}.get(quality_choice, '192')
    
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
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
            print(f"\n🎵 Скачиваю MP3...\n")
            ydl.extract_info(clean_url, download=True)
            print(f"\n✅ Готово!")
            return True
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False

def progress_hook(d):
    if d['status'] == 'downloading':
        if d.get('total_bytes'):
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100
            speed = d.get('_speed_str', '?')
            eta = d.get('_eta_str', '?')
            print(f"\r📥 {percent:.1f}% - {speed} - ост. {eta}", end='')
    elif d['status'] == 'finished':
        print("\n🔧 Обработка...")

def main():
    print("=" * 65)
    print("🎬 YouTube Downloader v3.7 - ИСПРАВЛЕНА СИНХРОНИЗАЦИЯ")
    print("=" * 65)
    print("\n💡 Теперь аудио и видео синхронизированы при обрезке!")
    
    # Проверка FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        print("✅ FFmpeg найден")
    except:
        print("\n⚠️ FFMPEG НЕ НАЙДЕН!")
        print("Обрезка НЕ БУДЕТ работать!")
        print("Скачайте FFmpeg: https://ffmpeg.org/download.html\n")
    
    while True:
        print("\n📋 Меню:")
        print("1. 📹 Скачать видео (с обрезкой и синхронизацией)")
        print("2. 🚀 Скачать видео (лучшее качество)")
        print("3. 📀 Скачать плейлист")
        print("4. 🎵 Скачать MP3")
        print("5. 🚪 Выход")
        
        choice = input("\n👉 Выбор (1-5): ").strip()
        
        if choice == '1':
            url = input("🔗 Ссылка: ").strip()
            if url:
                download_video_with_quality_and_time(url)
            else:
                print("❌ Введите ссылку")
        elif choice == '2':
            url = input("🔗 Ссылка: ").strip()
            if url:
                download_video_best_quality(url)
        elif choice == '3':
            url = input("🔗 Ссылка на плейлист: ").strip()
            if url:
                download_playlist(url)
        elif choice == '4':
            url = input("🔗 Ссылка: ").strip()
            if url:
                download_audio(url)
        elif choice == '5':
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Выберите 1-5")

if __name__ == "__main__":
    main()