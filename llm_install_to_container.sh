#!/bin/bash

set -euo pipefail

MODEL="${1:-}"

if [ -z "$MODEL" ]; then
    read -rp "インストールするモデルを入力。gpt-oss:20bなど：" MODEL                            
fi

if [ -z "$MODEL" ]; then
    echo "モデル名が指定されていません。スクリプトを終了します。"
    exit 1
fi

docker exec -it ollama-gpt-oss ollama run "$MODEL"