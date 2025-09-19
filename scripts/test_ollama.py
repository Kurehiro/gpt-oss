# ~/ssd_yamaguchi/project_Laplace/gpt-oss-standalone/test_ollama.py
import requests
import json

url = "http://localhost:11434/api/generate"

data = {
    "model": "gpt-oss:20b",
    "prompt": "以下の情報から会話文を作成してください。会話はこちらから”会話生成”と入力されてから作成してください\n内容:日常的な会話の中で人物の誰かが用事やふとした出来事でその場から離れる\n人物:{太郎,花子,二郎,たま子}\n場所:{キッチン,リビング,風呂場,トイレ,ベランダ,庭,玄関,寝室,物置,太郎の部屋,花子の部屋,二郎の部屋,たま子の部屋}\n補足1:会話が行われている場所は一般的な家庭環境とする\n補足2:会話をしている人数は2人以上4人以下とする\n候補3:人物が向かうとする行き先は”場所”から生成してください\n補足4:「お腹がすいた＝キッチン」などの場所と目的が繋がっているような間接的な表現を考慮しつつ作成してください\n補足5:会話文の長さは15行以上\n補足6:会話の内容は自然な言い回しをしてください\n補足7:「〇〇さんに呼ばれた」のような会話内で登場しない人物から呼び出されたような展開も作成してください。この際に場所は”太郎さんの所”と出力してください\n補足8:人物が何かを行った動作や行おうとした動作、何処かへ向かう動作を会話文の中に明記してはいけない\n会話文を生成した後、誰(人物)が何処(場所)へ向かったのかを次のように返してください\npeople_place(人物|場所)",
    "stream": False
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
