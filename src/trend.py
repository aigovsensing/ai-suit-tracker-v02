from typing import List
from .extract import Lawsuit
from .courtlistener import CLCaseSummary
from .gemini import get_gemini_summary
from .utils import debug_log

def generate_trend_summary(lawsuits: List[Lawsuit], cl_cases: List[CLCaseSummary], lookback_days: int) -> str:
    """
    수집된 뉴스 및 소송 데이터를 기반으로 Gemini를 통해 주요 동향 요약을 생성합니다.
    """
    
    # 데이터 요약 구성 (출처 URL 포함)
    news_context = ""
    for idx, s in enumerate(lawsuits, 1):
        url = s.article_urls[0] if s.article_urls else ""
        news_context += f"{idx}. {s.update_or_filed_date} | {s.article_title or s.case_title} | {s.reason} | 출처: {url}\n"
    
    case_context = ""
    for idx, c in enumerate(cl_cases, 1):
        # slug 생성 (utils의 공통 함수 사용)
        from .utils import slugify_case_name
        slug = slugify_case_name(c.case_name)
        docket_url = f"https://www.courtlistener.com/docket/{c.docket_id}/{slug}/"
        case_context += f"{idx}. {c.recent_updates} | {c.case_name} | Nature: {c.nature_of_suit} | Snippet: {c.extracted_ai_snippet or ''} | 출처: {docket_url}\n"

    prompt = f"""
당신은 AI 법률 및 저작권 전문가입니다. 지금 시간 기준으로 최근 {lookback_days}일 동안, 허가 받지 않은 데이터를 AI 모델 학습에 이용하여 발생한 소송들을 분석하여 한글로 1장짜리 보고서를 생성해주세요.

[보고서 구성 항목]
1. 개요: 최근 AI 소송 및 무단 데이터 사용 관련 동향의 전반적인 흐름 요약
2. 주요 소송 및 분쟁 현황: 제공된 데이터를 바탕으로 주요 소송 건들에 대한 구체적 현황 (주체, 사건명, 날짜, 핵심 내용 등)
3. 주요 법적 쟁점 및 향후 전망: 현재 주요하게 다뤄지는 법적 논점과 향후 소송 전개 방향 및 결과에 대한 전문적 예측
4. 시사점: 이번 동향이 AI 업계, 창작자, 소비자 및 관련 이해관계자들에게 주는 의미와 교훈
5. 삼성전자 제품 관련 여부: 삼성전자의 생성형 AI 모델(예: 가우스), 서비스 또는 디바이스(갤럭시 AI 등)에 미칠 수 있는 영향, 유사 리스크 존재 여부 또는 전략적 시사점

[작성 지침]
1. 별도의 대제목(예: "## {lookback_days}일간의...")은 생략하고 바로 '1. 개요'부터 작성해주세요.
2. "AI Overview" 스타일처럼 전문적이고 분석적이며 정중한 톤을 유지해주세요.
3. 각 소송 항목에는 가능한 경우 제공된 데이터의 '출처'를 마크다운 링크 형식으로 포함해주세요 (예: [출처 이름](URL)).
4. 제공된 데이터를 최대한 활용하되, 모델의 지식을 바탕으로 인터넷 검색 결과(필요 시)를 반영하여 내용을 풍성하게 구성해주세요.

[제공된 데이터 - 뉴스]
{news_context or "최근 수집된 뉴스가 없습니다."}

[제공된 데이터 - 법원 소송]
{case_context or "최근 수집된 법원 소송 데이터가 없습니다."}
"""

    debug_log(f"Gemini 동향 요약 생성 중 (데이터: 뉴스 {len(lawsuits)}건, 소송 {len(cl_cases)}건)")
    summary = get_gemini_summary(prompt)
    
    if not summary:
        return ""
        
    return summary.strip()
