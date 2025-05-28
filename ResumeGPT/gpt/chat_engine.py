# gpt/chat_engine.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

def ask_with_resume(resume_text: str, user_input: str) -> str:
    prompt = f"""
너는 구직자가 업로드한 이력서를 기반으로 친절하고 말투가 부드러운 취업 상담 AI야.
이력서 내용은 아래와 같아:

--- 이력서 ---
{resume_text}
---------------

이제 아래 사용자 질문에 답해줘. 핵심 정보는 요약하되, 너무 기계처럼 말하지 말고 자연스럽게 대화해줘.

사용자 질문: {user_input}
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 이력서 기반 취업 상담 챗봇이야. 말투는 친근하고 부드러워야 해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT 오류] {str(e)}"

def ask_with_jobseeker_list(jobseeker_infos: list, employer_input: str) -> str:
    # jobseeker_infos: [{"name": "홍길동", "text": "이력서 내용..."}, ...]
    combined_text = ""
    for i, info in enumerate(jobseeker_infos, start=1):
        combined_text += f"{i}. 이름: {info['name']}\n이력서 요약:\n{info['text']}\n\n"

    prompt = f"""
당신은 채용담당자 AI입니다. 아래는 현재 지원한 구직자들의 정보입니다:

{combined_text}

위 목록을 참고하여 다음 질문에 답해주세요:
질문: "{employer_input}"
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 채용 담당자를 도와주는 AI야. 구직자 이력서를 바탕으로 조건에 맞는 사람을 추천해줘."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT 오류] {str(e)}"