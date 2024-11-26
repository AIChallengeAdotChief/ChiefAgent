from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from openai import OpenAI
from typing import List, Dict
import uuid
import json
from search_youtube import summarize_youtube_video
from agent_functions import functions
from agent_prompt import system_prompt
import chainlit as cl

app = FastAPI()

class UserInput(BaseModel):
    content: str

class Conversation(BaseModel):
    messages: List[dict]

challenge_api_key = "sk-gapk-XPsXjmca7y06Ll7PUTrzM19hZ-e8syFu"
input_url = "https://a.sktelecom.com/"

client = OpenAI(
    api_key=challenge_api_key,
    base_url="https://api.platform.a15t.com/v1",
)

# 세션 저장소
sessions: Dict[str, List[dict]] = {}

class UserInput(BaseModel):
    content: str

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": system_prompt}]
    return sessions[session_id]

@app.post("/create_session")
async def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = [{"role": "system", "content": system_prompt}]
    return {"session_id": session_id}


@app.post("/adot_chef/{session_id}")
async def adot_chef_api(session_id: str, user_input: UserInput):
    conversation = get_session(session_id)
    conversation.append({"role": "user", "content": user_input.content})

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini-2024-07-18",
            messages=conversation,
            response_format=None,
            functions=functions,
            function_call="auto"
        )
        
        response_message = completion.choices[0].message

        if response_message.function_call:
            function_name = response_message.function_call.name
            function_args = response_message.function_call.arguments

            if function_name == "delete_session":
                await delete_session(session_id)
                return "다음에도 에이닷 쉐프랑 함께 요리해요!"
            
            elif function_name == "summarize_youtube":
                url = json.loads(function_args).get("url")
                summary = summarize_youtube(url)
                conversation.append({"role": "user", "content": "이 요리를 하고싶어요. "+summary})

                completion = client.chat.completions.create(
                model="openai/gpt-4o-mini-2024-07-18",
                messages=conversation,
                response_format=None,
                functions=functions,
                function_call="auto"
                )
                
                response_message = completion.choices[0].message

                assistant_response = response_message.content
                conversation.append({"role": "assistant", "content": assistant_response})

                return {"response": assistant_response}
        
        assistant_response = response_message.content
        conversation.append({"role": "assistant", "content": assistant_response})
        
        return {"response": assistant_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"conversation": sessions[session_id]}

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

def summarize_youtube(url: str) -> str:
    summary = summarize_youtube_video(url)


    return summary