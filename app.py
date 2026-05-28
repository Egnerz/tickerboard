import json
import os
import sys
import time
import urllib.request
import threading
from datetime import datetime, timezone, timedelta, date
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# ── Delad datakache — browser och enhet läser alltid samma fetch ──────────────
_cache_lock = threading.Lock()
_cache = {"quotes": None, "status": None, "fetched_at": 0.0}

def _refresh_cache():
    config = load_config()
    quotes = fetch_quotes(config["tickers"])
    status = get_market_status()
    with _cache_lock:
        _cache["quotes"] = quotes
        _cache["status"] = status
        _cache["fetched_at"] = time.time()
    return quotes, status

def get_cached_quotes(max_age: float = 20.0):
    """Returnerar cachad data om den är färskare än max_age sekunder, annars hämtar nytt."""
    with _cache_lock:
        age = time.time() - _cache["fetched_at"]
        if _cache["quotes"] is not None and age < max_age:
            return _cache["quotes"], _cache["status"]
    return _refresh_cache()

# ── Bakgrundsjobb ──────────────────────────────────────────
_push_timer: threading.Timer | None = None

def _schedule_push():
    global _push_timer
    config = load_config()
    try:
        quotes, status = _refresh_cache()
        if config.get("awtrix_enabled") and config.get("awtrix_ip"):
            push_all_to_awtrix(
                config["awtrix_ip"], quotes, status,
                config.get("language", "en"),
                config.get("display_mode", "scroll"),
                config.get("page_duration", 5),
                config.get("scroll_speed", 40),
                config.get("refresh_interval", 60),
                config.get("ticker_names", {}),
            )
    except Exception:
        pass
    interval = max(10, config.get("refresh_interval", 60))
    _push_timer = threading.Timer(interval, _schedule_push)
    _push_timer.daemon = True
    _push_timer.start()

@app.on_event("startup")
def start_background_push():
    _schedule_push()

# When frozen by PyInstaller, config lives next to the .exe; in dev, next to app.py
if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
    _static_dir = os.path.join(sys._MEIPASS, "static")
else:
    _base_dir = os.path.dirname(os.path.realpath(__file__))
    _static_dir = os.path.join(_base_dir, "static")

CONFIG_FILE = os.path.join(_base_dir, "config.json")

DEFAULT_INDICES = [
    {"symbol": "^GSPC",  "flag": "🇺🇸", "name": "S&P 500"},
    {"symbol": "^NDX",   "flag": "🇺🇸", "name": "NASDAQ-100"},
    {"symbol": "^DJI",   "flag": "🇺🇸", "name": "Dow Jones"},
    {"symbol": "^OMX",   "flag": "🇸🇪", "name": "OMX Stockholm 30"},
    {"symbol": "^FTSE",  "flag": "🇬🇧", "name": "FTSE 100"},
    {"symbol": "^GDAXI", "flag": "🇩🇪", "name": "DAX"},
    {"symbol": "^FCHI",  "flag": "🇫🇷", "name": "CAC 40"},
    {"symbol": "^N225",  "flag": "🇯🇵", "name": "Nikkei 225"},
    {"symbol": "^HSI",   "flag": "🇭🇰", "name": "Hang Seng"},
    {"symbol": "^BSESN", "flag": "🇮🇳", "name": "BSE Sensex"},
    {"symbol": "^AXJO",  "flag": "🇦🇺", "name": "ASX 200"},
    {"symbol": "^KS11",  "flag": "🇰🇷", "name": "KOSPI"},
]
DEFAULT_TICKERS = [i["symbol"] for i in DEFAULT_INDICES]

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"tickers": list(DEFAULT_TICKERS), "awtrix_ip": "", "awtrix_enabled": False, "refresh_interval": 60, "ticker_names": {}, "awtrix_brightness": 50}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_market_status():
    et = timezone(timedelta(hours=-4))  # EDT, ändra till -5 vintertid
    now = datetime.now(et)
    if now.weekday() >= 5:
        return "closed"
    t = now.hour * 60 + now.minute
    if 240 <= t < 570:
        return "pre"
    elif 570 <= t < 960:
        return "regular"
    elif 960 <= t < 1200:
        return "post"
    return "closed"

