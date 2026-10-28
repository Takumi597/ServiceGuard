@echo off
setlocal
cd /d %~dp0

set PYTHONHASHSEED=0
set PYTHONDONTWRITEBYTECODE=1
set SOURCE_DATE_EPOCH=1700000000

python -m pip install -r requirements.txt
if errorlevel 1 goto blad

pyinstaller --clean --noconfirm ServiceGuard.spec
if errorlevel 1 goto blad

if not exist dist\deploy mkdir dist\deploy
copy /y dist\ServiceGuard.exe dist\deploy\ >nul
copy /y config.json dist\deploy\ >nul
copy /y whitelist.json dist\deploy\ >nul
copy /y sysmon-config.xml dist\deploy\ >nul
copy /y README.txt dist\deploy\ >nul

pyinstaller --clean --noconfirm --onefile --name testService --hidden-import win32timezone --hidden-import servicemanager tests\testService.py

echo.
echo Budowanie zakonczone. Folder gotowy do wdrozenia: dist\deploy
echo Usluga testowa: dist\testService.exe
goto koniec

:blad
echo.
echo Budowanie nie powiodlo sie. Sprawdz komunikaty powyzej.

:koniec
endlocal
