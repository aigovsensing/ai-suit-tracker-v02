import os
import google.generativeai as genai
from typing import List, Optional
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

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Gemini API를 사용하여 텍스트 리스트의 임베딩을 생성합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not texts:
        return []

    try:
        genai.configure(api_key=api_key, transport='rest')
        # 한 번에 최대 100개까지 지원하므로 배치 처리가 필요할 수 있지만, 
        # 여기서는 보통 뉴스 건수가 적으므로 단순 호출합니다.
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document"
        )
        return result['embeddings']
    except Exception as e:
        debug_log(f"Gemini 임베딩 생성 중 오류 발생: {e}")
        return []

def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    두 벡터 간의 코사인 유사도를 계산합니다.
    """
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = sum(a * a for a in v1) ** 0.5
    norm_v2 = sum(a * a for a in v2) ** 0.5
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return dot_product / (norm_v1 * norm_v2)

from typing import List, Optional, Tuple

def generate_gemini_image(prompt: str, output_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Google AI Studio의 Imagen 3 모델을 사용하여 이미지를 생성하고 저장합니다.
    Returns: (saved_path, error_message)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        msg = "GEMINI_API_KEY가 설정되지 않아 이미지 생성을 건너뜀."
        debug_log(msg)
        return None, msg

    try:
        from google import genai as genai_new
        from google.genai import types
        
        client = genai_new.Client(api_key=api_key)
        
        # 지브리 스타일을 위한 프롬프트 강화
        enhanced_prompt = f"Studio Ghibli anime style illustration, {prompt}. Hand-drawn aesthetic, lush colors, whimsical lighting, detailed scenery, painterly texture."
        
        debug_log(f"이미지 생성 시도: {enhanced_prompt}")
        
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type='image/png',
                add_watermark=False
            )
        )

        if response.generated_images:
            img = response.generated_images[0]
            # output_path가 폴더인 경우 파일명 생성
            if os.path.isdir(output_path):
                from datetime import datetime
                filename = f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = os.path.join(output_path, filename)
            
            # 폴더 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 이미지 저장
            with open(output_path, "wb") as f:
                f.write(img.image.image_bytes)
            
            debug_log(f"이미지 저장 완료: {output_path}")
            return output_path, None
            
        return None, "이미지가 생성되었으나 응답 데이터가 비어 있습니다."
    except Exception as e:
        error_msg = str(e)
        debug_log(f"Gemini 이미지 생성 중 오류 발생: {error_msg}")
        return None, error_msg