def _get_name(symbol: str) -> str:
    try:
        info = yf.Ticker(symbol).info
        return info.get("longName") or info.get("shortName") or symbol
    except Exception:
        return symbol

def fetch_quotes(symbols: list) -> list:
    if not symbols:
        return []

    et = timezone(timedelta(hours=-4))
    today = datetime.now(et).date()

    try:
        raw = yf.download(
            symbols, period="2d", interval="1m",
            prepost=True, progress=False, auto_adjust=False,
            group_by="ticker",
        )
    except Exception as e:
        return [{"symbol": s, "name": s, "error": str(e)} for s in symbols]

    single = len(symbols) == 1

    def extract(sym: str) -> dict:
        try:
            if single:
                # Newer yfinance versions may use ticker as top-level key even for single symbols
                if isinstance(raw.columns, pd.MultiIndex):
                    close = raw[sym]["Close"] if sym in raw else None
                else:
                    close = raw["Close"] if "Close" in raw.columns else None
            else:
                close = raw[sym]["Close"] if sym in raw else None

            if close is None or close.dropna().empty:
                return {"symbol": sym, "name": sym, "error": "no data"}

            close = close.dropna()
            close_et = close.copy()
            close_et.index = close_et.index.tz_convert(et)

            t_min = close_et.index.hour * 60 + close_et.index.minute
            today_mask    = close_et.index.date == today
            prev_mask     = close_et.index.date < today
            # On weekends/holidays/after-midnight: no data for calendar today,
            # so fall back to the most recent trading day in the dataset
            if not today_mask.any():
                all_dates = sorted(set(close_et.index.date))
                if all_dates:
                    last_day   = all_dates[-1]
                    today_mask = close_et.index.date == last_day
                    prev_mask  = close_et.index.date < last_day
            pre_mask      = today_mask & (t_min < 570)
            post_mask     = today_mask & (t_min >= 960)
            regular_mask  = today_mask & ~pre_mask & ~post_mask
            # Use yesterday's last regular-hours candle as prev_close (official close)
            prev_reg_mask = prev_mask & (t_min >= 570) & (t_min < 960)

            def last(mask):
                s = close_et[mask]
                return float(s.iloc[-1]) if not s.empty else None

            prev_close    = last(prev_reg_mask) or last(prev_mask)
            pre_price     = last(pre_mask)
            post_price    = last(post_mask)
            regular_close = last(regular_mask)
            # Always use the most current available price
            price = post_price or regular_close or pre_price

            def chg(p, base):
                if p is None or not base:
                    return None, None
                c = p - base
                return round(c, 2), round(c / base * 100, 2)

            change, pct           = chg(price, prev_close)
            pre_change, pre_pct   = chg(pre_price, prev_close)
            # post_pct = AH change from today's regular close (shown in browser badge)
            post_change, post_pct = chg(post_price, regular_close or prev_close)

            # Detect if this market is actively trading right now.
            # We can't rely on US session masks (OMX trades in EU hours).
            # Instead: count candles in the last 20 minutes — active markets
            # produce ~1 candle/min, extended/pre-market is much sparser.
            is_live = False
            now_et = datetime.now(et)
            all_today_candles = close_et[today_mask]
            if not all_today_candles.empty:
                now_ts = now_et.timestamp()
                last_ts_unix = all_today_candles.index[-1].timestamp()
                last_candle_age_min = (now_ts - last_ts_unix) / 60
                # Density check: count candles in the 90-minute window ending at
                # the last available candle. Free data feeds delay European/Asian
                # markets by ~15 min so we can't use "now" as the window end.
                # Active markets produce ~1 candle/min; sparse pre/post ~0.1/min.
                cutoff_90 = last_ts_unix - 5400
                recent_90 = sum(1 for ts in all_today_candles.index
                                if ts.timestamp() >= cutoff_90)
                # ≥0.5 candles/min in that window AND last data < 90 min old
                is_live = (recent_90 / 90.0) >= 0.5 and last_candle_age_min < 90

            return {
                "symbol":      sym,
                "name":        sym,
                "price":       round(price, 2) if price is not None else None,
                "change":      change,
                "pct":         pct,
                "pre_price":   round(pre_price, 2) if pre_price is not None else None,
                "pre_change":  pre_change,
                "pre_pct":     pre_pct,
                "post_price":  round(post_price, 2) if post_price is not None else None,
                "post_change": post_change,
                "post_pct":    post_pct,
                "is_live":     is_live,
            }
        except Exception as e:
            return {"symbol": sym, "name": sym, "error": str(e)}

    results = [extract(s) for s in symbols]

    # Fetch display names in parallel without hitting rate limits
    missing_names = [r["symbol"] for r in results if "error" not in r]
    if missing_names:
        with ThreadPoolExecutor(max_workers=4) as pool:
            names = dict(zip(missing_names, pool.map(_get_name, missing_names)))
        for r in results:
            if "error" not in r:
                r["name"] = names.get(r["symbol"], r["symbol"])

    return results

