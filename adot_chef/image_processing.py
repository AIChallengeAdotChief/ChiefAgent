import openai
from openai import OpenAI
from PIL import Image
import base64

challenge_api_key = "sk-gapk-XPsXjmca7y06Ll7PUTrzM19hZ-e8syFu"

# Prompt 
image_system_prompt = """
너는 이제 두가지 역할을 수행하는 유능한 AI Assistant입니다. 사용자가 주는 사진을 분석해서 두가지 판단을 수행하면 됩니다.
1. 사진에 식재료가 존재하면 이미지에 있는 모든 사물을 나열해주세요. 그리고 나열한 사물(식재료)을 기반으로 만들 수 있는 요리를 3개 이상 추천해주세요 
Ex) "냉장고 속에 [식빵, 토마토, 감자, 식재료1, 식재료2] 가 있네요! 이 재료로 우리는 [제육볶음, 김치찌개, 볶음밥]을 만들 수 있어요

2. 사진이 요리를 하는 과정 중에 있는 사진이라고 분석하였다면, 현재 요리의 상태를 묘사해주세요.
Ex) "오 지금은 계란프라이를 만들고 있군요? 써니사이드업을 원하시면 지금 불을 꺼주세요!"

3. 1.와 2.가 아니라면 "사진이 이상해요! 냉장고 내부나 요리하는 사진을 올려주세요" 라고 말해주세요.
예시에 기반해서 답변을 생성해주고, 너무 많은 말을 추가하지 말아주세요
"""


# 이미지 파일을 base64로 인코딩하는 함수
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# ChatGPT API 호출 함수 (이미지 분석 포함)
def chat_with_gpt(image_base64):
    openai.api_key = challenge_api_key

    client = OpenAI(
            api_key=challenge_api_key,
            base_url="https://api.platform.a15t.com/v1",
        )

    response = client.chat.completions.create(
        model="openai/gpt-4-turbo-2024-04-09", 
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": image_system_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        response_format=None,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # 이미지 경로 지정
    # image_path = "/content/IMG_1170_JPEG.rf.106557445fb280eb6f5d9b94fef37810.jpg"
    image_path = "/content/sonjil.png"

    # 이미지 인코딩 수행
    image_base64 = encode_image_to_base64(image_path)

    # ChatGPT와 대화 수행 (이미지 분석 포함)
    gpt_response = chat_with_gpt(image_base64)
    print(gpt_response)