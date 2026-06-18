import os
import json
import requests
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
    FormSubmit.co API를 사용하여 email.json에 등록된 수신자들에게 이메일을 발송합니다.
    """
    enable_sender = os.environ.get("ENABLE_EMAIL_SENDER") == "1"
    if not enable_sender:
        debug_log("이메일 전송 기능이 비활성화 상태입니다. (ENABLE_EMAIL_SENDER != 1)")
        return

    # 실행 환경의 작업 디렉토리에 맞게 상대 경로 탐색
    email_json_path = os.path.join("data", "email.json")
    if not os.path.exists(email_json_path):
        print(f"[WARNING] 이메일 전송 기능이 활성화되었으나 설정 파일이 존재하지 않습니다: {email_json_path}")
        return

    try:
        with open(email_json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] 이메일 설정 파일(email.json)을 읽거나 파싱하는 데 실패했습니다: {e}")
        return

    sender = config.get("sender", "")
    receivers = config.get("receivers", [])

    if not receivers:
        print("[WARNING] 이메일 수신자(receivers) 목록이 비어 있습니다.")
        return

    debug_log(f"이메일 발송 작업을 시작합니다. (수신인 수: {len(receivers)})")

    for receiver in receivers:
        receiver = receiver.strip()
        if not receiver:
            continue
        
        # FormSubmit API endpoint
        url = f"https://formsubmit.co/ajax/{receiver}"
        
        payload = {
            "sender": sender,
            "message": content,
            "_subject": subject,
            "_honey": "",
            "_captcha": "false"
        }
        
        try:
            debug_log(f"이메일 전송 요청 중: {receiver} (제목: {subject})")
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("success") == "true" or res_data.get("success") is True:
                    debug_log(f"이메일 전송 성공: {receiver}")
                else:
                    print(f"[ERROR] 이메일 전송 응답 오류 ({receiver}): {response.text}")
            else:
                print(f"[ERROR] 이메일 전송 실패 ({receiver}): {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] 이메일 전송 중 네트워크 또는 서버 오류 발생 ({receiver}): {e}")
