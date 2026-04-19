from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .fetch import fetch_news
from .extract import load_known_cases, build_lawsuits_from_news
from .render import render_markdown
from .github_issue import find_or_create_issue, create_comment, close_other_daily_issues
from .github_issue import list_comments
from .slack import post_to_slack
from .utils import debug_log, slugify_case_name
from .dedup import apply_deduplication
from .courtlistener import (
    search_recent_documents,
    build_complaint_documents_from_hits,
    build_case_summaries_from_hits,
    build_case_summaries_from_docket_numbers,
    build_case_summaries_from_case_titles,
    build_documents_from_docket_ids,
)
from .queries import COURTLISTENER_QUERIES
from .trend import generate_trend_summary

def main() -> None:
    # 0) 환경 변수 로드
    owner = os.environ.get("GITHUB_OWNER")
    repo = os.environ.get("GITHUB_REPO")
    gh_token = os.environ.get("GITHUB_TOKEN")
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")

    if not all([owner, repo, gh_token, slack_webhook]):
        missing = [k for k, v in {"GITHUB_OWNER": owner, "GITHUB_REPO": repo, "GITHUB_TOKEN": gh_token, "SLACK_WEBHOOK_URL": slack_webhook}.items() if not v]
        raise ValueError(f"필수 환경 변수가 누락되었습니다: {', '.join(missing)}")

    base_title = os.environ.get("ISSUE_TITLE_BASE", "AI 소송 모니터링")
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", "3"))
    # 필요 시 2로 변경: 환경변수 LOOKBACK_DAYS=2
    
    # KST 기준 날짜 생성
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    run_ts_kst = now_kst.strftime("%Y-%m-%d %H:%M")
    issue_day_kst = now_kst.strftime("%Y-%m-%d")
    issue_title = f"{base_title} ({issue_day_kst})"
    debug_log(f"KST 기준 실행시각: {run_ts_kst}")
    
    issue_label = os.environ.get("ISSUE_LABEL", "ai-lawsuit-monitor")

    # 1) CourtListener 검색
    hits = []
    for q in COURTLISTENER_QUERIES:
        debug_log(f"Running CourtListener query: {q}")
        hits.extend(search_recent_documents(q, days=lookback_days, max_results=20))
    
    # 중복 제거
    dedup = {}
    for h in hits:
        key = (h.get("absolute_url") or h.get("url") or "") + "|" + (h.get("caseName") or h.get("title") or "")
        dedup[key] = h
    hits = list(dedup.values())

    cl_docs = build_complaint_documents_from_hits(hits, days=lookback_days)
    # RECAP 도켓(사건) 요약: "법원 사건(도켓) 확인 건수"로 사용
    cl_cases = build_case_summaries_from_hits(hits)

    # 2) 뉴스 수집
    news = fetch_news()
    known = load_known_cases()
    lawsuits = build_lawsuits_from_news(news, known, lookback_days=lookback_days)

    # 2-1) 뉴스 테이블의 소송번호(도켓번호)로 RECAP 도켓/문서 확장
    docket_numbers = [s.case_number for s in lawsuits if (s.case_number or "").strip() and s.case_number != "미확인"]
    extra_cases = build_case_summaries_from_docket_numbers(docket_numbers)

    # 2-2) 소송번호가 없더라도, '소송제목'(추정 케이스명)으로 도켓 확장
    case_titles = [s.case_title for s in lawsuits if (s.case_title or "").strip() and s.case_title != "미확인"]
    extra_cases_by_title = build_case_summaries_from_case_titles(case_titles)

    merged_cases = {c.docket_id: c for c in (cl_cases + extra_cases + extra_cases_by_title)}
    cl_cases = list(merged_cases.values())

    # 문서도 docket id 기반으로 추가 시도(Complaint 우선, 없으면 fallback)
    docket_ids = list(merged_cases.keys())
    extra_docs = build_documents_from_docket_ids(docket_ids, days=lookback_days)
    merged_docs = {}
    for d in (cl_docs + extra_docs):
        key = (d.docket_id, d.doc_number, d.date_filed, d.document_url)
        merged_docs[key] = d
    cl_docs = list(merged_docs.values())

    docket_case_count = len(cl_cases)
    
    # =====================================================
    # FIX: RECAP 문서 건수 계산 방식 수정
    # 해결: cl_docs에 있는 것 + cl_cases 중 complaint_link가 있는 Docket ID 합산
    # =====================================================
    unique_dockets_with_docs = set()
    for d in cl_docs:
        if d.docket_id:
            unique_dockets_with_docs.add(d.docket_id)
    for c in cl_cases:
        if c.complaint_link and c.docket_id:
            unique_dockets_with_docs.add(c.docket_id)
    
    recap_doc_count = len(unique_dockets_with_docs)

    # =====================================================
    # NEW: DEBUG 모드 및 데이터 유무에 따른 실행 구조 개선
    # - DEBUG=1: 데이터가 없어도 항상 출력 (디버깅용)
    # - DEBUG=0 (기본): 데이터(News, Cases)가 모두 0건이면 출력/통지 건너뜀
    # =====================================================
    is_debug = os.environ.get("DEBUG") == "1"
    if not is_debug and len(lawsuits) == 0 and docket_case_count == 0:
        debug_log(f"데이터가 없으며 DEBUG=0이므로 리포트 생성 및 전송을 건너뜁니다. (News: 0, Cases: 0)")
        return

    # 3) 렌더링
    md = render_markdown(
        lawsuits,
        cl_docs,
        cl_cases,
        recap_doc_count,
        lookback_days=lookback_days,
    )



    # 4) GitHub Issue 작업
    issue_no = find_or_create_issue(owner, repo, gh_token, issue_title, issue_label)

    issue_url = f"https://github.com/{owner}/{repo}/issues/{issue_no}"

    # =========================================================
    # Baseline 비교 로직 (매 댓글 실시간 중복 제거 강화)
    # =========================================================
    # 1. 현재 이슈의 기존 댓글 (오늘 이미 보고된 내용 확인)
    current_comments = list_comments(owner, repo, gh_token, issue_no)
    
    # 2. 전날(이전 이슈)의 댓글도 항상 베이스라인에 포함 (Cross-Issue 연속성 유지)
    # [Mission] 오늘 첫 번째 댓글 뿐만 아니라, 이후 모든 'Add a comment' 시에도 전날 리포트와 중복되면 skip함
    from .github_issue import list_issues_by_label
    recent_issues = list_issues_by_label(owner, repo, gh_token, issue_label, state="all", per_page=10)
    other_issues = [it for it in recent_issues if int(it["number"]) < issue_no]
    
    prev_comments = []
    if other_issues:
        other_issues.sort(key=lambda x: int(x["number"]), reverse=True)
        prev_issue_no = int(other_issues[0]["number"])
        debug_log(f"이전 이슈 #{prev_issue_no}의 댓글을 베이스라인에 추가하여 중복을 필터링합니다.")
        prev_comments = list_comments(owner, repo, gh_token, prev_issue_no)
        
    # 오늘 수집된 댓글 + 어제 최종 댓글들을 모두 합쳐서 중복 제거 기준으로 사용
    all_baseline_comments = current_comments + prev_comments
    
    md, new_news_count, new_cases_count = apply_deduplication(md, all_baseline_comments)
    
    # 새로운 소식이 하나도 없는지 여부 확인
    no_new_updates = (new_news_count == 0 and new_cases_count == 0)

    if no_new_updates:
        md = "새로운 소식들이 없습니다."
    else:
        # 실행 시각(KST) 생성
        run_info = f"### 실행 시각(KST): {run_ts_kst}\n\n"
        
        # 4-2) Gemini를 통한 핵심 동향 요약 추가 (옵션 설정)
        trend_summary_section = ""
        trend_lookback = os.environ.get("GEMINI_AISUIT_TREND_DAYS")
        if trend_lookback:
            try:
                trend_days = int(trend_lookback)
                debug_log(f"Gemini 동향 요약 기능 활성화 (설정 기간: {trend_days}일)")
                trend_summary = generate_trend_summary(lawsuits, cl_cases, trend_days)
                if trend_summary:
                    trend_summary_section = f"## 🗓️ {trend_days}일간의 소송센싱 주요 동향 현황 (wih Gemini)\n\n{trend_summary}\n\n---\n\n"
                    debug_log("Gemini 동향 요약 생성 완료")
            except Exception as e:
                debug_log(f"Gemini 동향 요약 생성 중 오류 발생: {e}")

        # 최종 마크다운 조합 (요약 -> 실행시간 -> 본문)
        # 사용자의 요청에 맞춰 순서 조정: 요약 -> 실행시간 -> 본문
        md = trend_summary_section + run_info + md

    # 이전 날짜 이슈 Close
    closed_nums = close_other_daily_issues(owner, repo, gh_token, issue_label, base_title, issue_title, issue_no, issue_url)
    if closed_nums:
        debug_log(f"이전 날짜 이슈 자동 Close: {closed_nums}")
    
    debug_log(f"📊 수집 및 분석 완료 (최근 {lookback_days}일)")
    debug_log(f"  ├ News: {len(lawsuits)}건")
    debug_log(f"  └ Cases (CourtListener+RECAP): {docket_case_count}건 (문서 {recap_doc_count}건)")

    debug_log("===== REPORT PREVIEW (First 1000 chars) =====")
    debug_log(md[:1000])
    debug_log(f"Report full length: {len(md)}")

    # KST 기준 타임스탬프
    timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST")

    comment_body = f"\n\n{md}"
    create_comment(owner, repo, gh_token, issue_no, comment_body)
    debug_log(f"Issue #{issue_no} 리포트 및 요약 댓글 업로드 완료")

    # 5) Slack 요약 전송
    # ============================================
    # Slack 출력 개선 (최종 포맷)
    # ============================================

    slack_dedup_news = None
    slack_dedup_cases = None

    if "### 중복 제거 요약:" in md:
        m_news = re.search(
            r"└ News (.+)",
            md,
        )

        m_cases = re.search(
            r"└ Cases (.+)",
            md,
        )

        if m_news:
            line = m_news.group(1).strip()
            # GitHub용 강조(**)와 🔴 제거 (Slack용으로 재구성하기 위함)
            line = line.replace("**", "").replace(" 🔴", "")
            # New 수치가 0보다 크면 강조 (Bolding + 🔴)
            slack_dedup_news = re.sub(
                r"(\d+)\s+\(New\)",
                lambda m: f"*{m.group(1)} (New)*" + (" :red_circle:" if int(m.group(1)) > 0 else ""),
                line
            )

        if m_cases:
            line = m_cases.group(1).strip()
            # GitHub용 강조(**)와 🔴 제거
            line = line.replace("**", "").replace(" 🔴", "")
            slack_dedup_cases = re.sub(
                r"(\d+)\s+\(New\)",
                lambda m: f"*{m.group(1)} (New)*" + (" :red_circle:" if int(m.group(1)) > 0 else ""),
                line
            )



    if no_new_updates:
        # 새로운 소식이 없는 경우 아주 간단하게 전송
        slack_body = "새로운 소식들이 없습니다."
    else:
        slack_lines = []

        slack_lines.append(":bar_chart: AI 소송 모니터링")
        slack_lines.append(f"🕒 {timestamp}")
        slack_lines.append("")

        # 🔁 Dedup Summary
        if slack_dedup_news and slack_dedup_cases:
            slack_lines.append(":arrows_counterclockwise: Dedup Summary")
            slack_lines.append(f"└ News {slack_dedup_news}")
            slack_lines.append(f"└ Cases {slack_dedup_cases}")
            slack_lines.append("")

        # 📈 Collection Status
        slack_lines.append(":chart_with_upwards_trend: Collection Status")
        slack_lines.append(f"└ News: {len(lawsuits)}")
        slack_lines.append(
            f"└ Cases: {docket_case_count} (Docs: {recap_doc_count})"
        )
        slack_lines.append("")

        # 🔗 GitHub
        slack_lines.append(f":link: GitHub: <{issue_url}|#{issue_no}>")

        # 🆕 최신 RECAP 문서 (820 Copyright) - Top 3
        copyright_cases = []
        for c in cl_cases:
            nos = str(c.nature_of_suit or "").strip()
            if "820" in nos or "copyright" in nos.lower():
                copyright_cases.append(c)

        top_cases = sorted(
            copyright_cases,
            key=lambda x: x.recent_updates if x.recent_updates != "미확인" else "",
            reverse=True
        )[:3]

        if top_cases:
            slack_lines.append("")
            slack_lines.append(":new: 최신 RECAP 문서 (820 Copyright)")

            for c in top_cases:
                date = c.recent_updates if c.recent_updates != "미확인" else "N/A"
                name = c.case_name
                # slug 생성 (utils의 공통 함수 사용)
                slug = slugify_case_name(name)
                docket_url = f"https://www.courtlistener.com/docket/{c.docket_id}/{slug}/"
                
                slack_lines.append(f"• {date} | <{docket_url}|{name}>")
        
        slack_body = "\n".join(slack_lines)

    try:
        post_to_slack(slack_webhook, slack_body)
        debug_log(f"Slack 전송 완료")
    except Exception as e:
        debug_log(f"Slack 전송 실패: {e}")
        
if __name__ == "__main__":
    main()
