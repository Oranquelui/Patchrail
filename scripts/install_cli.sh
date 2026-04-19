#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Install Patchrail as the `patchrail` command via pipx.

Usage:
  sh scripts/install_cli.sh [--python /path/to/python3.13] [--with-langgraph] [--dry-run]

Options:
  --python PATH       Python 3.12+ interpreter to use for installation.
  --with-langgraph    Inject optional `langgraph` runtime into the Patchrail pipx environment.
  --dry-run           Print the commands without executing them.
  -h, --help          Show this help text.
EOF
}

python_bin="${PATCHRAIL_PYTHON:-python3}"
with_langgraph=0
dry_run=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --python)
      shift
      if [ "$#" -eq 0 ]; then
        echo "Missing value for --python" >&2
        exit 1
      fi
      python_bin="$1"
      ;;
    --with-langgraph)
      with_langgraph=1
      ;;
    --dry-run)
      dry_run=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
install_cmd="pipx install --force --python $python_bin --editable $repo_root"
inject_cmd="pipx inject patchrail langgraph"
verify_cmd="patchrail --help"

if [ "$dry_run" -eq 1 ]; then
  printf '%s\n' "$install_cmd"
  if [ "$with_langgraph" -eq 1 ]; then
    printf '%s\n' "$inject_cmd"
  fi
  printf '%s\n' "$verify_cmd"
  exit 0
fi

if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx is required. Install it with 'brew install pipx' and then run 'pipx ensurepath'." >&2
  exit 1
fi

if [ ! -x "$python_bin" ] && ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Python interpreter not found: $python_bin" >&2
  exit 1
fi

if ! "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Patchrail requires Python 3.12+ for installation." >&2
  exit 1
fi

echo "Installing Patchrail into pipx using $python_bin"
pipx install --force --python "$python_bin" --editable "$repo_root"

if [ "$with_langgraph" -eq 1 ]; then
  echo "Injecting optional langgraph runtime into the Patchrail pipx environment"
  pipx inject patchrail langgraph
fi

echo "Patchrail is installed. Run:"
echo "  patchrail --help"
