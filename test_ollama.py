# ~/ssd_yamaguchi/project_Laplace/gpt-oss-standalone/test_ollama.py
import requests
import json

url = "http://localhost:11434/api/generate"

data = {
    "model": "gemma:2b",
    "prompt": "あなたは何のモデル？何ができる？anser in Japanese.",
    "stream": False
}

try:
    response = requests.post(url, json=data)
    response.raise_for_status()

    response_data = response.json()

    print("コンテナ内のLLMからの応答:")
    print(response_data['response'])

except requests.exceptions.RequestException as e:
    print(f"エラーが発生しました: {e}")