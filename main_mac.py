import sys
import os
import threading
import webbrowser
import signal
import subprocess
import uvicorn

PORT = 8000

def _run_server():
    import app as tickerapp
    uvicorn.run(tickerapp.app, host='127.0.0.1', port=PORT, log_level='error')

def _open_browser():
    import time
    time.sleep(1.5)
    try:
        subprocess.run(['open', f'http://localhost:{PORT}'], check=False)
    except Exception:
        webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    browser_thread = threading.Thread(target=_open_browser, daemon=True)
    browser_thread.start()

    print(f'Tickerboard running at http://localhost:{PORT}')
    print('Press Ctrl+C to quit.')

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

    def _shutdown(sig, frame):
        _cleanup_awtrix()
        print('\nQuitting...')
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    server_thread.join()
