from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import openai
import re
from googleapiclient.discovery import build


# OpenAI API 키 설정
challenge_api_key = 'sk-gapk-XPsXjmca7y06Ll7PUTrzM19hZ-e8syFu'
# GCP API Key 
gcp_api_key = "AIzaSyB4wZxsRGWNj0WoWURSNJ6bIXwAg7kkzyc"

# System Prompt 
system_prompt = """
너는 텍스트로 들어오는 다양한 정보들을 참고해서 레시피를 설명하는 AI 어시스턴트야. 
아래 사용자의 입력의 자막과 영상 상세정보를 참고해서 json object를 만들어줘. 
필요한 식재료는 "ingredients"로 구성하고, "recipe"는 각 요리의 단계와 요리 방법이야. 
단계별로 나눠줘야 해. 아래는 예시 프롬프트야. 

{
    "ingredients": ["밀가루 2컵", "차가운 버터 1컵", "설탕 1큰술", "소금 1/2 큰술", "찬물 4~6큰술", "사과", "계피 가루 1작은술"],
    "recipe": [
        "1. 반죽 만들기: 밀가루, 버터, 설탕, 소금을 섞어 찬물을 추가하며 반죽을 뭉친 뒤, 두 덩어리로 나눠 냉장고에서 1시간 휴지시킵니다.",
        "2. 필링 준비: 사과를 얇게 썰어 설탕, 갈색 설탕, 밀가루, 계피, 넛맥, 레몬즙과 섞어 필링을 만듭니다.",
        "3. 파이 조립: 반죽 한 덩어리를 밀어 틀에 깔고, 필링을 올린 뒤 버터 조각을 얹습니다. 나머지 반죽으로 덮거나 격자 모양을 만듭니다.",
        "4. 표면 처리: 윗면에 계란물을 발라주고, 칼로 공기 구멍을 몇 개 냅니다.",
        "5. 굽기: 200°C에서 15분, 이후 175°C에서 35~45분간 구워 황금빛이 날 때까지 완성합니다."
    ]
}
"""

def extract_video_id(url):
    """
    유튜브 URL에서 Video ID를 추출하는 함수
    """
    match = re.search(r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    return None

def get_video_details(youtube_url, api_key):
    """
    YouTube URL을 사용해 영상 정보를 호출하는 함수
    """
    # URL에서 Video ID 추출
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return {"error": "유효하지 않은 YouTube URL입니다."}

    # YouTube API 클라이언트 생성
    youtube = build("youtube", "v3", developerKey=api_key)

    # API 요청
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )
    response = request.execute()

    # 응답 처리
    if "items" not in response or len(response["items"]) == 0:
        return {"error": "영상 정보를 찾을 수 없습니다."}

    # 데이터 정리
    video_data = response["items"][0]
    snippet = video_data["snippet"]
    statistics = video_data["statistics"]
    content_details = video_data["contentDetails"]

    # 상세 정보 반환
    details = {
        "title": snippet.get("title", "정보 없음"),
        "description": snippet.get("description", "정보 없음"),
        "channel_title": snippet.get("channelTitle", "정보 없음"),
        "publish_date": snippet.get("publishedAt", "정보 없음"),
        "view_count": statistics.get("viewCount", "0"),
        "like_count": statistics.get("likeCount", "0"),
        "comment_count": statistics.get("commentCount", "0"),
        "duration": content_details.get("duration", "정보 없음"),
    }
    return details

def get_video_id(url):
    # URL에서 video_id 추출
    if "youtu.be" in url:
        return url.split("/")[-1]
    elif "youtube.com" in url:
        return url.split("v=")[1].split("&")[0]
    else:
        return None

def clean_youtube_subtitles(subtitles):
    """
    유튜브 자막 데이터를 깔끔하게 정리하는 함수.
    """
    cleaned_subtitles = []

    for subtitle in subtitles:
        text = subtitle['text']

        # 1. 불필요한 텍스트 제거
        text = text.strip()  # 앞뒤 공백 제거
        text = re.sub(r'\[.*?\]', '', text)  # [음악] 등 대괄호 제거
        text = re.sub(r'[^\w\sㄱ-ㅎ가-힣]', '', text)  # 특수 문자 제거
        text = re.sub(r'\s+', ' ', text)  # 여러 공백을 하나로 축소

        # 2. 의미 없는 짧은 문장 제거
        if len(text.split()) < 3:  # 단어가 3개 미만인 경우 제외
            continue

        cleaned_subtitles.append(text)

    return cleaned_subtitles

def summarize_youtube_video(url):
    video_id = get_video_id(url)

    # 유튜브 영상 상세 정보 추출
    video_info = get_video_details(url, gcp_api_key)
    video_description = video_info['description']


    if not video_id:
        return "올바른 YouTube URL이 아닙니다."

    try:
        # 자막 가져오기
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        # text = ' '.join([t['text'] for t in transcript])
        text = clean_youtube_subtitles(transcript)
        text = ' '.join(text)
        client = OpenAI(
            api_key=challenge_api_key,
            base_url="https://api.platform.a15t.com/v1",
        )

        # GPT-3.5 또는 GPT-4를 사용하여 텍스트 요약
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini-2024-07-18",
            messages=[{"role": "system", "content": system_prompt}, # 여기 수정해서 잘해보면 됨
                      {"role": "user", "content": f'자막 : {text}, 영상 상세정보 : {video_description}'}],
            response_format=None,
        )

        # Correctly access the text attribute
        summary = response.choices[0].message.content.strip()

        return summary
    except Exception as e:
        return f"요약 중 오류 발생: {str(e)}"
    

# if __name__ == "__main__":

#     # 사용 예시
#     url = "https://youtu.be/qWbHSOplcvY?si=wq9QdYJ4nGMJi-dX"
#     summary = summarize_youtube_video(url)
#     print(summary )