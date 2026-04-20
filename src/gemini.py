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
        
        # 안전 설정 카테고리명 (HARM_CATEGORY_ prefix)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 1차 시도: Google Search 도구 포함
        # SDK 0.8.0+ 버전에서는 도구명을 리스트에 직접 문자열로 넣는 방식이 더 안정적입니다.
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
                tools=["google_search_retrieval"],
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                debug_log(f"Gemini (Search) 응답 차단됨: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No candidates'}")
        except Exception as e:
            debug_log(f"Gemini 도구(Search) 호출 실패: {e}")
            
        # 2차 시도 (Fallback): 도구 없이 기본 모델로 시도
        # 모델 명칭을 gemini-1.5-flash-latest로 통일하여 404 에러를 방지합니다.
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest", safety_settings=safety_settings)
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
