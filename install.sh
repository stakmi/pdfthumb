#!/usr/bin/env bash
# Install pdfthumb into a local virtualenv and link the CLI into ~/.local/bin.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
BIN_DIR="${PDFTHUMB_BIN_DIR:-$HOME/.local/bin}"
PYTHON="${PYTHON:-python3}"

command -v "$PYTHON" >/dev/null 2>&1 || { echo "error: $PYTHON not found. Install Python >= 3.9." >&2; exit 1; }
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || { echo "error: Python >= 3.9 required (found $("$PYTHON" -V 2>&1))." >&2; exit 1; }

echo "==> Creating virtualenv at $VENV_DIR"
[ -x "$VENV_DIR/bin/python" ] || "$PYTHON" -m venv "$VENV_DIR"

echo "==> Installing dependencies"
"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
if [ "${1:-}" = "--dev" ]; then
  "$VENV_DIR/bin/python" -m pip install --quiet -e "$PROJECT_DIR[dev]"
else
  "$VENV_DIR/bin/python" -m pip install --quiet -e "$PROJECT_DIR"
fi

echo "==> Linking pdfthumb into $BIN_DIR"
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/pdfthumb" "$BIN_DIR/pdfthumb"

"$BIN_DIR/pdfthumb" --version

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "warning: $BIN_DIR is not on your PATH. Add this to your shell profile:"
     echo "  export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac
echo "Done. Try: pdfthumb --help"
