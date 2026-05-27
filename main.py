import sys
import os
import threading
import webbrowser
import time

import uvicorn
from PIL import Image, ImageDraw
import pystray

PORT = 8000

def _make_icon():
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=10, fill='#1a1f2e')
    # Mini stock-chart bars
    bars = [
        (8,  42, 18, 54, '#f85149'),
        (22, 28, 32, 54, '#3fb950'),
        (36, 36, 46, 54, '#3fb950'),
        (50, 18, 60, 54, '#58a6ff'),
    ]
    for x0, y0, x1, y1, c in bars:
        d.rectangle([x0, y0, x1, y1], fill=c)
    return img

def _open_browser(icon=None, item=None):
    webbrowser.open(f'http://localhost:{PORT}')

def _cleanup_awtrix():
    try:
        import app as tickerapp
        config = tickerapp.load_config()
        ip = config.get("awtrix_ip", "").strip()
        if ip:
            for name in list(tickerapp._last_awtrix_apps):
                tickerapp.push_to_awtrix(ip, {"lifetime": 1}, name=name)
    except Exception:
        pass

def _quit(icon, item):
    _cleanup_awtrix()
    icon.stop()
    os._exit(0)

def _run_server():
    import app as tickerapp
    uvicorn.run(tickerapp.app, host='127.0.0.1', port=PORT, log_level='error')

if __name__ == '__main__':
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    # Give the server a moment to start, then open the browser
    threading.Timer(1.5, _open_browser).start()

    menu = pystray.Menu(
        pystray.MenuItem('Öppna Tickerboard', _open_browser, default=True),
        pystray.MenuItem('Avsluta', _quit),
    )
    icon = pystray.Icon('Tickerboard', _make_icon(), 'Tickerboard', menu)
    icon.run()
