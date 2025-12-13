import json
import boto3
import os

bedrock_client = boto3.client("bedrock-agent-runtime", region_name="ap-northeast-2")

FLOW_IDENTIFIER = os.environ["FLOW_ID"]          # ex) XRJ9VDEACA
FLOW_ALIAS_ID   = os.environ["FLOW_ALIAS_ID"]    # ex) B59SIC4X7Y

def lambda_handler(event, context):
    # 1) event에서 user_input 파싱


    user_input = event.get("user_input") or ""

    # 2) FlowInputNode.document 에 값 전달
    flow_inputs = [
        {
            "content": {"document": user_input},
            "nodeName": "FlowInputNode",
            "nodeOutputName": "document"
        }
    ]

    # 3) Flow 호출
    response = bedrock_client.invoke_flow(
        flowIdentifier=FLOW_IDENTIFIER,
        flowAliasIdentifier=FLOW_ALIAS_ID,
        inputs=flow_inputs,
    )

    # 4) 결과/에러 스트림 처리
    final_text = None
    flow_error = None

    for ev in response.get("responseStream", []):
        if "flowErrorEvent" in ev:
            flow_error = ev["flowErrorEvent"]
            break

        flow_output = ev.get("flowOutputEvent")
        if not flow_output:
            continue

        if flow_output.get("nodeName") != "FlowOutputNode":
            continue

        content = flow_output.get("content", {})
        doc = content.get("document")
        if isinstance(doc, str):
            final_text = doc
        elif isinstance(doc, dict):
            final_text = json.dumps(doc, ensure_ascii=False)

    if flow_error:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps({"flow_error": flow_error}, ensure_ascii=False),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps({"result": final_text}, ensure_ascii=False),
    }
