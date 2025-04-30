import json
import os
import urllib.request  # urllibをインポートしてAPIを呼び出す
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# APIのURL（Google Colabで立てたFastAPIサーバーのURL）
API_URL = "https://0f49-35-240-154-247.ngrok-free.app"  # 実際のAPI URLに置き換えます

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

        # 会話履歴を使用
        messages = conversation_history.copy()

        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        # APIに送信するペイロードを構築
        request_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }

        # JSON形式でエンコード
        data = json.dumps(request_payload).encode('utf-8')

        # HTTPリクエストの作成
        req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})

        # Google Colabで立てたFastAPIサーバーにリクエストを送信
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())

        # 結果の検証
        if not result.get('success', False):
            raise Exception("Failed to get valid response from the model")

        assistant_response = result['response']

        # 会話履歴にアシスタントの応答を追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

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
                "conversationHistory": messages
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
