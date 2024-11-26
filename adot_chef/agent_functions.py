# 함수 정의
functions = [
    {
        "name": "delete_session",
        "description": "현재 세션을 종료하고 삭제합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "삭제할 세션의 ID"
                }
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "summarize_youtube",
        "description": "유튜브 비디오의 내용을 요약합니다",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "요약할 유튜브 비디오의 URL"
                }
            },
            "required": ["url"]
        }
    }
]