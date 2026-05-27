# Tickerboard

Real-time stock and index overview in your browser — with automatic push to your [AWTRIX3](https://blueforcer.github.io/awtrix3/) display.

## Download

Get the latest release from [Releases](../../releases/latest):

| Platform | File |
|----------|------|
| Windows  | `Tickerboard.exe` |
| Linux    | `tickerboard-linux` |

### Windows
Double-click `Tickerboard.exe`. A tray icon appears and the browser opens automatically at `http://localhost:8000`. Right-click the tray icon to open or quit.

> **Note:** Windows Defender may warn about an unknown publisher. Click "More info" → "Run anyway".

### Linux
```bash
chmod +x tickerboard-linux
./tickerboard-linux
```
Then open `http://localhost:8000` in your browser.

## Features

- Live data via Yahoo Finance
- Shows price, change, pre-market and after-hours columns
- Automatically pushes to AWTRIX3 display (scrolling or paged mode)
- Prioritises actively trading markets (e.g. OMX30 in the morning before US opens)
- Adjustable display brightness with Night/Day presets
- Custom display names per ticker (e.g. `INVE-B.ST` → `Investor`)
- English and Swedish labels

## Configuration

Settings are saved automatically to `config.json` (created on first run) in the same folder as the binary. No code changes needed.

## Building from source

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

**Windows:**
```
build.bat
```

**Linux:**
```bash
pip install pyinstaller
pyinstaller --onefile --name tickerboard-linux --add-data "static:static" main_linux.py
```

**Run in dev mode:**
```bash
uvicorn app:app --reload --port 8000
```
