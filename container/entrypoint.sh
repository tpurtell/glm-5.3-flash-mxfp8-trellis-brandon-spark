#!/usr/bin/env bash
set -euo pipefail
exec vllm serve "$@" --chat-template /opt/trellismx/data/serving_chat_template.jinja
