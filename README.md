# Tickerboard

Real-time stock and index overview in your browser - with automatic push to your [Ulanzi TC001](https://www.ulanzi.com/products/ulanzi-pixel-smart-clock-2882) pixel display running [AWTRIX3](https://blueforcer.github.io/awtrix3/) firmware.

![GitHub Release](https://img.shields.io/github/v/release/Egnerz/tickerboard)

![Tickerboard screenshot](static/img/screenshot.png)

[Svenska instruktioner](README.sv.md)

---

## Getting started

### Step 1 - Flash AWTRIX3 firmware on your Ulanzi TC001

The TC001 ships with its own firmware. You need to replace it with AWTRIX3 to use it with Tickerboard.

1. Connect the TC001 to your computer via USB-C
2. Open **Google Chrome** or **Microsoft Edge** (other browsers do not support Web Serial)
3. Go to the AWTRIX3 web flasher: **https://blueforcer.github.io/awtrix3/#/flasher**
4. Click **Connect**, select the TC001 serial port, and follow the on-screen steps
5. After flashing, the device reboots and opens a Wi-Fi hotspot named **AWTRIX_XXXXXX**
6. Connect your computer to that hotspot, go to **http://4.3.2.1**, enter your Wi-Fi credentials and save
7. The device connects to your network - check your router or the display itself for its IP address (e.g. `192.168.1.54`)

> **Note:** Flashing replaces the original firmware. The process is reversible - you can always re-flash the stock firmware from Ulanzi's website if needed.

#### If the web flasher does not work - use esptool

The web flasher requires a compatible browser and can sometimes fail. If it does, flash manually with esptool:

1. Install esptool: `pip install esptool`
2. Download the latest AWTRIX3 firmware `.bin` file from [github.com/Blueforcer/awtrix3/releases](https://github.com/Blueforcer/awtrix3/releases)
3. Find your serial port - on Windows it shows as `COM3` (or similar) in Device Manager, on Linux as `/dev/ttyUSB0` or `/dev/ttyACM0`
4. Erase the flash:
   ```
   esptool.py --port COM3 erase_flash
   ```
5. Flash the firmware:
   ```
   esptool.py --port COM3 write_flash 0x0 awtrix3.bin
   ```
   Replace `COM3` with your actual port and `awtrix3.bin` with the downloaded filename.
6. The device reboots and opens the `AWTRIX_XXXXXX` Wi-Fi hotspot - continue from step 5 above.

---

### Step 2 - Download Tickerboard

Get the latest release from [Releases](../../releases/latest):

| Platform | File |
|----------|------|
| Windows  | `Tickerboard.exe` |
| Linux    | `tickerboard-linux` |
| macOS    | `tickerboard-mac` |

---

### Step 3 - Run Tickerboard

**Windows**

Double-click `Tickerboard.exe`. A tray icon appears in the system tray and the browser opens automatically at `http://localhost:8000`.

> Windows Defender may warn about an unknown publisher. Click **More info** → **Run anyway**.

**Linux**
```bash
chmod +x tickerboard-linux
./tickerboard-linux
```
Then open `http://localhost:8000` in your browser.

**macOS**
```bash
chmod +x tickerboard-mac
./tickerboard-mac
```
The browser opens automatically. If macOS blocks the app, right-click it and choose **Open**, then confirm.

---

### Step 4 - Connect to your display

1. Open Tickerboard in the browser
2. Enter the TC001's IP address in the **AWTRIX IP** field
3. Check **Auto-push to device**
4. Click **↻ Refresh** - your tickers will appear on the display

---

## Features

- Live data via Yahoo Finance
- Shows price, change, pre-market and after-hours columns
- Automatically pushes to AWTRIX3 display (scrolling or paged mode)
- Prioritises actively trading markets (e.g. OMX30 in the morning before US opens)
- Adjustable display brightness with Night/Day presets
- Custom display names per ticker (e.g. `INVE-B.ST` → `Investor`)
- English and Swedish UI

## Configuration

All settings are saved automatically to `config.json` in the same folder as the binary - no manual editing needed. The file is created on first run.

---

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

**macOS:**
```bash
pip install pyinstaller
pyinstaller --onefile --name tickerboard-mac --add-data "static:static" main_mac.py
```

**Run in dev mode:**
```bash
uvicorn app:app --reload --port 8000
```
