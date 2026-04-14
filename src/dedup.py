from __future__ import annotations
import re
from typing import List, Set, Tuple
from .utils import debug_log

def extract_section(md_text: str, section_title: str) -> str:
    """Markdown 텍스트에서 특정 섹션 제목(또는 포함됨) 아래의 내용을 추출합니다."""
    lines = md_text.split("\n")
    start = None
    end = None
    
    # 윈도우 줄바꿈 등 처리 위해 strip() 사용
    target = section_title.strip().lower()

    for i, line in enumerate(lines):
        clean_line = line.strip().lower()
        if target in clean_line:
            start = i + 1
            continue
        # 다음 ## 섹션이 나오면 종료 (단, 자신은 제외)
        if start is not None and line.startswith("## "):
            end = i
            break
            
    if start is None:
        return ""
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end])

def parse_table(section_md: str) -> Tuple[List[str], List[List[str]], Tuple[str, str]]:
    """Markdown 테이블을 헤더, 행 데이터, 메타데이터(헤더/구분선 라인)로 파싱합니다."""
    lines = [l for l in section_md.split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return [], [], ("", "")

    header = lines[0]
    separator = lines[1]
    rows = lines[2:]

    def split_row(row_text: str) -> List[str]:
        # 역슬래시로 이스케이프되지 않은 파이프만 분할
        return [c.strip() for c in re.split(r'(?<!\\)\|', row_text.strip())[1:-1]]

    header_cols = split_row(header)
    parsed_rows = []
    for row in rows:
        cols = split_row(row)
        if len(cols) == len(header_cols):
            parsed_rows.append(cols)
        else:
            debug_log(f"Table row column mismatch: expected {len(header_cols)}, got {len(cols)}. Row: {row[:100]}...")

    return header_cols, parsed_rows, (header, separator)

def extract_article_url(cell: str) -> str | None:
    """Markdown 링크 셀에서 URL을 추출합니다."""
    m = re.search(r"\((https?://[^\)]+)\)", cell)
    if m:
        return m.group(1).split("&hl=")[0]
    return None

def apply_deduplication(md: str, comments: List[dict]) -> tuple[str, int, int, int]:
    """
    이전 GitHub 댓글들을 분석하여 중복된 데이터를 'skip' 처리하고 요약을 추가합니다.
    (News, Cases, Documents 통합 처리)
    """
    # 섹션 타이틀 정의
    NEWS_SECTION_TITLE = "## 📰 AI Suit News"
    CASES_SECTION_TITLE = "## ⚖️ Cases (Courtlistener+RECAP)"
    DOC_SECTION_TITLE = "📄 Cases: 법원 문서 기반"

    if not comments:
        # 댓글이 없는 경우, 현재 md에서 행 수 파싱
        news_section = extract_section(md, NEWS_SECTION_TITLE)
        _, n_rows, _ = parse_table(news_section)
        
        recap_section = extract_section(md, CASES_SECTION_TITLE)
        _, c_rows, _ = parse_table(recap_section)
        
        doc_section = extract_section(md, DOC_SECTION_TITLE)
        _, d_rows, _ = parse_table(doc_section)
        
        return md, len(n_rows), len(c_rows), len(d_rows)

    # 1) Baseline Key Sets 생성
    base_article_set: Set[str] = set()
    base_docket_set: Set[str] = set()
    base_doc_set: Set[str] = set()

    for comment in comments:
        body = comment.get("body") or ""
        
        # News
        news_s = extract_section(body, NEWS_SECTION_TITLE)
        h_n, r_n, _ = parse_table(news_s)
        if h_n and "제목" in h_n:
            idx = h_n.index("제목")
            for r in r_n:
                url = extract_article_url(r[idx])
                if url: base_article_set.add(url)
        
        # Cases
        recap_s = extract_section(body, CASES_SECTION_TITLE)
        h_c, r_c, _ = parse_table(recap_s)
        if h_c and "도켓번호" in h_c:
            idx = h_c.index("도켓번호")
            for r in r_c:
                base_docket_set.add(r[idx])
        
        # Documents
        doc_s = extract_section(body, DOC_SECTION_TITLE)
        h_d, r_d, _ = parse_table(doc_s)
        if h_d and "법원 문서" in h_d:
            idx = h_d.index("법원 문서")
            for r in r_d:
                url = extract_article_url(r[idx])
                if url: base_doc_set.add(url)

    current_md = md

    # 2) News 처리
    news_section = extract_section(current_md, NEWS_SECTION_TITLE)
    n_headers, n_rows, n_table_meta = parse_table(news_section)
    new_article_count = 0
    total_article_count = len(n_rows)

    if n_headers and "제목" in n_headers:
        title_idx = n_headers.index("제목")
        no_idx = n_headers.index("No.") if "No." in n_headers else None
        header_line, separator_line = n_table_meta
        non_skip_rows = []
        for r in n_rows:
            url = extract_article_url(r[title_idx])
            if url in base_article_set:
                debug_log(f"Skipping duplicate News: {url}")
            else:
                non_skip_rows.append(r)
                new_article_count += 1
        
        if new_article_count == 0:
            new_news_section = "새로운 소식이 0건입니다.\n"
        else:
            new_lines = [header_line, separator_line]
            for i, r in enumerate(non_skip_rows, 1):
                if no_idx is not None: r[no_idx] = str(i)
                new_lines.append("| " + " | ".join(r) + " |")
            new_news_section = "\n".join(new_lines) + "\n"
        current_md = current_md.replace(news_section, new_news_section)

    # 3) Cases 처리
    recap_section = extract_section(current_md, CASES_SECTION_TITLE)
    c_headers, c_rows, c_table_meta = parse_table(recap_section)
    new_docket_count = 0
    total_docket_count = len(c_rows)

    if c_headers and "도켓번호" in c_headers:
        do_idx = c_headers.index("도켓번호")
        no_idx = c_headers.index("No.") if "No." in c_headers else None
        header_line, separator_line = c_table_meta
        non_skip_rows = []
        for r in c_rows:
            docket = r[do_idx]
            if docket in base_docket_set:
                debug_log(f"Skipping duplicate Case: {docket}")
            else:
                non_skip_rows.append(r)
                new_docket_count += 1
        if new_docket_count == 0:
            new_recap_section = "새로운 소식이 0건입니다.\n"
        else:
            new_lines = [header_line, separator_line]
            for i, r in enumerate(non_skip_rows, 1):
                if no_idx is not None: r[no_idx] = str(i)
                new_lines.append("| " + " | ".join(r) + " |")
            new_recap_section = "\n".join(new_lines) + "\n"
        current_md = current_md.replace(recap_section, new_recap_section)

    # 4) Documents 처리
    doc_section = extract_section(current_md, DOC_SECTION_TITLE)
    d_headers, d_rows, d_table_meta = parse_table(doc_section)
    new_doc_count = 0
    total_doc_count = len(d_rows)

    if d_headers and "법원 문서" in d_headers:
        doc_idx = d_headers.index("법원 문서")
        no_idx = d_headers.index("No.") if "No." in d_headers else None
        header_line, separator_line = d_table_meta
        non_skip_rows = []
        for r in d_rows:
            url = extract_article_url(r[doc_idx])
            if url in base_doc_set:
                debug_log(f"Skipping duplicate Document: {url}")
            else:
                non_skip_rows.append(r)
                new_doc_count += 1
        if new_doc_count == 0:
            # Document 섹션은 <details> 내부에 있는 경우가 많으므로 단순 텍스트로 대체 시 구조가 깨질 수 있음.
            # 하지만 render_markdown에서 cl_docs가 없으면 섹션 자체를 생성 안 하므로,
            # 여기서는 테이블 내용만 "0건"으로 바꿈.
            new_doc_section = "새로운 문서가 0건입니다.\n"
        else:
            new_lines = [header_line, separator_line]
            for i, r in enumerate(non_skip_rows, 1):
                if no_idx is not None: r[no_idx] = str(i)
                new_lines.append("| " + " | ".join(r) + " |")
            new_doc_section = "\n".join(new_lines) + "\n"
        current_md = current_md.replace(doc_section, new_doc_section)

    # 5) 중복 제거 요약 생성
    summary_header = (
        "### 중복 제거 요약:\n"
        "🔁 Dedup Summary\n"
        f"└ News: **{new_article_count} (New)**" + (" 🔴" if new_article_count > 0 else "") + "\n"
        f"└ Cases: **{new_docket_count} (New)**" + (" 🔴" if new_docket_count > 0 else "") + "\n"
        f"└ Docs: **{new_doc_count} (New)**" + (" 🔴" if new_doc_count > 0 else "") + "\n\n"
    )

    return summary_header + current_md, new_article_count, new_docket_count, new_doc_count


def generate_consolidated_report(comments: List[dict]) -> str:
    """
    모든 댓글의 내용을 취합하여 통합된 리포트를 생성합니다.
    """
    if not comments:
        return "수집된 리포트 내용이 없습니다."

    unique_news = {}  # URL -> row list
    unique_cases = {}  # Docket -> row list
    unique_docs = {}  # URL -> row list

    news_header_line = None
    news_sep_line = None
    news_header_cols = []

    case_header_line = None
    case_sep_line = None
    case_header_cols = []

    doc_header_line = None
    doc_sep_line = None
    doc_header_cols = []

    # 섹션 타이틀 (apply_deduplication과 통일)
    NEWS_TITLE = "## 📰 AI Suit News"
    CASES_TITLE = "## ⚖️ Cases (Courtlistener+RECAP)"
    DOCS_TITLE = "📄 Cases: 법원 문서 기반"

    for comment in comments:
        body = comment.get("body") or ""

        # 1) News 파싱
        news_section = extract_section(body, NEWS_TITLE)
        h_news, r_news, meta_news = parse_table(news_section)
        if h_news and "제목" in h_news:
            title_idx = h_news.index("제목")
            if not news_header_line:
                news_header_cols = h_news
                news_header_line, news_sep_line = meta_news
            
            for r in r_news:
                url = extract_article_url(r[title_idx])
                key = url if url else r[title_idx]
                if key not in unique_news:
                    unique_news[key] = r

        # 2) Cases 파싱
        recap_section = extract_section(body, CASES_TITLE)
        h_cases, r_cases, meta_cases = parse_table(recap_section)
        if h_cases and "도켓번호" in h_cases:
            docket_idx = h_cases.index("도켓번호")
            if not case_header_line:
                case_header_cols = h_cases
                case_header_line, case_sep_line = meta_cases
            
            for r in r_cases:
                docket = r[docket_idx]
                if docket not in unique_cases:
                    unique_cases[docket] = r

        # 3) Documents 파싱
        doc_section = extract_section(body, DOCS_TITLE)
        h_docs, r_docs, meta_docs = parse_table(doc_section)
        if h_docs and "법원 문서" in h_docs:
            doc_idx = h_docs.index("법원 문서")
            if not doc_header_line:
                doc_header_cols = h_docs
                doc_header_line, doc_sep_line = meta_docs
            
            for r in r_docs:
                url = extract_article_url(r[doc_idx])
                if url and url not in unique_docs:
                    unique_docs[url] = r

    lines = ["## 📑 당일 소송건들 통합 정리 자료\n"]

    # News 통합 출력
    lines.append("### 📰 통합 AI Suit News")
    if unique_news:
        lines.append(news_header_line)
        lines.append(news_sep_line)
        
        # 위험도 예측 점수 기준으로 내림차순 정렬
        news_rows = list(unique_news.values())
        if "위험도⬇️" in news_header_cols:
            risk_idx = news_header_cols.index("위험도⬇️")
            def get_news_risk_score(row):
                # "🟡 45"와 같은 문자열에서 숫자만 추출
                m = re.search(r"(\d+)", row[risk_idx])
                return int(m.group(1)) if m else 0
            news_rows.sort(key=get_news_risk_score, reverse=True)

        no_idx = news_header_cols.index("No.") if "No." in news_header_cols else None
        for i, row_data in enumerate(news_rows, 1):
            row = list(row_data)
            if no_idx is not None:
                row[no_idx] = str(i)
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("수집된 뉴스 소식이 없습니다.")
    lines.append("")

    # Cases 통합 출력
    lines.append("### ⚖️ 통합 Cases (Courtlistener+RECAP)")
    if unique_cases:
        lines.append(case_header_line)
        lines.append(case_sep_line)
        
        # 위험도 기준으로 내림차순 정렬
        case_rows = list(unique_cases.values())
        if "위험도⬇️" in case_header_cols:
            risk_idx = case_header_cols.index("위험도⬇️")
            def get_case_risk_score(row):
                # "🟡 45"와 같은 문자열에서 숫자만 추출
                m = re.search(r"(\d+)", row[risk_idx])
                return int(m.group(1)) if m else 0
            case_rows.sort(key=get_case_risk_score, reverse=True)

        no_idx = case_header_cols.index("No.") if "No." in case_header_cols else None
        for i, row_data in enumerate(case_rows, 1):
            row = list(row_data)
            if no_idx is not None:
                row[no_idx] = str(i)
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("수집된 사건 소식이 없습니다.")
    lines.append("")

    # Documents 통합 출력
    lines.append("### 📄 통합 법원 문서 (RECAP Docs)")
    if unique_docs:
        lines.append(doc_header_line)
        lines.append(doc_sep_line)
        
        doc_rows = list(unique_docs.values())
        # 날짜(제출일⬇️) 기준 내림차순 정렬 시도
        if "제출일⬇️" in doc_header_cols:
            date_idx = doc_header_cols.index("제출일⬇️")
            doc_rows.sort(key=lambda r: r[date_idx], reverse=True)

        no_idx = doc_header_cols.index("No.") if "No." in doc_header_cols else None
        for i, row_data in enumerate(doc_rows, 1):
            row = list(row_data)
            if no_idx is not None:
                row[no_idx] = str(i)
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("수집된 법원 문서가 없습니다.")
    lines.append("")

    return "\n".join(lines)
