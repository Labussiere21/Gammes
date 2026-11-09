@echo off
REM ============================================================
REM  GrilleMaker - build Windows (.exe + installateur)
REM  Prerequis : Python 3.10+ (coche "Add to PATH")
REM              Inno Setup 6 (https://jrsoftware.org/isdl.php)
REM ============================================================
cd /d "%~dp0"
echo [1/3] Installation des dependances...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller || goto :err

echo [2/3] Compilation de l'application...
python -m PyInstaller --noconfirm --clean --windowed --name GrilleMaker ^
  --icon icon.ico --add-data "exemples;exemples" --add-data "icon.png;." app.py || goto :err

echo [3/3] Creation de l'installateur...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo Inno Setup introuvable. L'app est dispo dans dist\GrilleMaker\GrilleMaker.exe
  pause & exit /b 0
)
%ISCC% installer.iss || goto :err
echo.
echo OK : installateur cree dans Output\GrilleMaker-Setup.exe
pause
exit /b 0
:err
echo ERREUR pendant le build.
pause
exit /b 1
