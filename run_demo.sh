#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m patchgap.agent_cli demo_repo --replay --issue "Users occasionally receive duplicate entitlement after payment."
