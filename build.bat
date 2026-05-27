@echo off
echo Installerar beroenden...
pip install pyinstaller pystray pillow

echo.
echo Bygger Tickerboard.exe...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name Tickerboard ^
  --add-data "static;static" ^
  main.py

echo.
if exist dist\Tickerboard.exe (
    echo Klar! Tickerboard.exe finns i mappen dist\
) else (
    echo Nagot gick fel, se felmeddelanden ovan.
)
pause
