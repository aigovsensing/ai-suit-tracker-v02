import os
import google.generativeai as genai
from .utils import debug_log

def get_gemini_model_name() -> str:
    """
    환경 변수에서 사용할 Gemini 모델명을 가져옵니다. 기본값은 'gemini-1.5-flash'입니다.
    """
    return os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

def get_gemini_model_display_name() -> str:
    """
    출력용으로 친숙한 모델 이름을 반환합니다.
    """
    model_name = get_gemini_model_name()
    if "gemini-1.5-flash" in model_name.lower() or "gemini-flash" in model_name.lower():
        return "Gemini 1.5 Flash"
    if "gemini-1.5-pro" in model_name.lower() or "gemini-pro" in model_name.lower():
        return "Gemini 1.5 Pro"
    if "gemini-2.0-flash" in model_name.lower():
        return "Gemini 2.0 Flash"
    
    # 환경변수에 직접 'Gemini 2.5 Flash' 처럼 넣었을 경우를 위해
    if "-" not in model_name and not model_name.islower():
        return model_name
        
    return "Gemini"

def get_gemini_summary(prompt: str) -> str:
    """
    Gemini API를 사용하여 텍스트 요약을 생성합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        debug_log("GEMINI_API_KEY가 설정되지 않아 Gemini 요약을 건너뜁니다.")
        return ""

    try:
        # REST 전송 방식을 사용하여 v1beta의 추가 메타데이터 필드를 더 안정적으로 가져오도록 설정
        genai.configure(api_key=api_key, transport='rest')
        
        # 안전 설정 (HARM_CATEGORY_ prefix 기반)
        # 법률 데이터 분석 중 차단을 방지하기 위해 최소화된 필터를 유지합니다.
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 모델 호출
        try:
            model_name = get_gemini_model_name()
            model = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings
            )
            response = model.generate_content(prompt)
            
            # 응답 검증 및 텍스트 추출
            if response.candidates and response.candidates[0].content.parts:
                # 모델 버전 및 서비스 티어 정보 추출 (to_dict() 및 직접 속성 접근 병용)
                resp_dict = {}
                try:
                    if hasattr(response, 'to_dict'):
                        resp_dict = response.to_dict()
                except Exception:
                    pass

                # 1) 모델 버전 추출 (최대한 다양한 경로 시도)
                model_version = None
                
                # 직접 속성 확인
                if hasattr(response, 'model_version'):
                    model_version = response.model_version
                
                # 내부 _result 객체 확인 (SDK 내부 proto 메시지)
                if not model_version and hasattr(response, '_result'):
                    model_version = getattr(response._result, 'model_version', None)
                
                # dict에서 확인
                if not model_version:
                    model_version = resp_dict.get('model_version') or resp_dict.get('modelVersion')
                
                # 최후의 수단: model_name 사용
                if not model_version:
                    model_version = model_name

                # 2) 서비스 티어 추출
                service_tier = '알 수 없음'
                
                # 직접 속성 확인
                usage_obj = getattr(response, 'usage_metadata', None)
                if usage_obj:
                    service_tier = getattr(usage_obj, 'service_tier', None) or getattr(usage_obj, 'serviceTier', None)
                
                # 내부 _result.usage_metadata 확인
                if (not service_tier or str(service_tier).lower() == 'none') and hasattr(response, '_result'):
                    usage_proto = getattr(response._result, 'usage_metadata', None)
                    if usage_proto:
                        service_tier = getattr(usage_proto, 'service_tier', None)
                
                # dict에서 확인
                if not service_tier or str(service_tier).lower() == 'none':
                    usage_dict = resp_dict.get('usage_metadata') or resp_dict.get('usageMetadata') or {}
                    service_tier = usage_dict.get('service_tier') or usage_dict.get('serviceTier')
                
                # 최종 포맷팅 및 기본값 처리
                if service_tier and str(service_tier).lower() != 'none':
                    service_tier = str(service_tier).capitalize()
                elif resp_dict.get('usage_metadata') or resp_dict.get('usageMetadata'):
                    service_tier = "Standard"

                debug_log(f"Gemini Metadata 추출 결과 - model_version: {model_version}, service_tier: {service_tier}")

                # 결과 상단에 정보 추가
                header = f"모델 정보: {model_version}\n서비스 티어: {service_tier}\n\n"
                return header + response.text
            else:
                debug_log(f"Gemini 응답이 차단되거나 후보가 없습니다: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No candidates'}")
                return ""

        except Exception as e:
            debug_log(f"Gemini 모델 호출 중 오류 발생: {e}")
            return ""

    except Exception as e:
        debug_log(f"Gemini API 라이브러리 구성 중 오류 발생: {e}")
        return ""
