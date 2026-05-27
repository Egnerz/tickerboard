import sys
import os
import threading
import webbrowser
import signal
import uvicorn

PORT = 8000

def _run_server():
    import app as tickerapp
    uvicorn.run(tickerapp.app, host='0.0.0.0', port=PORT, log_level='error')

def _open_browser():
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    browser_thread = threading.Thread(target=_open_browser, daemon=True)
    browser_thread.start()

    print(f'Tickerboard körs på http://localhost:{PORT}')
    print('Tryck Ctrl+C för att avsluta.')

    def _shutdown(sig, frame):
        print('\nAvslutar...')
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    server_thread.join()
