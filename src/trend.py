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
당신은 AI 법률 및 저작권 전문가입니다. 최근 {lookback_days}일간의 AI 관련 소송 및 뉴스 데이터를 분석하여 핵심 동향 요약 리포트를 한글로 작성해주세요.

[작성 지침]
1. 별도의 제목(예: "## {lookback_days}일간의...")은 생략하고 바로 본문부터 작성해주세요.
2. "AI Overview" 스타일로 정중하고 전문적인 톤으로 작성해주세요.
3. 현재 날짜와 최근 {lookback_days}일간의 가장 중요한 핵심 소송 및 동향을 3~5개 정도 핵심 위주로 요약해주세요.
4. 각 항목에는 반드시 해당 사건의 '출처'를 포함하고 가능하다면 마크다운 링크 형식으로 작성해주세요 (예: [출처 이름](URL)). 사용자가 직접 원문을 확인할 수 있도록 하기 위함입니다.
5. 각 항목은 '주체/사건명 (날짜): 핵심 내용 요약' 형식으로 작성해주세요.
6. 마지막에는 최근의 전반적인 '핵심 동향'을 한 문장으로 정리해주세요.

[제공된 데이터 - 뉴스]
{news_context}

[제공된 데이터 - 법원 소송]
{case_context}
"""

    debug_log(f"Gemini 동향 요약 생성 중 (데이터: 뉴스 {len(lawsuits)}건, 소송 {len(cl_cases)}건)")
    summary = get_gemini_summary(prompt)
    
    if not summary:
        return ""
        
    return summary.strip()