_STATUS_LABELS = {
    "en": {
        "pre":    ("PRE ",    "#FFA500"),
        "post":   ("POST ",   "#58a6ff"),
        "closed": ("CLOSED ", "#6e7681"),
    },
    "sv": {
        "pre":    ("FH ",     "#FFA500"),
        "post":   ("EH ",     "#58a6ff"),
        "closed": ("STÄNGT ", "#6e7681"),
    },
}

def build_awtrix_payload(quotes: list, status: str, language: str = "en", scroll_speed: int = 40, lifetime: int = 180, ticker_names: dict = None) -> dict:
    ticker_names = ticker_names or {}
    valid = [q for q in quotes if "error" not in q and q.get("pct") is not None]
    if not valid:
        return None

    # Live markets (actively trading right now) scroll first
    valid.sort(key=lambda q: (0 if q.get("is_live") else 1))

    parts = []
    for q in valid:
        sym = q["symbol"]
        display = ticker_names.get(sym) or sym.replace("^", "")
        pct = q["pct"]  # always most-current price vs yesterday — same as browser
        if pct is None:
            continue
        sign = "+" if pct >= 0 else ""
        color = "#3fb950" if pct >= 0 else "#f85149"
        parts.append({"t": f"{display} {sign}{pct:.2f}%  ", "c": color})

    if not parts:
        return None

    lang_map = _STATUS_LABELS.get(language, _STATUS_LABELS["en"])
    # Skip the status label when any displayed ticker is actively trading —
    # the live tickers speak for themselves and "STÄNGT" would be misleading
    any_live = any(q.get("is_live") for q in valid)
    label = None if any_live else lang_map.get(status)

    text_payload = []
    LEAD = " " * 80
    if label:
        text_payload.append({"t": LEAD + label[0], "c": label[1]})
    text_payload.extend(parts)
    if not label and text_payload:
        text_payload[0] = {"t": LEAD + text_payload[0]["t"], "c": text_payload[0]["c"]}

    return {"text": text_payload, "scrollSpeed": scroll_speed, "lifetime": lifetime, "repeat": 1}

def push_to_awtrix(ip: str, payload: dict, name: str = "tickerboard") -> list:
    data = json.dumps(payload).encode()
    url = f"http://{ip}/api/custom?name={name}"
    try:
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return []
    except Exception as e:
        return [str(e)]

_last_awtrix_apps: set = {"tickerboard"}

