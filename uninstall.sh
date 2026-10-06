#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${PDFTHUMB_BIN_DIR:-$HOME/.local/bin}"
LINK="$BIN_DIR/pdfthumb"
if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$PROJECT_DIR/.venv/bin/pdfthumb" ]; then
  rm "$LINK" && echo "Removed $LINK"
fi
rm -rf "$PROJECT_DIR/.venv" && echo "Removed $PROJECT_DIR/.venv"
