#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN=${PYTHON_BIN:-python3}
PATCHRAIL_HOME=${PATCHRAIL_HOME:-"$ROOT_DIR/.patchrail"}

export PATCHRAIL_HOME

json_query() {
  "$PYTHON_BIN" -c '
import json
import sys

data = json.load(sys.stdin)
for key in sys.argv[1:]:
    data = data[key]
print(data)
' "$@"
}

"$PYTHON_BIN" -m patchrail.cli config init >/dev/null
"$PYTHON_BIN" -m patchrail.cli preflight --role planner >/dev/null
"$PYTHON_BIN" -m patchrail.cli preflight --role reviewer >/dev/null
"$PYTHON_BIN" -m patchrail.cli preflight --role executor --runner auto >/dev/null

create_output=$("$PYTHON_BIN" -m patchrail.cli task create \
  --title "Local Smoke Test" \
  --description "Exercise the local Patchrail flow")
task_id=$(printf '%s' "$create_output" | json_query task id)

"$PYTHON_BIN" -m patchrail.cli plan \
  --task-id "$task_id" \
  --summary "Run the local smoke harness" \
  --step "Resolve planner candidate" \
  --step "Execute local runner" >/dev/null

run_output=$("$PYTHON_BIN" -m patchrail.cli run --task-id "$task_id" --runner auto)
run_id=$(printf '%s' "$run_output" | json_query run id)

"$PYTHON_BIN" -m patchrail.cli review \
  --run-id "$run_id" \
  --verdict pass \
  --summary "Local smoke run reviewed" >/dev/null

"$PYTHON_BIN" -m patchrail.cli approve \
  --task-id "$task_id" \
  --rationale "Local smoke flow passed" >/dev/null

status_output=$("$PYTHON_BIN" -m patchrail.cli status --task-id "$task_id")
final_state=$(printf '%s' "$status_output" | json_query task state)

printf 'Local smoke flow completed: task=%s run=%s state=%s\n' "$task_id" "$run_id" "$final_state"
printf 'PATCHRAIL_HOME=%s\n' "$PATCHRAIL_HOME"
