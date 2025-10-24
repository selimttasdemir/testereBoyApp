#!/usr/bin/env bash
set -euo pipefail

# Build script to create a distributable folder using PyInstaller.
# This script builds a one-folder (--onedir) distribution so the SQLite
# database file can live alongside the exe and remain writable/persistent.

APP_NAME="TestereBoyAppCAGCELIK"

echo "Cleaning previous builds..."
rm -rf build dist "${APP_NAME}.spec"

echo "Running PyInstaller..."
# Include logo.png if present next to the exe. Do NOT embed data.db into the exe;
# instead we'll copy any existing data.db into the dist folder after build so it stays writable.
if [ -f logo.png ]; then
  pyinstaller --noconsole --onedir --name "${APP_NAME}" --add-data "logo.png:." app.py
else
  echo "Warning: logo.png not found, building without it."
  pyinstaller --noconsole --onedir --name "${APP_NAME}" app.py
fi

BUILD_DIR="dist/${APP_NAME}"
if [ -f data.db ]; then
  echo "Copying existing data.db into ${BUILD_DIR}/"
  cp data.db "${BUILD_DIR}/"
else
  echo "No data.db found in project root. The app will create a new DB on first run."
fi

echo "Build complete. The distributable folder is: ${BUILD_DIR}"
echo "To run the app on the target machine, copy the entire folder to that machine and run the ${APP_NAME} executable inside it."
