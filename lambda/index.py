import json
import os
import urllib.request
import urllib.parse
import re
from botocore.exceptions import ClientError

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# APIのURL（環境変数から取得）
API_URL = os.environ.get("API_URL", "https://0f49-35-240-154-247.ngrok-free.app")  # 環境変数を使う

# モデルID
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

def lambda_handler(event, context):
    try:
        # コンテキストから実行リージョンを取得し、クライアントを初期化
        region = extract_region_from_arn(context.invoked_function_arn)
        print(f"Initialized with region: {region}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # シンプルな形で、受け取ったメッセージをそのままプロンプトに設定
        prompt = message  # 受け取ったメッセージをそのまま使用

        # APIに送信するペイロードを構築
        request_payload = {
            "prompt": prompt,  # シンプルな形でメッセージをプロンプトとして使用
            "max_new_tokens": 512,  # 最大トークン数
            "stopSequences": [],    # 停止シーケンス
            "temperature": 0.7,     # 温度パラメータ
            "top_p": 0.9,           # top_pサンプリング
            "do_sample": True       # サンプリングの使用
        }

        # リクエストの作成（`urllib.request` を使用）
        data = json.dumps(request_payload).encode('utf-8')  # JSONデータをエンコード
        req = urllib.request.Request(API_URL + "/generate", data=data, headers={
            'Content-Type': 'application/json'
        })

        # APIにリクエストを送信
        response = urllib.request.urlopen(req)

        # 結果を取得
        response_data = json.load(response)

        # レスポンスの確認
        if 'generated_text' not in response_data:
            raise Exception("Failed to get valid response from the model")

        # アシスタントの応答（生成されたテキスト）
        assistant_response = response_data['generated_text']
        response_time = response_data.get('response_time', 'N/A')  # 応答時間がない場合に備えて

        print(f"Generated response: {assistant_response}")
        print(f"Response time: {response_time}")

        # 成功レスポンスを返す
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "response_time": response_time
            })
        }

    except Exception as error:
        print("Error:", str(error))

        # エラーハンドリングのレスポンスを返す
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
