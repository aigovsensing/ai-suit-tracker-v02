# AI Lawsuit Monitor (CourtListener/RECAP & News Extractor)

AI 모델 학습을 위한 데이터 무단 사용 및 관련 저작권 소송을 추적하고 분석하는 자동화 도구입니다. 최근 3일 내의 소송 정보를 **CourtListener(RECAP Archive)**와 **뉴스(RSS)**에서 수집하여 GitHub Issue와 Slack으로 통합 리포트를 제공하며, 인텔리전트한 중복 제거 로직을 통해 최신 업데이트만 깔끔하게 확인할 수 있습니다.

## ✨ 핵심 기능

### 1. 🔍 다각도 소송 추적
- **CourtListener(RECAP) 정밀 탐색**: "PACER Document" 중 Complaint, Petition 등 소장 위주로 우선 수집합니다.
- **뉴스 기반 보강**: RSS 뉴스를 통해 최신 소송 소식을 수집하고, 관련 도켓(Docket) 정보를 역추적하여 상세 정보를 확장합니다.
- **지능형 쿼리**: 정밀한 키워드 조합(AI training, LLM, copyright, DMCA 등)을 사용하여 관련성 높은 항목만 필터링합니다.

### 2. ⚖️ 정밀 데이터 분석 & 감지 레벨 분석
- **비인가 데이터 학습 소송 감지 레벨(0~100)**: 소장의 내용을 분석하여 저작권 직접 언급, 무단 수집, 학습 직접 언급, 상업적 이용 여부 등을 점수화하고 시각화(🟢, 🟡, ⚠️, 🔥)합니다.
- **주요 섹션 추출**: 소장의 초반 텍스트에서 '소송 이유', 'AI 학습 관련 핵심 주장', '법적 근거'를 자동으로 추출하여 요약합니다.
- **통계 자동 산출**: **Nature of Suit (NOS)** 통계와 함께 각 코드별 의미 안내표를 제공하여 전반적인 법적 트렌드 분석을 돕습니다.

### 3. 🤖 스마트 리포팅 & 중복 제거 (Dedup)
- **일자별 통합 이슈**: 매일 하나의 GitHub Issue를 생성하고, 주기적 실행 결과를 댓글로 누적합니다.
- **강력한 중복 제거 시스템**:
    *   **이슈 내 중복 제거**: 현재 이슈 내에서 이미 보고된 내용을 제외합니다.
    *   **이슈 간 중복 제거 (Cross-Day Dedup)**: **날짜가 바뀌어 새 이슈가 생성되어도 전날 마지막 리포트와 중복되는 내용(뉴스 제목/소송 도켓번호 기준)은 자동으로 Skip** 처리하여 중복 열람의 피로도를 해소합니다.
- **가독성 최적화 (Folding)**: 리빙 섹션(동향 요약, NOS 통계, Top 3 소송 등)은 기본적으로 접음(fold) 처리되어 리포트가 길어져도 핵심을 빠르게 파악할 수 있습니다.
- **통합 정리 리포트**: 이슈 종료(Close) 직전, 당일에 수집된 모든 리포트 내용을 취합하여 **"당일 소송건들 통합 정리 자료"**를 최종 발행합니다.

### 4. 📢 실시간 알림 시스템
- **Slack 알람**: 중복 제거 요약, 수집 현황, 최신 RECAP 문서 링크를 포함한 요약을 실시간으로 발송합니다.
- **자동 이슈 관리**: 이전 날짜의 이슈를 자동으로 닫고 최신 이슈 링크를 연결하여 히스토리를 체계적으로 관리합니다.
 
### 5. 🤖 Gemini 인텔리전트 요약 & 동향 분석
- **AI 인텔리전트 요약**: 수집된 최신 소송 및 뉴스 데이터를 Gemini 모델이 실시간 분석하여 "AI Overview" 스타일의 핵심 트렌드 리포트를 발행합니다.
- **스마트 기능 안내 (Skip Notice)**: 기능이 비활성화된 경우, 사용자에게 활성화 방법을 안내하는 디자인틱한 안내 메시지를 자동으로 출력합니다.
 
### 6. 📝 계층형 댓글 구조 (Output Structure)
- **이슈 본문**: 데이터 수집 출처 및 법률 코드 안내 등 기본 가이드 제공
- **첫 번째 댓글**: Gemini 기반 "최근 3일간의 소송센싱 주요 동향 현황" 요약 리포트
- **두 번째 댓글**: 실행 시각, 중복 제거 요약, 뉴스/소송 상세 테이블이 포함된 메인 리포트

## 🛠️ 설정 가이드

### 1. GitHub Secrets (필수)
| Name | Description |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `GITHUB_OWNER` | Repository 소유자 (예: `aigovsensing`) |
| `GITHUB_REPO` | Repository 이름 (예: `ai-suit-tracker-v02`) |
| `GITHUB_TOKEN` | GitHub API 토큰 (`secrets.GITHUB_TOKEN` 사용 가능) |
| `GEMINI_API_KEY` | (선택/Gemini 사용 시) Google AI Studio API 키 |

