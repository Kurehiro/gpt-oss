#!/bin/bash
CONTAINER_NAME="ollama-gpt-oss"
# コンテナが起動していない場合は起動
if ! docker ps | grep -q CON; then
    echo "コンテナが起動していません。コンテナを起動します..."
    docker start ollama-gpt-oss
fi

set -euo pipefail

MODEL="${1:-}"

if [ -z "$MODEL" ]; then
    read -rp "インストールするモデルを入力。gpt-oss:20bなど：" MODEL                            
fi

if [ -z "$MODEL" ]; then
    echo "モデル名が指定されていません。スクリプトを終了します。"
    exit 1
fi
echo "モデル '$MODEL' をコンテナ内にインストールします..."

docker exec -it ollama-gpt-oss ollama run "$MODEL"