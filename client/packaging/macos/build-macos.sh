#!/usr/bin/env bash
set -euo pipefail

client_root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$client_root"

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

if [[ ! -d dist/WhatsMeal.app ]]; then
  echo "Build finished but dist/WhatsMeal.app was not created."
  echo "Expected output directory: $client_root/dist"
  exit 1
fi

(
  cd dist
  rm -f WhatsMeal-macOS.zip
  ditto -c -k --sequesterRsrc --keepParent WhatsMeal.app WhatsMeal-macOS.zip
)

if [[ ! -f dist/WhatsMeal-macOS.zip ]]; then
  echo "Zip creation failed: dist/WhatsMeal-macOS.zip was not created."
  exit 1
fi

echo
echo "Build complete:"
echo "  $client_root/dist/WhatsMeal.app"
echo "  $client_root/dist/WhatsMeal-macOS.zip"
echo "Uses the bundled API base by default."
echo "Optional override: add .env to WhatsMeal.app/Contents/MacOS with API_BASE_URL=..."
