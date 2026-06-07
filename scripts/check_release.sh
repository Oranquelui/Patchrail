#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Build and verify the Patchrail release package.

Usage:
  sh scripts/check_release.sh [--python /path/to/python3.13] [--dry-run]

Options:
  --python PATH       Python 3.12+ interpreter to use for build and install checks.
  --dry-run           Print the commands without executing them.
  -h, --help          Show this help text.
EOF
}

python_bin="${PATCHRAIL_PYTHON:-python3}"
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
tmp_dir="${PATCHRAIL_RELEASE_TMP:-}"

build_cmd="$python_bin -m build"
venv_cmd="$python_bin -m venv .patchrail-release-venv"
install_cmd=".patchrail-release-venv/bin/python -m pip install dist/patchrail-*.whl"
help_cmd=".patchrail-release-venv/bin/patchrail --help"
smoke_cmd="PATH=.patchrail-release-venv/bin:\$PATH PYTHON_BIN=.patchrail-release-venv/bin/python PATCHRAIL_HOME=.patchrail-release-home sh scripts/local_smoke_test.sh"

if [ "$dry_run" -eq 1 ]; then
  printf '%s\n' "cd $repo_root"
  printf '%s\n' "$build_cmd"
  printf '%s\n' "$venv_cmd"
  printf '%s\n' "$install_cmd"
  printf '%s\n' "$help_cmd"
  printf '%s\n' "$smoke_cmd"
  exit 0
fi

if [ ! -x "$python_bin" ] && ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "Python interpreter not found: $python_bin" >&2
  exit 1
fi

if ! "$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Patchrail release checks require Python 3.12+." >&2
  exit 1
fi

if [ -z "$tmp_dir" ]; then
  tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/patchrail-release.XXXXXX")
  trap 'rm -rf "$tmp_dir"' EXIT INT TERM
fi

cd "$repo_root"
rm -rf dist
"$python_bin" -m build

release_venv="$tmp_dir/venv"
release_home="$tmp_dir/patchrail-home"
"$python_bin" -m venv "$release_venv"

wheel_path=$(find dist -name 'patchrail-*.whl' -type f | sort | tail -n 1)
if [ -z "$wheel_path" ]; then
  echo "No Patchrail wheel found under dist/." >&2
  exit 1
fi

"$release_venv/bin/python" -m pip install "$wheel_path"
PATCHRAIL_HOME="$release_home" "$release_venv/bin/patchrail" --help >/dev/null
PATH="$release_venv/bin:$PATH" PYTHON_BIN="$release_venv/bin/python" PATCHRAIL_HOME="$release_home" sh scripts/local_smoke_test.sh
