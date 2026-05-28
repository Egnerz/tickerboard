# Tickerboard

Real-time stock and index overview in your browser - with automatic push to your [Ulanzi TC001](https://www.ulanzi.com/products/ulanzi-pixel-smart-clock-2882) pixel display running [AWTRIX3](https://blueforcer.github.io/awtrix3/) firmware.

![GitHub Release](https://img.shields.io/github/v/release/Egnerz/tickerboard)

![Tickerboard screenshot](static/img/screenshot-v2.png)

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

> Windows Defender may warn about an unknown publisher. Click **More info** -> **Run anyway**.

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

1. Enter the TC001's IP address in the **IP field** in the top bar
2. Click **Test** to verify the connection
3. Enable **Auto-push** in the settings row to push automatically on every refresh
4. Click **Refresh** to fetch data - tickers appear on the display immediately

---

## Features

### Ticker management

- **Add tickers** - type a symbol (e.g. `AAPL`, `^GSPC`, `TSLA`, `INVE-B.ST`) in the search bar and press Enter or click **+ Add**
- **World indices panel** - click **World indices** to open a panel with 12 major global indices grouped by flag. Click an index to stage it for adding, then click **Add selected**. Click a green index to remove it from your list immediately.
- **Remove tickers** - click the trash icon on any row to remove a ticker
- **Custom display name** - click the Display name field on any row and type a short name (e.g. `INVEB` instead of `INVE-B.ST`). This name is shown on the AWTRIX display instead of the symbol.

### Data

- Live prices via Yahoo Finance with pre-market and after-hours data
- A green dot next to the symbol means the market is actively trading right now
- The table shows: symbol, full name, display name, price, day change, and after-hours/pre-market change
- Market status badge (top right) shows the current US session: Open, Pre-market, After-hours, or Closed

### AWTRIX display

- **Auto-push** - when enabled, data is sent to the display automatically on every refresh
- **Send to device** - manual push at any time
- **Scrolling text** mode - all tickers scroll as one continuous ticker tape
- **One at a time** mode - each ticker is shown as a full-screen static card, cycling through all tickers
- When any market is actively trading (e.g. OMX30 during European hours), only the live tickers are shown on the display so the screen stays relevant
- Green color = positive change, red = negative

### Settings

All settings are saved automatically and restored on next launch.

| Setting | Description |
|---------|-------------|
| Auto-push | Automatically push to the display on every refresh |
| Every | Refresh interval (10 sec to 10 min) |
| Display | Scrolling text or one ticker at a time |
| Speed | Scroll speed (only applies to scrolling mode) |
| Brightness | Display brightness, with Night (~15%) and Day (~70%) presets |
| Language | English or Swedish |

### Light and dark mode

Click the moon/sun icon in the top-right corner to toggle between dark and light mode. The preference is saved in the browser.

---

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
