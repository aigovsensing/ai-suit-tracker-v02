# AI Lawsuit Monitor (CourtListener/RECAP & News Extractor)

AI 모델 학습을 위한 데이터 무단 사용 및 관련 저작권 소송을 추적하고 분석하는 자동화 도구입니다. 최근 3일 내의 소송 정보를 **CourtListener(RECAP Archive)**와 **뉴스(RSS)**에서 수집하여 GitHub Issue와 Slack으로 통합 리포트를 제공하며, 인텔리전트한 중복 제거 로직을 통해 최신 업데이트만 깔끔하게 확인할 수 있습니다.

## ✨ 핵심 기능

### 1. 🔍 다각도 소송 추적
- **CourtListener(RECAP) 정밀 탐색**: "PACER Document" 중 Complaint, Petition 등 소장 위주로 우선 수집합니다.
- **뉴스 기반 보강**: RSS 뉴스를 통해 최신 소송 소식을 수집하고, 관련 도켓(Docket) 정보를 역추적하여 상세 정보를 확장합니다.
- **지능형 쿼리**: 정밀한 키워드 조합(AI training, LLM, copyright, DMCA 등)을 사용하여 관련성 높은 항목만 필터링합니다.

### 2. ⚖️ 정밀 데이터 분석 & 위험도 평가
- **AI 학습 위험도 점수(0~100)**: 소장의 내용을 분석하여 저작권 직접 언급, 무단 수집, 학습 직접 언급, 상업적 이용 여부 등을 점수화하고 시각화(🟢, 🟡, ⚠️, 🔥)합니다.
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

## 🛠️ 설정 가이드

### 1. GitHub Secrets (필수)
Repository → Settings → Secrets and variables → Actions → New repository secret

| Name | Description |
|---|---|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `GITHUB_OWNER` | Repository 소유자 (예: `aigovsensing`) |
| `GITHUB_REPO` | Repository 이름 (예: `ai-suit-tracker-v02`) |
| `GITHUB_TOKEN` | GitHub API 토큰 (`secrets.GITHUB_TOKEN` 사용 가능) |

### 2. GitHub Variables (선택/권장)
| Name | Value (Default) | Description |
|---|---|---|
| `COURTLISTENER_TOKEN` | (선택 권장) | CourtListener API v4 인증 토큰 (일일 요청 한도 증대용) |
| `LOOKBACK_DAYS` | `3` | 며칠 전까지의 정보를 수집할지 설정 |
| `ISSUE_TITLE_BASE` | `AI 소송 모니터링` | 생성될 이슈의 기본 제목 |
| `DEBUG` | `0` | 1 설정 시 중복 제거 제외 사유 등 상세 디버그 로그 출력 |

## 🚀 실행 및 스케줄

### GitHub Actions (KST 최적화 스케줄)
- **업무 시간 (KST 08:00 - 20:00)**: 최신 공방 대응을 위해 **매 1시간마다** 정밀 실행
- **비업무 시간 (KST 22:00 - 06:00)**: 자원 효율화를 위해 **매 2시간마다** 실행
- `Actions` 탭에서 `workflow_dispatch`를 통해 즉시 실행 가능합니다.

### 로컬 실행
1. `pip install -r requirements.txt`
2. `.env` 파일 설정 (GITHUB 모듈 정보 및 Slack Webhook)
3. `python -m src.run`

## 📊 위험도 평가 기준 (Evaluation Matrix)

| 항목 | 조건 | 점수 |
|---|---|---|
| **저작권 직접 언급** | 820, 3820, 'copyright' 등 | +30 |
| **무단 데이터 수집 명시** | scrape, crawl, ingest, unauthorized 등 | +25 |
| **모델 학습 직접 언급** | train, training, model, llm, genai 등 | +20 |
| **저작권 관련/쟁점** | infringement, dmca, fair use, exclusive 등 | +10 |
| **상업적 사용** | commercial, profit, revenue, enterprise 등 | +10 |
| **집단소송** | class action, putative class 등 | +5 |
| **데이터 제공 계약/협력**| contract, licensing, partnership, 계약 등 | -10 |

- **80~100 🔥**: 무단 수집 + 학습 + 상업적 사용 (고위험 리스크)
- **60~79 ⚠️**: 모델 학습 직접 언급 및 관련 쟁점 수반
- **40~59 🟡**: 학습 데이터 관련 법적 쟁점 존재
- **0~39 🟢**: 간접 연관 또는 정식 계약 사례 (최소 0점 보정)

## 📚 참고문헌 (References)

본 프로젝트의 고도화와 AI 및 저작권법의 교차점 이해를 위해 참고하면 좋은 주요 논문 및 보고서입니다.

