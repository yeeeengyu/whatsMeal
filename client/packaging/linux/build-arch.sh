#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$repo_root"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This build script must be run on Linux."
  exit 1
fi

if ! command -v pacman >/dev/null 2>&1; then
  echo "pacman was not found. Use build-linux.sh for non-Arch distributions."
  exit 1
fi

missing_packages=()
for package in python python-gobject gtk3 libayatana-appindicator; do
  if ! pacman -Q "$package" >/dev/null 2>&1; then
    missing_packages+=("$package")
  fi
done

if (( ${#missing_packages[@]} > 0 )); then
  echo "Missing Arch runtime packages:"
  printf '  %s\n' "${missing_packages[@]}"
  echo
  echo "Install them with:"
  echo "  sudo pacman -S ${missing_packages[*]}"
  exit 1
fi

exec client/packaging/linux/build-linux.sh
