#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$repo_root"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This build script must be run on Linux."
  exit 1
fi

distro_id="unknown"
if [[ -f /etc/os-release ]]; then
  # shellcheck source=/dev/null
  source /etc/os-release
  distro_id="${ID:-unknown}"
fi

if [[ ! -f school-meal-tray/meal_tray.py ]]; then
  echo "school-meal-tray/meal_tray.py was not found."
  exit 1
fi

if [[ ! -d school-meal-tray/.venv ]]; then
  python3 -m venv --system-site-packages school-meal-tray/.venv
fi

source school-meal-tray/.venv/bin/activate

echo "[1/5] Updating pip..."
python -m pip install --upgrade pip

echo "[2/5] Installing Python build dependencies..."
pip install --prefer-binary requests python-dotenv pyinstaller

echo "[3/5] Checking Linux tray dependencies..."
if ! python - <<'PY'
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
except ValueError:
    gi.require_version("AppIndicator3", "0.1")

from gi.repository import Gdk, GLib, Gtk  # noqa: F401
PY
then
  cat <<'MSG'

Missing GTK/AppIndicator runtime packages.

Ubuntu/Debian:
  sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1

Arch Linux:
  sudo pacman -S python-gobject gtk3 libayatana-appindicator

After installing them, run this script again.
MSG
  echo
  echo "Detected distro: $distro_id"
  exit 1
fi

echo "[4/5] Cleaning old build output..."
rm -rf school-meal-tray/build school-meal-tray/dist

echo "[5/5] Building Linux tray binary..."
pyinstaller \
  --noconfirm \
  --clean \
  --distpath school-meal-tray/dist \
  --workpath school-meal-tray/build \
  client/packaging/linux/SchoolMealTray.spec

if [[ -f school-meal-tray/.env ]]; then
  cp school-meal-tray/.env school-meal-tray/dist/.env
fi

echo
echo "Build complete: school-meal-tray/dist/SchoolMealTray"
if [[ -f school-meal-tray/dist/.env ]]; then
  echo "Copied runtime env: school-meal-tray/dist/.env"
else
  echo "Add NEIS_API_KEY to school-meal-tray/dist/.env before running."
fi
