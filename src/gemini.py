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
        
        # 'google_search_retrieval' 도구는 API 키 권한이나 지역에 따라 작동하지 않을 수 있으므로,
        # 실패 시 도구를 제외하고 기본 텍스트 생성으로 재시도하는 로직을 추가합니다.
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_retrieval": {}}]
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            debug_log(f"Gemini 도구(Search) 호출 실패, 기본 모델로 재시도합니다: {e}")
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text

    except Exception as e:
        debug_log(f"Gemini API 호출 중 최종 오류 발생: {e}")
        return ""