def push_all_to_awtrix(ip: str, quotes: list, status: str, language: str,
                        display_mode: str, page_duration: int, scroll_speed: int = 40,
                        refresh_interval: int = 60, ticker_names: dict = None) -> list:
    global _last_awtrix_apps
    ticker_names = ticker_names or {}
    valid = [q for q in quotes if "error" not in q and q.get("pct") is not None]
    valid.sort(key=lambda q: (0 if q.get("is_live") else 1))
    # Show only live markets on the device when any are actively trading,
    # so e.g. only OMX30 appears during Swedish morning before US opens.
    live = [q for q in valid if q.get("is_live")]
    valid = live if live else valid
    errors = []
    new_apps: set = set()
    # Data expires after 3× the refresh interval so stale info clears
    # automatically if the server goes offline (e.g. computer shut down)
    lifetime = max(180, refresh_interval * 3)

    if display_mode == "paged":
        for q in valid:
            sym = q["symbol"]
            display = ticker_names.get(sym) or sym.replace("^", "")
            pct = q["pct"]
            sign = "+" if pct >= 0 else ""
            color = "#3fb950" if pct >= 0 else "#f85149"
            name = f"tickerboard_{sym.replace('^', '')}"
            new_apps.add(name)
            errors.extend(push_to_awtrix(ip, {
                "text": [
                    {"t": display + " ", "c": "#c9d1d9"},
                    {"t": f"{sign}{pct:.1f}%", "c": color},
                ],
                "noScroll": True,
                "center": True,
                "duration": page_duration,
                "lifetime": lifetime,
            }, name=name))
    else:
        payload = build_awtrix_payload(valid, status, language, scroll_speed, lifetime, ticker_names)
        if payload:
            errors.extend(push_to_awtrix(ip, payload))
            new_apps.add("tickerboard")

    # Expire any apps from the previous mode that are no longer in use
    for old in _last_awtrix_apps - new_apps:
        push_to_awtrix(ip, {"lifetime": 1}, name=old)
    _last_awtrix_apps = new_apps
    return errors

# ── API endpoints ──────────────────────────────────────────

@app.get("/api/tickers")
def get_tickers():
    return load_config()["tickers"]

@app.post("/api/tickers/{symbol}")
def add_ticker(symbol: str):
    config = load_config()
    symbol = symbol.upper()
    if symbol not in config["tickers"]:
        config["tickers"].append(symbol)
        save_config(config)
    return {"ok": True}

@app.delete("/api/tickers/{symbol}")
def remove_ticker(symbol: str):
    config = load_config()
    symbol = symbol.upper()
    config["tickers"] = [t for t in config["tickers"] if t != symbol]
    save_config(config)
    return {"ok": True}


@app.get("/api/default-indices")
def get_default_indices():
    config = load_config()
    existing = set(config["tickers"])
    return [
        {**idx, "added": idx["symbol"] in existing}
        for idx in DEFAULT_INDICES
    ]

@app.post("/api/restore-defaults")
async def restore_defaults(request: Request):
    try:
        body = await request.json()
        symbols = body.get("symbols")
    except Exception:
        symbols = None
    targets = [i["symbol"] for i in DEFAULT_INDICES if symbols is None or i["symbol"] in symbols]
    config = load_config()
    existing = set(config["tickers"])
    added = [t for t in targets if t not in existing]
    config["tickers"] = list(existing) + added
    save_config(config)
    return {"ok": True, "added": added}

@app.get("/api/ticker-names")
def get_ticker_names():
    return load_config().get("ticker_names", {})

@app.post("/api/ticker-names/{symbol}")
async def set_ticker_name(symbol: str, request: Request):
    body = await request.json()
    name = str(body.get("name", "")).strip()
    config = load_config()
    if "ticker_names" not in config:
        config["ticker_names"] = {}
    if name:
        config["ticker_names"][symbol] = name
    else:
        config["ticker_names"].pop(symbol, None)
    save_config(config)
    return {"ok": True}

@app.delete("/api/ticker-names/{symbol}")
def delete_ticker_name(symbol: str):
    config = load_config()
    if "ticker_names" in config:
        config["ticker_names"].pop(symbol, None)
        save_config(config)
    return {"ok": True}

