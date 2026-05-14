#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This build script must be run on macOS."
  exit 1
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "[1/4] Updating pip..."
python -m pip install --upgrade pip

echo "[2/4] Installing dependencies..."
pip install --prefer-binary -r requirements.txt

echo "[3/4] Cleaning old build output..."
rm -rf build dist

echo "[4/4] Building macOS app..."
pyinstaller --noconfirm --clean packaging/macos/WhatsMealMac.spec

if [[ -f .env ]]; then
  cp .env dist/WhatsMeal.app/Contents/MacOS/.env
elif [[ -f .env.example ]]; then
  cp .env.example dist/WhatsMeal.app/Contents/MacOS/.env
fi

(
  cd dist
  rm -f WhatsMeal-macOS.zip
  ditto -c -k --sequesterRsrc --keepParent WhatsMeal.app WhatsMeal-macOS.zip
)

echo
echo "Build complete:"
echo "  dist/WhatsMeal.app"
echo "  dist/WhatsMeal-macOS.zip"
