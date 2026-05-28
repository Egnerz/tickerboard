# Tickerboard

Realtidsöversikt för aktier och index i webbläsaren - med automatisk push till din [Ulanzi TC001](https://www.ulanzi.com/products/ulanzi-pixel-smart-clock-2882) pixeldisplay som kör [AWTRIX3](https://blueforcer.github.io/awtrix3/)-firmware.

![GitHub Release](https://img.shields.io/github/v/release/Egnerz/tickerboard)

![Tickerboard skärmbild](static/img/screenshot.png)

[English instructions](README.md)

---

## Kom igång

### Steg 1 - Flasha AWTRIX3-firmware på din Ulanzi TC001

TC001 levereras med sin egen firmware. Du behöver ersätta den med AWTRIX3 för att använda Tickerboard.

1. Anslut TC001 till datorn via USB-C
2. Öppna **Google Chrome** eller **Microsoft Edge** (andra webbläsare stöder inte Web Serial)
3. Gå till AWTRIX3 web flasher: **https://blueforcer.github.io/awtrix3/#/flasher**
4. Klicka **Connect**, välj TC001:s serieport och följ stegen på skärmen
5. Efter flashningen startar enheten om och öppnar en Wi-Fi-hotspot med namnet **AWTRIX_XXXXXX**
6. Anslut datorn till den hotspoten, gå till **http://4.3.2.1**, ange dina Wi-Fi-uppgifter och spara
7. Enheten ansluter till ditt nätverk - kolla routern eller displayen för att hitta IP-adressen (t.ex. `192.168.1.54`)

> **Obs:** Flashningen ersätter den ursprungliga firmware. Det går att återställa - du kan alltid flasha tillbaka originalfirmware från Ulanzis webbplats.

#### Om web flashern inte fungerar - använd esptool

Web flashern kräver en kompatibel webbläsare och kan ibland misslyckas. I så fall kan du flasha manuellt med esptool:

1. Installera esptool: `pip install esptool`
2. Ladda ner den senaste AWTRIX3-firmware som `.bin`-fil från [github.com/Blueforcer/awtrix3/releases](https://github.com/Blueforcer/awtrix3/releases)
3. Hitta din serieport - på Windows visas den som `COM3` (eller liknande) i Enhetshanteraren, på Linux som `/dev/ttyUSB0` eller `/dev/ttyACM0`
4. Radera flashminnet:
   ```
   esptool.py --port COM3 erase_flash
   ```
5. Flasha firmware:
   ```
   esptool.py --port COM3 write_flash 0x0 awtrix3.bin
   ```
   Ersätt `COM3` med din faktiska port och `awtrix3.bin` med det nedladdade filnamnet.
6. Enheten startar om och öppnar `AWTRIX_XXXXXX`-hotspoten - fortsätt sedan från steg 5 ovan.

---

### Steg 2 - Ladda ner Tickerboard

Hämta senaste versionen under [Releases](../../releases/latest):

| Plattform | Fil |
|-----------|-----|
| Windows   | `Tickerboard.exe` |
| Linux     | `tickerboard-linux` |
| macOS     | `tickerboard-mac` |

---

### Steg 3 - Kör Tickerboard

**Windows**

Dubbelklicka på `Tickerboard.exe`. En ikon visas i systemfältet och webbläsaren öppnas automatiskt på `http://localhost:8000`.

> Windows Defender kan varna om okänd utgivare. Klicka **Mer information** och sedan **Kör ändå**.

**Linux**
```bash
chmod +x tickerboard-linux
./tickerboard-linux
```
Öppna sedan `http://localhost:8000` i webbläsaren.

**macOS**
```bash
chmod +x tickerboard-mac
./tickerboard-mac
```
Webbläsaren öppnas automatiskt. Om macOS blockerar appen, högerklicka och välj **Öppna**, bekräfta sedan.

---

### Steg 4 - Anslut till displayen

1. Öppna Tickerboard i webbläsaren
2. Ange TC001:s IP-adress i fältet **AWTRIX IP**
3. Kryssa i **Auto-push to device**
4. Klicka **Refresh** - dina tickers visas nu på displayen

---

## Funktioner

- Livedata via Yahoo Finance
- Visar pris, förändring, förhandel och efterhandel
- Pushar automatiskt till AWTRIX3-display (rullande text eller en ticker åt gången)
- Prioriterar aktivt handlade marknader (t.ex. OMX30 på morgonen innan USA öppnar)
- Justerbar ljusstyrka med natt- och dagläge
- Anpassade visningsnamn per ticker (t.ex. `INVE-B.ST` blir `Investor`)
- Stöd för svenska och engelska etiketter

## Inställningar

Alla inställningar sparas automatiskt i `config.json` i samma mapp som programmet - inga manuella ändringar behövs. Filen skapas vid första start.

---

## Bygg från källkod

Kräver Python 3.10+.

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

**Kör i dev-läge:**
```bash
uvicorn app:app --reload --port 8000
```
