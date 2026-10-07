#!/usr/bin/env bash
# Install the Dynawo release the tutorial is tested with and declare it to PowSyBl.
# DYNAWO_HOME overrides the install folder, DYNAWO_VERSION the release.
set -euo pipefail

version="${DYNAWO_VERSION:-1.7.0}"
home="${DYNAWO_HOME:-$HOME/dynawo}"
config_dir="${POWSYBL_CONFIG_DIR:-$HOME/.itools}"
config="$config_dir/config.yml"

if [ -x "$home/dynawo.sh" ]; then
  echo "Dynawo already installed in $home"
else
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  url="https://github.com/dynawo/dynawo/releases/download/v$version/Dynawo_Linux_v$version.zip"
  echo "Downloading $url"
  curl -fL --progress-bar -o "$tmp/dynawo.zip" "$url"
  unzip -q "$tmp/dynawo.zip" -d "$tmp"
  mkdir -p "$(dirname "$home")"
  mv "$tmp/dynawo" "$home"
fi

mkdir -p "$config_dir"
if [ -f "$config" ] && grep -q "^dynawo:" "$config"; then
  echo "$config already declares Dynawo, left unchanged"
else
  printf 'dynawo:\n  homeDir: %s\n  debug: false\n' "$home" >> "$config"
  echo "Declared Dynawo in $config"
fi

"$home/dynawo.sh" version