1. **Mark A. Lemley & Bryan Casey**, ["Fair Learning"](https://texaslawreview.org/fair-learning/), *Texas Law Review*, 2021. (머신러닝 학습 데이터를 공정 이용 관점에서 분석한 기초 문헌)
2. **Matthew Sag**, ["Copyright Safety for Generative AI"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4438599), *Houston Law Review*, 2023. (생성형 AI의 학습 데이터 수집과 저작권 침해 방지에 관한 실질적 가이드라인 제시)
3. **Peter Henderson et al.**, ["Foundation Models and Fair Use"](https://arxiv.org/abs/2303.15715), *arXiv preprint*, 2023. (파운데이션 모델이 직면한 저작권 쟁점과 법적 리스크 분석)
4. **Benjamin L. W. Sobel**, ["Artificial Intelligence's Fair Use Crisis"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3032483), *Columbia Journal of Law & the Arts*, 2017. (AI와 저작권 시스템 간의 마찰과 공정 이용의 한계 연구)
5. **Niva Elkin-Koren**, ["Controlling the Means of Creativity: Generative AI and the Future of Copyright"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4506671), *Cardozo Arts & Entertainment Law Journal*, 2023. (창작 수단으로서의 AI와 저작권법의 미래)
6. **Daniel J. Gervais**, ["The Human Cause as the Foundation of Copyright Law"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4524065), *Vanderbilt Law School*, 2023. (인간 저작자와 생성형 AI 간의 저작권 보호 범위 고찰)
7. **Pamela Samuelson**, ["Generative AI meets Copyright"](https://www.science.org/doi/10.1126/science.adi5127), *Science*, 2023. (생성형 AI가 저작권법 체계 전반에 던지는 시사점 요약)

## 📝 참고 사항
- **RECAP 데이터**: PACER에 등록된 문서 중 공개(RECAP)된 문서만 실물 접근 가능합니다.
- **KST 기준**: 모든 시간 포맷과 이슈 일자 분류는 한국 표준시(Asia/Seoul)를 따릅니다.
- **GitHub Permissions**: Workflow가 이슈를 생성/수정/종료할 수 있도록 `contents: read`, `issues: write` 권한이 필요합니다.UG` | `0` | 1 설정 시 상세 실행 로그(디버그 메세지) 출력 |

## 🚀 실행 및 로컬 환경

### GitHub Actions
- **매 시간 정각(UTC)** 자동 실행됩니다.
- `Actions` -> `lawsuit-monitor` -> `Run workflow`를 통해 수동 실행도 가능합니다.

### 로컬 실행
1. 저장소 클론 및 패키지 설치: `pip install -r requirements.txt`
2. `.env` 파일 생성 ( `.env.example` 참고 ):
   ```env
   GITHUB_OWNER=your_id
   GITHUB_REPO=your_repo
   GITHUB_TOKEN=your_pat
   SLACK_WEBHOOK_URL=your_url
   COURTLISTENER_TOKEN=your_cl_token
   DEBUG=1
   ```
3. 실행: `python -m src.run`

## 📊 위험도 평가 기준 (Evaluation Matrix)

| 항목 | 조건 (주요 키워드) | 점수 |
|---|---|---|
| **저작권 직접 언급** | 820, 3820, 'copyright' 등 | +30 |
| **무단 데이터 수집 명시** | scrape, crawl, ingest, harvest, mining, unauthorized 등 | +25 |
| **모델 학습 직접 언급** | train, training, model, llm, generative ai, diffusion 등 | +20 |
| **저작권 관련/쟁점** | infringement, dmca, fair use, derivative, exclusive 등 | +10 |
| **상업적 사용** | commercial, profit, monetiz, revenue, enterprise 등 | +10 |
| **집단소송** | class action, putative class, representative 등 | +5 |
| **데이터 제공 계약/협력** | contract, licensing, agreement, partnership, 계약 등 | -10 |

- **80~100 🔥**: 무단 수집 + 학습 + 상업적 사용 (고위험 리스크)
- **60~79 ⚠️**: 모델 학습 직접 언급 및 관련 쟁점 수반
- **40~59 🟡**: 학습 데이터 관련 법적 쟁점 존재
- **0~39 🟢**: 간접 연관 또는 일반적인 주변 이슈 (정식 계약 포함시 감점 적용)

## 📝 참고 사항
- **RECAP 데이터**: PACER에 등록된 문서 중 "공개(RECAP)"된 문서만 접근 가능합니다. 문서가 없는 경우 힌트 정보만 제공됩니다.
- **KST 기준**: 이슈 생성 및 타임스탬프는 한국 표준시(Asia/Seoul)를 기준으로 작동합니다.
- **GitHub Permissions**: Workflow 실행 시 `issues: write` 권한이 필요합니다.

