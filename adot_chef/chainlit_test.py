import chainlit as cl
import requests
from PIL import Image
import PIL
import io
from image_processing import *

base_url = "http://localhost:8000"
session_id = None

@cl.on_chat_start
async def start():
    global session_id
    # 새 세션 생성
    session_response = requests.post(f"{base_url}/create_session")
    session_id = session_response.json()["session_id"]
    await cl.Message("안녕하세요! 어떤 요리에 관심있으신가요?").send()

    actions = [
        cl.Action(name="yes_button", value="yes", label="네"),
        cl.Action(name="no_button", value="no", label="아니요, 추가 도움이 필요합니다.")
    ]
    # await cl.Message(content="도움이 되셨나요?", actions=actions).send()

@cl.action_callback("yes_button")
async def on_yes(action):
    actions = [
        cl.Action(name="yes_button", value="yes", label="네"),
        cl.Action(name="no_button", value="no", label="아니요, 추가 도움이 필요합니다.")
    ]

    response = requests.post(f"{base_url}/adot_chef/{session_id}", json={"content": "네"})
    ai_response = response.json().get("response", "네")
    await cl.Message(content=ai_response, actions=actions).send()

@cl.action_callback("no_button")
async def on_no(action):
    actions = [
        cl.Action(name="yes_button", value="yes", label="네"),
        cl.Action(name="no_button", value="no", label="아니요, 추가 도움이 필요합니다.")
    ]

    response = requests.post(f"{base_url}/adot_chef/{session_id}", json={"content": "아니요, 추가 도움이 필요합니다."})
    ai_response = response.json().get("response", "아니요, 추가 도움이 필요합니다.")
    await cl.Message(content=ai_response, actions=actions).send()

@cl.on_message
async def main(message: cl.Message):
    global session_id

    if message.elements:
        # 이미지가 업로드된 경우
        for element in message.elements:

            
            if isinstance(element, cl.Image) and element.path:
                
                img = encode_image_to_base64(element.path)
                
                # img = Image.open(element.path)

                # 이미지 처리 (chat_with_gpt 함수는 별도로 구현해야 함)
                image_description = chat_with_gpt(img)
                
                # API 요청
                response = requests.post(f"{base_url}/adot_chef/{session_id}", json={"content": image_description})
                
                ai_response = response.json().get("response", "이미지 처리가 완료되었습니다.")
                await cl.Message(content=f"{ai_response}").send()
                await cl.Image(name="uploaded_image", content=element.content, display="inline").send()
    else:
        # 텍스트 메시지 처리
        response = requests.post(f"{base_url}/adot_chef/{session_id}", json={"content": message.content})
        
        actions = [
        cl.Action(name="yes_button", value="yes", label="네"),
        cl.Action(name="no_button", value="no", label="아니요, 추가 도움이 필요합니다.")
        ]
        ai_response = response.json().get("response", "응답을 받지 못했습니다.")
        await cl.Message(content=f"{ai_response}", actions=actions).send()

@cl.on_chat_end
async def end():
    global session_id
    if session_id:
        # 세션 종료 처리 (필요한 경우)
        requests.post(f"{base_url}/adot_chef/{session_id}", json={"content": "대화를 종료합니다."})
        session_id = None

if __name__ == "__main__":
    cl.run()