### 2. GitHub Variables (선택/권장)
| Name | Value (Default) | Description |
|---|---|---|
| `COURTLISTENER_TOKEN` | (선택 권장) | CourtListener API v4 인증 토큰 |
| `LOOKBACK_DAYS` | `3` | 며칠 전까지의 정보를 수집할지 설정 |
| `ISSUE_TITLE_BASE` | `AI 소송 모니터링` | 생성될 이슈의 기본 제목 |
| `GEMINI_AISUIT_TREND_DAYS` | (공백) | **설정 시 Gemini 요약 기능 활성화.** 분석할 데이터의 기간(예: `3`)을 입력하면 해당 기간의 동향을 Gemini가 분석하여 발행합니다. (미설정 시 기능 레벨에서 비활성화) |
| `PREVIOUS_ITEM_DEDUP_DAYS` | (공백) | **설정 시 이전 날짜 이슈와 중복 체크 수행.** `3` 설정 시 최근 3일간의 이슈 댓글들을 확인하여 중복된 소송/뉴스는 리포트에서 제외합니다. (미설정 시 이전 이슈와 중복 체크 안 함) |
| `DEBUG` | `0` | 1 설정 시 상세 디버그 로그 출력 |

## 🚀 실행 및 스케줄

### GitHub Actions (KST 최적화 스케줄)
- **업무 시간 (KST 08:00 - 20:00)**: **매 1시간마다** 정밀 실행
- **비업무 시간 (KST 22:00 - 06:00)**: **매 2시간마다** 실행
- `Actions` 탭에서 수동 실행(`workflow_dispatch`)도 가능합니다.

### 로컬 실행
1. `pip install -r requirements.txt`
2. `.env` 파일 설정 (GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN, SLACK_WEBHOOK_URL 등)
3. `python -m src.run`

## 📊 비인가 데이터 학습 소송 감지 기준 (Detection Criteria)

| 항목 | 조건 | 점수 |
|---|---|---|
| **저작권 직접 언급** | 820, 3820, 'copyright' 등 | +30 |
| **무단 데이터 수집 명시** | scrape, crawl, ingest, unauthorized 등 | +25 |
| **모델 학습 직접 언급** | train, training, model, llm, genai 등 | +20 |
| **저작권 관련/쟁점** | infringement, dmca, fair use, exclusive 등 | +10 |
| **상업적 사용** | commercial, profit, revenue, subscription 등 | +10 |
| **집단소송** | class action, putative class 등 | +5 |
| **데이터 제공 계약/협력**| contract, licensing, partnership, 계약 등 | -10 |

- **감지 레벨 (Detection Level)**: 해당 건이 비인가 데이터 학습 소송과 얼마나 밀접한지를 표현합니다.
- **80~100 🔥**: 무단 수집 + 학습 + 상업적 사용 (Critical High)
- **60~79 ⚠️**: 모델 학습 직접 언급 및 관련 쟁점 수반 (High)
- **40~59 🟡**: 학습 데이터 관련 법적 쟁점 존재 (Medium)
- **0~39 🟢**: 간접 연관 또는 정식 계약 사례 (Low)

## 📝 참고 사항
- **RECAP 데이터**: PACER에 등록된 문서 중 공개(RECAP)된 문서만 실물 접근 가능합니다.
- **KST 기준**: 모든 시간 포맷과 이슈 일자 분류는 한국 표준시(Asia/Seoul)를 따릅니다.
- **GitHub Permissions**: Workflow가 이슈를 관리할 수 있도록 `contents: read`, `issues: write` 권한이 필요합니다.

## 📚 참고문헌 (References)


[1] M. A. Lemley and B. Casey, "Fair Learning," *Texas Law Review*, vol. 99, no. 4, pp. 743–785, Mar. 2021. \[Online\]. Available: [https://texaslawreview.org/fair-learning/](https://texaslawreview.org/fair-learning/) (preprint: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3528447](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3528447))

[2] M. Sag, "Copyright Safety for Generative AI," *Houston Law Review*, vol. 61, no. 4, pp. 295–347, 2023. \[Online\]. Available: [https://houstonlawreview.org/article/92126-copyright-safety-for-generative-ai](https://houstonlawreview.org/article/92126-copyright-safety-for-generative-ai) (preprint: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4438593](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4438593))

[3] P. Henderson *et al.*, "Foundation Models and Fair Use," arXiv preprint, arXiv:2303.15715, Mar. 2023. \[Online\]. Available: [https://arxiv.org/abs/2303.15715](https://arxiv.org/abs/2303.15715)

[4] B. L. W. Sobel, "Artificial Intelligence's Fair Use Crisis," *Columbia Journal of Law & the Arts*, vol. 41, no. 1, pp. 45–97, 2017. \[Online\]. Available: [https://journals.library.columbia.edu/index.php/lawandarts/article/view/2036](https://journals.library.columbia.edu/index.php/lawandarts/article/view/2036)

[5] N. Elkin-Koren, "Controlling the Means of Creativity: Generative AI and the Future of Copyright," *Cardozo Arts & Entertainment Law Journal*, vol. 41, no. 1, pp. 1–42, 2023. \[Online\]. Available: [https://larc.cardozo.yu.edu/aelj/](https://larc.cardozo.yu.edu/aelj/)  

[6] D. J. Gervais, "The Human Cause as the Foundation of Copyright Law," *Vanderbilt Law Review*, vol. 76, no. 4, pp. 1121–1180, May 2023. \[Online\]. Available: [https://vanderbiltlawreview.org](https://vanderbiltlawreview.org) (SSRN 선행 버전: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3857844](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3857844))

[7] P. Samuelson, "Generative AI meets Copyright," *Science*, vol. 381, no. 6654, pp. 158–161, July 2023. \[Online\]. Available: [https://www.science.org/doi/10.1126/science.adi0656](https://www.science.org/doi/10.1126/science.adi0656)

---