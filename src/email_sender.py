import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .utils import debug_log

def get_subject_for_report(report_body: str, fallback_type: str, lookback_days: int = 3) -> str:
    """
    보고서 본문에서 제목(조간뉴스/석간뉴스)을 파싱하여 이메일 제목을 생성합니다.
    """
    for line in report_body.splitlines():
        line = line.strip()
        if "(조간뉴스)" in line:
            idx = line.find("(조간뉴스)")
            title_part = line[idx:].strip()
            title_part = title_part.replace("**", "").replace("*", "")
            return f'[ai.gov.sensing] "{title_part}"'
        elif "(석간뉴스)" in line:
            idx = line.find("(석간뉴스)")
            title_part = line[idx:].strip()
            title_part = title_part.replace("**", "").replace("*", "")
            return f'[ai.gov.sensing] "{title_part}"'

    if fallback_type == "morning":
        return f'[ai.gov.sensing] "(조간뉴스) {lookback_days}일간의 소송센싱 주요 동향 현황"'
    else:
        return '[ai.gov.sensing] "(석간뉴스) 당일 신규/업데이트 소송건 요약 보고서 (Gemini)"'


def send_email_report(subject: str, content: str) -> None:
    """
    Gmail SMTP를 사용하여 email.json 또는 환경 변수에 등록된 수신자들에게 이메일을 발송합니다.
    """
    enable_sender = os.environ.get("ENABLE_EMAIL_SENDER") == "1"
    if not enable_sender:
        debug_log("이메일 전송 기능이 비활성화 상태입니다. (ENABLE_EMAIL_SENDER != 1)")
        return

    # 환경 변수 및 설정 파일 로드
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port_str = os.environ.get("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587

    # Secrets / Variables 우선 순위 처리
    # SMTP_PASS가 없으면 SMTP_PASSWORD도 허용 (하위 호환성)
    smtp_password = os.environ.get("SMTP_PASS") or os.environ.get("SMTP_PASSWORD")
    smtp_user = os.environ.get("SMTP_USER")

    # 설정 파일(email.json) 정보 읽기 (환경 변수 백업/오버라이드용)
    email_json_path = os.path.join("data", "email.json")
    config = {}
    if os.path.exists(email_json_path):
        try:
            with open(email_json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[WARNING] 이메일 설정 파일(email.json) 파싱 실패: {e}")
    
    # 발신자 설정: EMAIL_FROM -> SMTP_USER -> config.sender -> default
    sender = os.environ.get("EMAIL_FROM") or smtp_user or config.get("sender", "")
    if not sender:
        print("[ERROR] 발신자 이메일 주소(sender/SMTP_USER)가 설정되지 않았습니다.")
        return

    # 로그인 사용자: SMTP_USER -> sender
    login_user = smtp_user or sender

    # 수신자 설정: EMAIL_TO (쉼표 구분) -> config.receivers -> [sender]
    email_to_env = os.environ.get("EMAIL_TO")
    if email_to_env:
        receivers = [r.strip() for r in email_to_env.split(",") if r.strip()]
    else:
        receivers = config.get("receivers", [])
        if not receivers:
            receivers = [sender]

    if not receivers:
        print("[WARNING] 이메일 수신자(receivers) 목록이 비어 있습니다.")
        return

    if not smtp_password:
        print("[ERROR] SMTP 비밀번호(SMTP_PASS/SMTP_PASSWORD 환경변수)가 설정되지 않았습니다.")
        return

    debug_log(f"이메일 발송 작업을 시작합니다. (수신인 수: {len(receivers)})")

    # 이메일 메시지 생성 (기존 본문 형식이 마크다운이므로 plain 텍스트 전송)
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject
    msg.attach(MIMEText(content, "plain", "utf-8"))

    try:
        debug_log(f"SMTP 서버 연결 중: {smtp_host}:{smtp_port}")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(login_user, smtp_password)
            
            for receiver in receivers:
                receiver = receiver.strip()
                if not receiver:
                    continue
                debug_log(f"이메일 전송 요청 중: {receiver} (제목: {subject})")
                server.sendmail(sender, [receiver], msg.as_string())
                debug_log(f"이메일 전송 성공: {receiver}")
    except Exception as e:
        print(f"[ERROR] 이메일 전송 중 SMTP 서버 오류 발생: {e}")


