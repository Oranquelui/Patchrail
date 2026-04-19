#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN=${PYTHON_BIN:-python3}
PATCHRAIL_HOME=${PATCHRAIL_HOME:-"$ROOT_DIR/.patchrail"}
PATCHRAIL_CONFIG_PRESET=${PATCHRAIL_CONFIG_PRESET:-local}
PATCHRAIL_WORKFLOW_BACKEND=${PATCHRAIL_WORKFLOW_BACKEND:-local}
PATCHRAIL_RUNNER=${PATCHRAIL_RUNNER:-auto}
PATCHRAIL_AUTO_APPROVE_FALLBACK=${PATCHRAIL_AUTO_APPROVE_FALLBACK:-}
PATCHRAIL_AUTO_PLAN=${PATCHRAIL_AUTO_PLAN:-0}
PATCHRAIL_PLAN_ACCESS_MODE=${PATCHRAIL_PLAN_ACCESS_MODE:-auto}
PATCHRAIL_AUTO_REVIEW=${PATCHRAIL_AUTO_REVIEW:-0}
PATCHRAIL_REVIEW_ACCESS_MODE=${PATCHRAIL_REVIEW_ACCESS_MODE:-auto}

if [ -z "$PATCHRAIL_AUTO_APPROVE_FALLBACK" ]; then
  if [ "$PATCHRAIL_CONFIG_PRESET" = "real" ]; then
    PATCHRAIL_AUTO_APPROVE_FALLBACK=1
  else
    PATCHRAIL_AUTO_APPROVE_FALLBACK=0
  fi
fi

export PATCHRAIL_HOME

run_patchrail() {
  "$PYTHON_BIN" -m patchrail.cli --json "$@"
}

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

json_query_optional() {
  "$PYTHON_BIN" -c '
import json
import sys

data = json.load(sys.stdin)
try:
    for key in sys.argv[1:]:
        data = data[key]
except Exception:
    sys.exit(1)
if data is None:
    sys.exit(1)
print(data)
' "$@"
}

run_patchrail config init --preset "$PATCHRAIL_CONFIG_PRESET" --workflow-backend "$PATCHRAIL_WORKFLOW_BACKEND" >/dev/null
run_patchrail preflight --role planner >/dev/null
run_patchrail preflight --role reviewer >/dev/null
run_patchrail preflight --role executor --runner "$PATCHRAIL_RUNNER" >/dev/null

create_output=$(run_patchrail task create \
  --title "Local Smoke Test" \
  --description "Exercise the local Patchrail flow")
task_id=$(printf '%s' "$create_output" | json_query task id)

if [ "$PATCHRAIL_AUTO_PLAN" = "1" ]; then
  run_patchrail plan \
    --task-id "$task_id" \
    --auto \
    --access-mode "$PATCHRAIL_PLAN_ACCESS_MODE" >/dev/null
else
  run_patchrail plan \
    --task-id "$task_id" \
    --summary "Run the local smoke harness" \
    --step "Resolve planner candidate" \
    --step "Execute local runner" >/dev/null
fi

set +e
run_output=$(run_patchrail run --task-id "$task_id" --runner "$PATCHRAIL_RUNNER" 2>&1)
run_status=$?
set -e

fallback_approved=0
if [ "$run_status" -ne 0 ]; then
  if [ "$PATCHRAIL_AUTO_APPROVE_FALLBACK" = "1" ]; then
    status_output=$(run_patchrail status --task-id "$task_id")
    if request_status=$(printf '%s' "$status_output" | json_query_optional latest_fallback_request status); then
      if [ "$request_status" = "pending" ]; then
        run_patchrail approve-fallback \
          --task-id "$task_id" \
          --rationale "Auto-approve smoke fallback for preset $PATCHRAIL_CONFIG_PRESET" >/dev/null
        fallback_approved=1
        run_output=$(run_patchrail run --task-id "$task_id" --runner "$PATCHRAIL_RUNNER")
      else
        printf '%s\n' "$run_output" >&2
        exit "$run_status"
      fi
    else
      printf '%s\n' "$run_output" >&2
      exit "$run_status"
    fi
  else
    printf '%s\n' "$run_output" >&2
    exit "$run_status"
  fi
fi

run_id=$(printf '%s' "$run_output" | json_query run id)

if [ "$PATCHRAIL_AUTO_REVIEW" = "1" ]; then
  run_patchrail review \
    --run-id "$run_id" \
    --auto \
    --access-mode "$PATCHRAIL_REVIEW_ACCESS_MODE" >/dev/null
else
  run_patchrail review \
    --run-id "$run_id" \
    --verdict pass \
    --summary "Local smoke run reviewed" >/dev/null
fi

run_patchrail approve \
  --task-id "$task_id" \
  --rationale "Local smoke flow passed" >/dev/null

status_output=$(run_patchrail status --task-id "$task_id")
final_state=$(printf '%s' "$status_output" | json_query task state)

printf 'Local smoke flow completed: preset=%s workflow_backend=%s task=%s run=%s state=%s fallback_approved=%s auto_plan=%s auto_review=%s\n' \
  "$PATCHRAIL_CONFIG_PRESET" "$PATCHRAIL_WORKFLOW_BACKEND" "$task_id" "$run_id" "$final_state" "$fallback_approved" "$PATCHRAIL_AUTO_PLAN" "$PATCHRAIL_AUTO_REVIEW"
printf 'PATCHRAIL_HOME=%s\n' "$PATCHRAIL_HOME"
