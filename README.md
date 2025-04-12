# 🎥 DeepSubTranslator

Automatically extract subtitle from video files, translate them to desire language using DeepSeek API, and embed the translated subtitles back into the video — all with progress tracking and Docker support.

---

## 🚀 Features

✅ Accepts video file or directory (recursive scan)  
✅ Skips videos that already contain Thai subtitles  
✅ Extracts embedded English subtitles (e.g. `eng`, `en`, `english`)  
✅ Translates subtitles using [DeepSeek Chat API](https://api-docs.deepseek.com/)  
✅ Ensures translation is length-appropriate and tone-consistent  
✅ Embeds Thai subtitles back into the video using `ffmpeg`  
✅ Progress bar using `rich`  
✅ Fully Dockerized  
✅ Unit and Integration Tested  
✅ GitHub Actions CI

---

## 🧰 Requirements

- Python 3.10+
- `ffmpeg`, `mkvtoolnix` (for video and subtitle processing)
- A valid DeepSeek API key

Install dependencies:

```bash
pip install -r requirements.txt
```

## 🐳 Run with Docker

Build image

```bash
sh build_image.sh
```

Run the translator

```bash
sh run.sh /path/to/video/or/folder [source_lang] [target_lang]
```

Example:

```bash
# you can run the scipt like this:
sh run.sh ./videos               # uses default eng -> tha
sh run.sh ./movie.mkv            # for a single file
sh run.sh ./videos eng tha       # explicitly specify languages
sh run.sh ./video.mp4 eng jpn    # translate from English to Japanese
```

## 🧪 Running Tests

Unit + Integration Tests

```bash
pytest tests/
```

## ⚙️ Configuration

You can optionally use a YAML config file:

```yaml
# config/deepseek.yml
api_key: YOUR_API_KEY
endpoint: https://api.deepseek.com/chat
model: deepseek-chat
system_prompt:
  description: "Translate from {source_language} to {target_language}."
  variables:
    source_language: "English"
    target_language: "Thai"
```

## 🧠 Project Structure

```bash
.
├── main.py                  # Main entrypoint
├── run.sh                   # Shell runner script for Docker container
├── build_image.sh           # Shell script for build docker image
├── utils/                   # All core logic (SRP-compliant)
│   ├── video_handler.py
│   ├── subtitle_handler.py
│   ├── file_utils.py
│   └── deepseek.py
├── tests/                   # Unit & integration tests
│   ├── test_*.py
│   └── assets/              # Test video + subtitles
├── Dockerfile
├── requirements.txt
└── README.md
```

## 📬 License

MIT License – do whatever you want, but please give credit if it helps you 🙌

## 🤝 Contributing

Pull requests welcome!
Feel free to file issues, suggest improvements, or ask questions.
