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
        
        # 안전 설정 (HARM_CATEGORY_ prefix 기반)
        # 법률 데이터 분석 중 차단을 방지하기 위해 최소화된 필터를 유지합니다.
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 모델 호출 (원래 동작하던 'gemini-flash-latest' 명칭 사용 및 도구 비활성화)
        try:
            model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            
            # 응답 검증 및 텍스트 추출
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                debug_log(f"Gemini 응답이 차단되거나 후보가 없습니다: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No candidates'}")
                return ""

        except Exception as e:
            debug_log(f"Gemini 모델 호출 중 오류 발생: {e}")
            return ""

    except Exception as e:
        debug_log(f"Gemini API 라이브러리 구성 중 오류 발생: {e}")
        return ""
