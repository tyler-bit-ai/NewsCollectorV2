"""
SMTP 이메일 발송
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging
from datetime import datetime

from utils.exceptions import NotificationError
from utils.retry import retry

logger = logging.getLogger(__name__)


class SMTPSender:
    """SMTP 발송기"""

    def __init__(self, user: str, password: str):
        """
        Args:
            user: Gmail 주소
            password: Gmail 앱 비밀번호
        """
        self.user = user
        self.password = password

    @retry(max_attempts=3)
    def send(self, html_content: str, recipients: List[str]) -> bool:
        """
        이메일 발송

        Args:
            html_content: HTML 본문
            recipients: 수신자 리스트

        Returns:
            성공 시 True

        Raises:
            NotificationError: 발송 실패
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[SKT 로밍팀] 일일 뉴스 리포트 - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.user
        msg['To'] = ", ".join(recipients)

        msg.attach(MIMEText(html_content, 'html', _charset='utf-8'))

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            # 백업: 파일로 저장
            self._backup_to_file(html_content)
            raise NotificationError(f"이메일 발송 실패: {e}")

    def _backup_to_file(self, html_content: str):
        """발송 실패 시 백업 파일 저장"""
        import os
        from datetime import datetime

        backup_dir = "output/backups"
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"email_backup_{timestamp}.html")

        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Email backed up to: {backup_file}")
