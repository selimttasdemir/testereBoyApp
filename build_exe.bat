@echo off
REM Build script for Windows to create distributable .exe

set APP_NAME=TestereBoyAppCAGCELIK

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

echo Running PyInstaller...
if exist logo.png (
    pyinstaller --noconsole --onedir --name %APP_NAME% --add-data "logo.png;." --hidden-import PIL --hidden-import PIL._tkinter_finder app.py
) else (
    echo Warning: logo.png not found, building without it.
    pyinstaller --noconsole --onedir --name %APP_NAME% --hidden-import PIL --hidden-import PIL._tkinter_finder app.py
)

set BUILD_DIR=dist\%APP_NAME%
if exist data.db (
    echo Copying existing data.db into %BUILD_DIR%\
    copy data.db "%BUILD_DIR%\"
) else (
    echo No data.db found in project root. The app will create a new DB on first run.
)

if exist logo.png (
    echo Copying logo.png into %BUILD_DIR%\
    copy logo.png "%BUILD_DIR%\"
) else (
    echo No logo.png found in project root.
)

echo.
echo Build complete! The distributable folder is: %BUILD_DIR%
echo To run the app, go to that folder and double-click %APP_NAME%.exe
pause
