#!/usr/bin/env bash
# Deploy this module to the foundrySB smoke server (CT 211) and restart Foundry.
# Usage: tools/deploy_smoke.sh [--no-restart] [--dry-run]
# Modelled on ~/wfvtt/tools/deploy_smoke.sh. One rsync per source dir, each into its own dest
# (two source dirs into one dest collide). Data/modules is root-owned, hence sudo rsync.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${SF2E_SMOKE_HOST:-192.168.11.36}"
USER="${SF2E_SMOKE_USER:-project}"
KEY="${SF2E_SMOKE_KEY:-$HOME/.ssh/foundry_test}"
MODULE_ID="$(python3 -c 'import json; print(json.load(open("module.json"))["id"])')"
DEST="/var/lib/foundrydata/Data/modules/${MODULE_ID}"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 -i "$KEY" "${USER}@${HOST}")
RESTART=1; DRY=()
for a in "$@"; do
  case "$a" in
    --no-restart) RESTART=0 ;;
    --dry-run)    DRY=(--dry-run) ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

echo "== syntax check"
for f in scripts/*.js scripts/*/*.js; do node --check "$f"; done
for f in module.json lang/*.json; do python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$f"; done

echo "== deploying ${MODULE_ID} -> ${USER}@${HOST}:${DEST}"
"${SSH[@]}" "sudo mkdir -p '${DEST}'"
for f in module.json README.md LICENSE CHANGELOG.md; do
  [ -f "$f" ] || continue
  rsync "${DRY[@]}" -a --rsync-path="sudo rsync" -e "ssh -o BatchMode=yes -i $KEY" "$f" "${USER}@${HOST}:${DEST}/"
done
for d in scripts templates lang icons; do
  [ -d "$d" ] || continue
  rsync "${DRY[@]}" -a --delete --rsync-path="sudo rsync" -e "ssh -o BatchMode=yes -i $KEY" "$d/" "${USER}@${HOST}:${DEST}/${d}/"
done
if [ ${#DRY[@]} -gt 0 ]; then echo "== dry run complete"; exit 0; fi

if [ "$RESTART" = 1 ]; then
  echo "== restarting foundry"
  "${SSH[@]}" "sudo systemctl restart foundry.service"
  echo -n "== waiting for foundry: "
  for _ in $(seq 1 30); do
    s=$(curl -s --max-time 3 "http://${HOST}:30000/api/status" || true)
    if [ -n "$s" ]; then echo; echo "$s"; break; fi
    echo -n "."; sleep 2
  done
fi
