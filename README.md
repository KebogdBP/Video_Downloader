<div align="center">

# 🎬 YouTube Video Downloader

### Быстрый и мощный загрузчик видео, аудио и плейлистов

Поддержка **YouTube**, **TikTok**, **Instagram**, **Vimeo**, **Twitch** и более **1000 платформ** благодаря `yt-dlp`.

<p>
<img src="https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/yt--dlp-Latest-FF0000?logo=youtube&logoColor=white" alt="yt-dlp">
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-success" alt="Platform">
<img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

</div>

---

## ✨ Возможности

* 🎥 Скачивание видео в максимальном доступном качестве
* 🎵 Конвертация видео в MP3
* 📀 Загрузка целых плейлистов
* 🌍 Поддержка более 1000 сайтов
* 🚀 Высокая скорость загрузки
* 📊 Отображение прогресса в реальном времени
* 🖥️ Простое консольное меню
* 🔧 Основан на актуальной версии `yt-dlp`

---

## 📋 Поддерживаемые платформы

| Платформа          | Поддержка |
| ------------------ | --------- |
| YouTube            | ✅         |
| YouTube Music      | ✅         |
| TikTok             | ✅         |
| Instagram          | ✅         |
| Vimeo              | ✅         |
| Twitch             | ✅         |
| Facebook           | ✅         |
| X (Twitter)        | ✅         |
| И ещё 1000+ сайтов | ✅         |

---

## 🚀 Быстрый старт

### 1. Установите Python

Скачайте Python 3.7+ с официального сайта:

https://www.python.org/downloads/

При установке обязательно включите:

```text
☑ Add Python to PATH
```

---

### 2. Установите зависимости

```bash
pip install yt-dlp
pip install yt-dlp-get-pot
pip install "yt-dlp[default,curl-cffi]"
```

Рекомендуется использовать nightly-сборку:

```bash
pip install -U --pre "yt-dlp[default,curl-cffi]"
```

---

### 3. Установите FFmpeg

FFmpeg необходим для:

* объединения видео и аудио;
* конвертации в MP3;
* обработки медиафайлов.

#### Windows

1. Скачайте FFmpeg Essentials Build
2. Распакуйте архив
3. Скопируйте `ffmpeg.exe` в:

```text
C:\Windows\System32\
```

#### Linux

```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

---

### 4. Запуск

```bash
python download_video.py
```

---

## 📸 Интерфейс программы

```text
==================================================
🎬 YouTube Video Downloader
==================================================

1. Скачать одно видео
2. Скачать плейлист
3. Скачать аудио (MP3)
4. Выход

Ваш выбор: 1

Введите ссылку:
https://youtu.be/example

📥 Скачивание: 45.2%
🚀 Скорость: 2.3 MB/s

✅ Готово!
```

---

## 📖 Использование

### Скачать одно видео

```text
1 → Скачать видео
```

Даже если ссылка принадлежит плейлисту, будет скачано только выбранное видео.

---

### Скачать плейлист

```text
2 → Скачать плейлист
```

Скачиваются все видео из списка.

---

### Скачать только аудио

```text
3 → Скачать аудио (MP3)
```

Автоматическая конвертация через FFmpeg.

---

## 🔗 Примеры ссылок

| Тип      | Пример                                |
| -------- | ------------------------------------- |
| Видео    | https://youtu.be/dQw4w9WgXcQ          |
| Плейлист | https://youtube.com/playlist?list=... |
| Канал    | https://youtube.com/@channel          |
| Shorts   | https://youtube.com/shorts/...        |

---

## ⚙️ Настройка качества видео

### Максимум 720p

```python
'format': 'best[height<=720]'
```

### Минимальное качество

```python
'format': 'worst'
```

### Максимум 1080p MP4

```python
'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best'
```

---

## 🎵 Настройка качества MP3

```python
'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',
    'preferredquality': '320'
}]
```

Поддерживаются:

* 192 kbps
* 256 kbps
* 320 kbps

---

## 📂 Структура проекта

```text
youtube-downloader/
│
├── download_video.py
├── quick_download.py
├── start.bat
├── README.md
├── requirements.txt
│
├── downloads/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── music/
│
└── .gitignore
```

---

## 🔧 Решение проблем

### No JavaScript runtime found

Установите:

* Deno (рекомендуется)
* Node.js

---

### Видео скачалось без звука

Причина:

```text
FFmpeg не установлен
```

Установите FFmpeg и повторите попытку.

---

### pip не найден

Используйте:

```bash
python -m pip install yt-dlp
```

---

### Ошибка SSL

```bash
pip install --trusted-host pypi.org \
--trusted-host files.pythonhosted.org \
yt-dlp
```

---

### Обновление yt-dlp

```bash
pip install -U yt-dlp
```

---

## 📦 Зависимости

| Пакет          | Назначение                  |
| -------------- | --------------------------- |
| Python 3.7+    | Среда выполнения            |
| yt-dlp         | Загрузка видео              |
| FFmpeg         | Конвертация и обработка     |
| yt-dlp-get-pot | Обход некоторых ограничений |

---

## 🛠 Планируемые улучшения

* GUI интерфейс
* Drag & Drop загрузка
* Поддержка прокси
* Планировщик загрузок
* Конвертация в дополнительные форматы
* Скачивание субтитров
* Интеграция с браузером

---

## 🤝 Вклад в проект

Любые улучшения приветствуются.

```bash
git checkout -b feature/my-feature
git commit -m "Add new feature"
git push origin feature/my-feature
```

После этого создайте Pull Request.

---

## 📜 Лицензия

Проект распространяется по лицензии MIT.

Подробнее:

https://opensource.org/licenses/MIT

---

## 🙏 Благодарности

* yt-dlp
* FFmpeg
* Всем участникам сообщества Open Source

---

<div align="center">

### ⭐ Если проект оказался полезным — поставьте звезду репозиторию

Made with ❤️ for the community

</div>
