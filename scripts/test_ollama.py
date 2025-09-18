# ~/ssd_yamaguchi/project_Laplace/gpt-oss-standalone/test_ollama.py
import requests
import json

url = "http://localhost:11434/api/generate"

data = {
    "model": "gpt-oss:20b",
    "prompt": "あなたは何のモデル？何ができる？answer in Japanese.",
    "stream": True
}

"""
model: 使用するLLMモデルの名前
prompt: プロンプト
stream: ストリーミング応答を使用するかどうか
    ストリーミング応答？
    - True: 応答が部分的に生成されるたびにデータを受け取る。普段使ってるのと同じ感じになる。
    - False: 応答が完全に生成されるまで待つ
    利点
    ・応答の一部をすぐに受け取れるため、ユーザー体験が向上する
    ・長い応答を待つ必要がない
    ・逐次処理でメモリ使用量を削減できる、らしい
    欠点
    ・実装が比較的複雑になる、
    というのは途中でエラーが起こったときの処理や停止トークン処理が必要、らしい
"""
# dataディクショナリの'stream'の値を見て、処理を分岐させる
if data["stream"]:
    # streamがTrueの場合の処理（ストリーミング）
    print("--- ストリーミング応答 (stream: True) ---")
    try:
        # requestsライブラリ自体のstream=Trueも必要
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()

        print("コンテナ内LLMからの応答:")
        
        # iter_lines()で一行ずつ（＝一つのJSONずつ）処理するループ
        for line in response.iter_lines():
            if line:
                #バイト列なのでutf-8にデコード
                decoded_line = line.decode('utf-8')
                # JSONをパースして辞書に変換
                response_data = json.loads(decoded_line)
                # 'response'キーの内容を表示、改行なし、バッファを即座にフラッシュ
                print(response_data['response'], end='', flush=True)

        print() # 最後に改行

    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")

else:
    # streamがFalseの場合の処理（一括受信）
    print("--- 一括応答 (stream: False) ---")
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        response_data = response.json()

        print("コンテナ内LLMからの応答:")
        print(response_data['response'])

    except requests.exceptions.RequestException as e:
        print(f"エラーが発生しました: {e}")
