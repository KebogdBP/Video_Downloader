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

```bash
start.bat
```
---

## 📸 Интерфейс программы

```text
==================================================
🎬 Video Downloader v4.5
==================================================
✅ FFmpeg готов

📋 МЕНЮ:
1. 🎬 Видео с обрезкой (с выбором качества)
2. 📀 Плейлист (с выбором качества + звук)
3. 🎵 Аудио
4. 🚪 Выход

👉 Выбор (1,2,3,4):

🔗 Ссылка:
https://youtu.be/example

📹 Видео: "Имя видео на сайте"
⏱️ Длительность: 03:36

📺 Доступные качества:
-----------------------------------------------------------------
 1. 144p ✓ со звуком
 2. 144p ✗ только видео (2.6 MB)
 3. 240p ✓ со звуком
 4. 240p ✗ только видео (5.6 MB)
 5. 360p ✓ со звуком
 6. 360p ✗ только видео (11.4 MB)
 7. 480p ✓ со звуком
 8. 480p ✗ только видео (22.7 MB)
 9. 720p ✓ со звуком
10. 720p ✗ только видео (43.2 MB)
11. 1080p ✓ со звуком
12. 1080p ✗ только видео (83.5 MB)
13. 1440p ✗ только видео (132.9 MB)
14. 2160p ✗ только видео (271.6 MB)
-----------------------------------------------------------------
0. Отмена

#Звук добавляется везде

👉 Выберите качество (1-14 или 0): 11

✅ Выбрано: 1080p ✓ со звуком

✂️ Обрезка (оставьте пустым для скачивания полного файла). Формат: 125 или 2:05 или 1:30:45
⏱️ Начальное время (0-03:36): 1:00
⏱️ Конечное время (0-03:36): 1:10

📊 Будет вырезан отрезок: с 01:00 по 01:10 

#Для удобства скачивается полностью оригинал

📥 Скачиваю видео...

📥 Скачивание: 45.2% | 🚀 Скорость: 2.3 MB/s

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
