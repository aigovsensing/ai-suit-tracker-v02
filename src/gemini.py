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
        
        # 안전 설정 카테고리명을 고도화된 상수 형태로 변경합니다 (HARM_CATEGORY_ prefix 권장)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 1차 시도: Google Search 도구 포함
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_retrieval": {}}],
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            # response.text 접근 전 candidates 존재 여부 확인 (차단 시 candidates[0].text 접근 불가)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                debug_log(f"Gemini 응답 비음: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No candidates'}")
        except Exception as e:
            debug_log(f"Gemini 도구(Search) 호출 실패: {e}")
            
        # 2차 시도 (Fallback): 도구 없이 기본 모델로 시도
        try:
            model = genai.GenerativeModel("gemini-1.5-flash", safety_settings=safety_settings)
            response = model.generate_content(prompt)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                debug_log("Gemini 기본 모델 응답이 차단되거나 비어있습니다.")
                return ""
        except Exception as e:
            debug_log(f"Gemini 기본 모델 최종 호출 실패: {e}")
            return ""

    except Exception as e:
        debug_log(f"Gemini API 라이브러리 구성 중 오류 발생: {e}")
        return ""
