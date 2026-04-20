import os
import google.generativeai as genai
from .utils import debug_log

def get_gemini_summary(prompt: str) -> str:
    """
    Gemini API를 사용하여 텍스트 요약을 생성합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        debug_log("GEMINI_API_KEY가 설정되지 않아 Gemini 요약을 건너뜁니다.")
        return ""

    try:
        genai.configure(api_key=api_key)
        # 2026년 기준 최신 Flash 모델 자동 매핑을 위해 flash-latest 사용
        # 인터넷 검색 소스 연동을 위한 tool 설정 추가
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            tools=[{"google_search_retrieval": {}}]
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        debug_log(f"Gemini API 호출 중 오류 발생: {e}")
        return ""
