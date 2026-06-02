<div align="center">
  
# 🎬 YouTube Video Downloader

### Мощный загрузчик видео с YouTube и 1000+ других сайтов

[![Python](https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-green?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Windows](https://img.shields.io/badge/Windows-10%2B-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Оглавление

- [✨ Возможности](#-возможности)
- [📸 Скриншоты](#-скриншоты)
- [🚀 Быстрый старт](#-быстрый-старт)
- [📖 Использование](#-использование)
- [⚙️ Настройка](#️-настройка)
- [🔧 Решение проблем](#-решение-проблем)
- [📁 Структура проекта](#-структура-проекта)

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🎥 **Скачивание видео** | Лучшее качество (до 4K/8K) в MP4 формате |
| 🎵 **Только аудио** | Конвертация в MP3 (192kbps) |
| 📀 **Плейлисты** | Скачивание целых плейлистов и каналов |
| 🌍 **1000+ сайтов** | YouTube, Vimeo, Twitch, TikTok, Instagram и другие |
| 📝 **Субтитры** | Автоматические и ручные субтитры |
| 🚀 **Высокая скорость** | Многопоточная загрузка |
| 💾 **Прогресс** | Визуальный индикатор загрузки |

---

## 📸 Скриншоты

```bash
==================================================
🎬 YouTube Video Downloader
==================================================

Выберите действие:
1. Скачать видео (ОДНО, даже из плейлиста)
2. Скачать плейлист (ВСЕ видео)
3. Скачать только аудио (MP3)
4. Выход

Ваш выбор (1-4): 1
Введите ссылку на видео или плейлист: https://youtu.be/...

🎬 Начинаю скачивание: https://youtu.be/...

📥 Скачивание: 45.2% - 2.3MB/s - осталось 00:15
🔧 Обработка видео...

✅ Готово! Видео сохранено в папку 'downloads'
📹 Название: My Awesome Video

# 🚀 Быстрый старт
Установка
1. Установите Python
Скачайте Python 3.7+ с официального сайта

⚠️ Важно: При установке обязательно поставьте галочку "Add Python to PATH"

2. Скачайте программу
Скачайте файл download_video.py из этого репозитория

3. Установите зависимости
Откройте командную строку и выполните:

bash
pip install yt-dlp
pip install yt-dlp yt-dlp-get-pot
pip install "yt-dlp[default,curl-cffi]

3.1 Обновите yt-dlp до последней nightly версии

bash
pip install -U --pre "yt-dlp[default,curl-cffi]

4. Установите FFmpeg (рекомендуется)
Windows:

Скачайте FFmpeg Essentials Build

Распакуйте архив

Скопируйте ffmpeg.exe из папки bin в C:\Windows\System32\

Linux:

bash
sudo apt update && sudo apt install ffmpeg
macOS:

bash
brew install ffmpeg
Первый запуск
bash
python download_video.py
Создайте удобный ярлык (Windows)
Создайте файл start.bat в той же папке:

batch
@echo off
python download_video.py
pause
Теперь можно запускать двойным кликом на start.bat

## 📖 Использование
Интерактивный режим
Запустите программу и выберите действие:

Клавиша	Действие
1	Скачать одно видео (даже из плейлиста)
2	Скачать весь плейлист
3	Скачать только аудио (MP3)
4	Выход
Примеры ссылок
Что скачать	Пример ссылки
Одно видео	https://youtu.be/dQw4w9WgXcQ
Плейлист	https://youtube.com/playlist?list=...
Канал	https://youtube.com/c/ChannelName
Быстрое скачивание (для продвинутых)
Создайте файл quick.py:

python
import yt_dlp
import sys

url = sys.argv[1] if len(sys.argv) > 1 else input("URL: ")

ydl_opts = {
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
Использование:

bash
python quick.py "https://youtu.be/..."
## ⚙️ Настройка
Изменение качества видео
Отредактируйте параметр format в файле download_video.py:

python
# Максимум 720p
'format': 'best[height<=720]'

# Самое низкое качество
'format': 'worst'

# Конкретный формат (например, 1080p MP4)
'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
Изменение папки загрузки
python
# Абсолютный путь
'outtmpl': 'C:/Users/Ваше_Имя/Videos/%(title)s.%(ext)s'

# Относительный путь
'outtmpl': 'my_videos/%(title)s.%(ext)s'
Скачивание субтитров
Добавьте в настройки:

python
ydl_opts = {
    # ... остальные настройки ...
    'writesubtitles': True,
    'subtitleslangs': ['ru', 'en'],  # русские и английские
    'writeautomaticsub': True,  # автоматические субтитры
}
Настройка качества MP3
python
'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',
    'preferredquality': '320',  # 192, 256, 320
}]
## 🔧 Решение проблем
❌ Ошибка: "No JavaScript runtime found"
Причина: YouTube требует JavaScript для работы

Решение: Установите Deno или Node.js

bash
# Deno (рекомендуется)
# Скачайте с https://deno.com/

# Или Node.js
# Скачайте с https://nodejs.org/
❌ Ошибка: "This video is not available"
Возможные причины:

Видео удалено или приватное

Региональное ограничение

Неправильная ссылка

Решение:

bash
# Обновите yt-dlp
pip install -U yt-dlp

# Попробуйте другой клиент в коде
'player_client': ['ios', 'android']  # вместо 'android', 'web'
❌ Видео скачалось без звука
Причина: Отсутствует FFmpeg для объединения видео и аудио

Решение: Установите FFmpeg (см. раздел "Быстрый старт")

❌ Команда 'pip' не распознана
Решение: Используйте полную команду

bash
python -m pip install yt-dlp
❌ Ошибка SSL
Решение:

bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org yt-dlp
❌ Медленная загрузка
Решение: Ограничьте скорость или используйте прокси

python
ydl_opts = {
    # Ограничение скорости (в байтах/сек)
    'ratelimit': 1024 * 1024,  # 1 MB/s
    
    # Использование прокси
    'proxy': 'socks5://127.0.0.1:1080',
}
📁 Структура проекта
text
youtube-downloader/
│
├── download_video.py          # Главная программа
├── quick_download.py          # Быстрое скачивание (опционально)
├── start.bat                  # Запуск на Windows
├── README.md                  # Документация
├── requirements.txt           # Зависимости
│
├── downloads/                 # Папка с загрузками
│   ├── video1.mp4
│   ├── video2.mp4
│   └── music/
│       └── song.mp3
│
└── .gitignore                 # Игнорируемые файлы (для Git)

## 📦 Зависимости
Python 3.7 или выше

yt-dlp - основной движок загрузки

FFmpeg - для объединения видео/аудио и конвертации (рекомендуется)

🤝 Вклад в проект
Хотите улучшить проект? Отлично!

Форкните репозиторий

Создайте ветку (git checkout -b feature/amazing-feature)

Сделайте коммит (git commit -m 'Add amazing feature')

Запушьте (git push origin feature/amazing-feature)

Откройте Pull Request

Идеи для улучшения:
GUI интерфейс на Tkinter/PyQt

Планировщик загрузок

Поддержка прокси

Конвертация в другие форматы

Скачивание только субтитров

Интеграция с браузером

## 📜 Лицензия
Распространяется под лицензией MIT.

text
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions...

Полный текст лицензии: https://opensource.org/licenses/MIT
## 🙏 Благодарности
yt-dlp - за мощный движок загрузки

FFmpeg - за обработку медиафайлов

Всем контрибьюторам и пользователям

<div align="center">
## 🌟 Если этот проект помог вам, поставьте звезду на GitHub!
Вопросы и предложения: Создать Issue

Сделано с ❤️ для сообщества

</div> ```
