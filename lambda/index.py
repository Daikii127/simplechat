import json
import os
import requests
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

        # 会話履歴を使用
        bedrock_messages = conversation_history.copy()

        # ユーザーメッセージを追加
        bedrock_messages.append({
            "role": "user",
            "content": message
        })

        # APIに送信するペイロードを構築
        request_payload = {
            "prompt": bedrock_messages,  # 会話履歴（bedrock_messages）
            "maxTokens": 512,            # 最大トークン数
            "stopSequences": [],         # 停止シーケンス
            "temperature": 0.7,          # 温度パラメータ
            "top_p": 0.9,                # top_pサンプリング
            "doSample": True             # サンプリングの使用
        }

        # HTTPリクエストの作成
        headers = {'Content-Type': 'application/json'}

        # FastAPIサーバーにリクエストを送信
        response = requests.post(API_URL + "/generate", json=request_payload, headers=headers)

        # 結果の検証
        if response.status_code != 200:
            raise Exception(f"Failed to get valid response from the model: {response.status_code}")

        result = response.json()

        if not result.get('generated_text', False):
            raise Exception("Failed to get valid response from the model")

        # アシスタントの応答（生成されたテキスト）
        assistant_response = result['generated_text']
        response_time = result['response_time']  # APIが返した総リクエスト時間を使用

        # 会話履歴にアシスタントの応答を追加
        bedrock_messages.append({
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
                "conversationHistory": bedrock_messages,
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