@app.post("/api/brightness")
async def set_brightness(request: Request):
    body = await request.json()
    level = max(1, min(100, int(body.get("level", 50))))
    config = load_config()
    config["awtrix_brightness"] = level
    # Use IP from request body so it works even before settings are saved
    ip = body.get("ip", "").strip() or config.get("awtrix_ip", "").strip()
    if ip:
        config["awtrix_ip"] = ip
    save_config(config)
    if not ip:
        return {"ok": False, "error": "No AWTRIX IP configured"}
    bri = round(level * 255 / 100)
    data = json.dumps({"BRI": bri}).encode()
    try:
        req = urllib.request.Request(
            f"http://{ip}/api/settings", data=data, method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        return {"ok": True, "bri": bri, "ip": ip}
    except Exception as e:
        return {"ok": False, "error": str(e), "ip": ip}

@app.get("/api/ping-awtrix")
def ping_awtrix(ip: str = ""):
    config = load_config()
    ip = ip.strip() or config.get("awtrix_ip", "").strip()
    if not ip:
        return {"ok": False, "error": "No AWTRIX IP configured", "ip": ""}
    try:
        req = urllib.request.Request(f"http://{ip}/api/stats", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            stats = json.loads(resp.read().decode())
        return {"ok": True, "ip": ip, "bri": stats.get("bri"), "version": stats.get("version")}
    except Exception as e:
        return {"ok": False, "error": str(e), "ip": ip}

@app.get("/api/settings")
def get_settings():
    config = load_config()
    return {
        "awtrix_ip": config.get("awtrix_ip", ""),
        "awtrix_enabled": config.get("awtrix_enabled", False),
        "refresh_interval": config.get("refresh_interval", 60),
        "language": config.get("language", "en"),
        "display_mode": config.get("display_mode", "scroll"),
        "page_duration": config.get("page_duration", 5),
        "scroll_speed": config.get("scroll_speed", 40),
        "awtrix_brightness": config.get("awtrix_brightness", 50),
    }

@app.post("/api/settings")
async def save_settings(request: Request):
    global _push_timer
    body = await request.json()
    config = load_config()
    config["awtrix_ip"] = body.get("awtrix_ip", "").strip().rstrip("/")
    config["awtrix_enabled"] = bool(body.get("awtrix_enabled", False))
    config["refresh_interval"] = max(10, int(body.get("refresh_interval", 60)))
    config["language"] = body.get("language", "en") if body.get("language") in ("en", "sv") else "en"
    config["display_mode"] = body.get("display_mode", "scroll") if body.get("display_mode") in ("scroll", "paged") else "scroll"
    config["page_duration"] = max(2, min(30, int(body.get("page_duration", 5))))
    config["scroll_speed"] = max(10, min(100, int(body.get("scroll_speed", 40))))
    save_config(config)
    # Starta om bakgrundstimern direkt med nya inställningar
    if _push_timer:
        _push_timer.cancel()
    _schedule_push()
    return {"ok": True}

@app.get("/api/refresh")
def refresh(push: bool = False, ip: str = ""):
    """Läser från delad cache (max 20s gammal). Browser och enhet ser alltid samma data."""
    config = load_config()
    quotes, status = get_cached_quotes(max_age=20.0)

    push_result = None
    awtrix_ip = ip.strip() or config.get("awtrix_ip", "").strip()
    if push and awtrix_ip:
        errors = push_all_to_awtrix(
            awtrix_ip, quotes, status,
            config.get("language", "en"),
            config.get("display_mode", "scroll"),
            config.get("page_duration", 5),
            config.get("scroll_speed", 40),
            config.get("refresh_interval", 60),
            config.get("ticker_names", {}),
        )
        push_result = {"ok": not errors, "errors": errors}

    return {
        "quotes": quotes,
        "market_status": status,
        "effective_status": status,
        "push": push_result,
    }

app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
