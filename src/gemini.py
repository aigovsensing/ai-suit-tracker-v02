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
        
        # 'google_search_retrieval' 도구는 환경에 따라 불리할 수 있으므로 안전장치를 강화합니다.
        # 또한 법률/소송 분석 중 특정 기업 언급이 시스템 필터에 걸리지 않도록 안전 설정을 조정합니다.
        safety_settings = [
            {"category": "HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_retrieval": {}}],
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            if response.text:
                return response.text
        except Exception as e:
            debug_log(f"Gemini 도구(Search) 호출 실패 혹은 차단, 기본 모델로 재시도합니다: {e}")
            
        # Fallback: 도구 없이 시도
        try:
            model = genai.GenerativeModel("gemini-1.5-flash", safety_settings=safety_settings)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            debug_log(f"Gemini 기본 모델 호출 실패: {e}")
            return ""

    except Exception as e:
        debug_log(f"Gemini API 구성 중 최종 오류 발생: {e}")
        return ""
