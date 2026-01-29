"""
API Routes for News Collector Dashboard
"""
from flask import Blueprint, jsonify, request
import threading
import uuid
import json
from pathlib import Path
import sys
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global task storage
analysis_tasks = {}
task_lock = threading.Lock()

# Email recipients configuration file
RECIPIENTS_FILE = Path(__file__).parent.parent / 'config' / 'email_recipients.json'


def get_recipients_file():
    """Get recipients file path"""
    file_path = Path(__file__).parent.parent / 'config' / 'email_recipients.json'
    return file_path


def load_recipients():
    """Load email recipients from configuration file"""
    try:
        file_path = get_recipients_file()
        if not file_path.exists():
            # Create default recipients file
            default_recipients = {
                "default_recipients": [
                    "sib1979@sk.com",
                    "minchaekim@sk.com",
                    "hyunju11.kim@sk.com",
                    "jieun.baek@sk.com",
                    "yjwon@sk.com",
                    "letigon@sk.com",
                    "lsm0787@sk.com",
                    "maclogic@sk.com",
                    "jungjaehoon@sk.com",
                    "hw.cho@sk.com",
                    "chlskdud0623@sk.com",
                    "youngmin.choi@sk.com",
                    "jinyeol.han@sk.com",
                    "jeongwoo.hwang@sk.com",
                    "funda@sk.com"
                ],
                "custom_recipients": []
            }
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_recipients, f, ensure_ascii=False, indent=2)
            return default_recipients

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading recipients: {e}")
        return {"default_recipients": [], "custom_recipients": []}


def save_recipients(recipients):
    """Save email recipients to configuration file"""
    try:
        file_path = get_recipients_file()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(recipients, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving recipients: {e}")
        return False


def run_analysis_task(task_id):
    """Run news collection and analysis task in background"""
    try:
        with task_lock:
            analysis_tasks[task_id]['status'] = 'running'
            analysis_tasks[task_id]['start_time'] = datetime.now().isoformat()
            analysis_tasks[task_id]['progress'] = 0

        # Import main collector
        from main import NewsCollector

        # Create collector instance
        collector = NewsCollector()

        # Update progress
        with task_lock:
            analysis_tasks[task_id]['progress'] = 10

        # Collect news
        logger.info(f"Task {task_id}: Starting news collection")
        all_news = collector.collect_all_categories()

        with task_lock:
            analysis_tasks[task_id]['progress'] = 50
            analysis_tasks[task_id]['news_collected'] = len(all_news)

        # Analyze news
        logger.info(f"Task {task_id}: Analyzing {len(all_news)} news items")
        analyzed_news = collector.analyze_news(all_news)

        with task_lock:
            analysis_tasks[task_id]['progress'] = 80
            analysis_tasks[task_id]['news_analyzed'] = len(analyzed_news)

        # Save results
        logger.info(f"Task {task_id}: Saving results")
        collector.save_results(analyzed_news)

        with task_lock:
            analysis_tasks[task_id]['status'] = 'completed'
            analysis_tasks[task_id]['progress'] = 100
            analysis_tasks[task_id]['end_time'] = datetime.now().isoformat()
            analysis_tasks[task_id]['result'] = {
                'total': len(analyzed_news),
                'by_category': {}
            }

            # Count by category
            for news in analyzed_news:
                category = news.get('category', 'unknown')
                if category not in analysis_tasks[task_id]['result']['by_category']:
                    analysis_tasks[task_id]['result']['by_category'][category] = 0
                analysis_tasks[task_id]['result']['by_category'][category] += 1

        logger.info(f"Task {task_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id}: Error - {e}")
        with task_lock:
            analysis_tasks[task_id]['status'] = 'failed'
            analysis_tasks[task_id]['error'] = str(e)
            analysis_tasks[task_id]['end_time'] = datetime.now().isoformat()


@api_bp.route('/analysis/start', methods=['POST'])
def start_analysis():
    """Start news collection and analysis task"""
    try:
        task_id = str(uuid.uuid4())

        # Initialize task
        with task_lock:
            analysis_tasks[task_id] = {
                'status': 'pending',
                'progress': 0,
                'start_time': None,
                'end_time': None,
                'news_collected': 0,
                'news_analyzed': 0,
                'error': None
            }

        # Start background task
        thread = threading.Thread(target=run_analysis_task, args=(task_id,))
        thread.daemon = True
        thread.start()

        logger.info(f"Started analysis task {task_id}")

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '뉴스 분석이 시작되었습니다'
        }), 200

    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        return jsonify({
            'success': False,
            'message': f'분석 시작 실패: {str(e)}'
        }), 500


@api_bp.route('/analysis/status/<task_id>', methods=['GET'])
def get_analysis_status(task_id):
    """Get analysis task status"""
    try:
        with task_lock:
            if task_id not in analysis_tasks:
                return jsonify({
                    'success': False,
                    'message': 'Task not found'
                }), 404

            task = analysis_tasks[task_id]

        return jsonify({
            'success': True,
            'status': task['status'],
            'progress': task['progress'],
            'news_collected': task.get('news_collected', 0),
            'news_analyzed': task.get('news_analyzed', 0),
            'error': task.get('error'),
            'result': task.get('result')
        }), 200

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/recipients', methods=['GET'])
def get_recipients():
    """Get all email recipients"""
    try:
        data = load_recipients()
        all_recipients = data['default_recipients'] + data['custom_recipients']

        return jsonify({
            'success': True,
            'recipients': all_recipients,
            'default_count': len(data['default_recipients']),
            'custom_count': len(data['custom_recipients'])
        }), 200

    except Exception as e:
        logger.error(f"Error getting recipients: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/recipients', methods=['POST'])
def add_recipient():
    """Add new email recipient"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({
                'success': False,
                'message': '이메일 주소를 입력해주세요'
            }), 400

        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({
                'success': False,
                'message': '올바른 이메일 형식이 아닙니다'
            }), 400

        recipients_data = load_recipients()
        all_recipients = recipients_data['default_recipients'] + recipients_data['custom_recipients']

        # Check if email already exists
        if email in all_recipients:
            return jsonify({
                'success': False,
                'message': '이미 존재하는 이메일 주소입니다'
            }), 400

        # Add to custom recipients
        recipients_data['custom_recipients'].append(email)

        if save_recipients(recipients_data):
            logger.info(f"Added new recipient: {email}")
            return jsonify({
                'success': True,
                'message': '이메일이 추가되었습니다',
                'email': email
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '이메일 저장 실패'
            }), 500

    except Exception as e:
        logger.error(f"Error adding recipient: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/recipients/<email>', methods=['DELETE'])
def remove_recipient(email):
    """Remove email recipient"""
    try:
        recipients_data = load_recipients()

        # Try to remove from custom recipients
        if email in recipients_data['custom_recipients']:
            recipients_data['custom_recipients'].remove(email)
            if save_recipients(recipients_data):
                logger.info(f"Removed recipient: {email}")
                return jsonify({
                    'success': True,
                    'message': '이메일이 삭제되었습니다'
                }), 200
        else:
            return jsonify({
                'success': False,
                'message': '기본 수신자는 삭제할 수 없습니다'
            }), 400

        return jsonify({
            'success': False,
            'message': '삭제 실패'
        }), 500

    except Exception as e:
        logger.error(f"Error removing recipient: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/email/send', methods=['POST'])
def send_email():
    """Send email to all recipients"""
    try:
        # Safely parse JSON request
        try:
            data = request.get_json(force=True, silent=True) or {}
        except Exception:
            data = {}

        recipients = data.get('recipients')

        # Load recipients if not provided
        if not recipients:
            recipients_data = load_recipients()
            recipients = recipients_data['default_recipients'] + recipients_data['custom_recipients']

        if not recipients:
            return jsonify({
                'success': False,
                'message': '수신자가 없습니다'
            }), 400

        # Get email credentials from environment
        gmail_user = os.getenv('GMAIL_USER')
        gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

        if not gmail_user or not gmail_app_password:
            return jsonify({
                'success': False,
                'message': '이메일 설정이 누락되었습니다. GMAIL_USER와 GMAIL_APP_PASSWORD 환경 변수를 확인해주세요.'
            }), 400

        # Import email sender
        from notifiers.smtp_sender import SMTPSender
        from notifiers.email_formatter import EmailFormatter

        # Get latest analyzed news
        output_dir = Path(__file__).parent.parent / 'output'
        html_files = list(output_dir.glob('*.html'))

        if not html_files:
            return jsonify({
                'success': False,
                'message': '발송할 뉴스가 없습니다. 먼저 분석을 실행해주세요.'
            }), 400

        # Get latest HTML file
        latest_html = max(html_files, key=lambda f: f.stat().st_mtime)

        # Read HTML content
        with open(latest_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Create sender with credentials
        sender = SMTPSender(user=gmail_user, password=gmail_app_password)

        # Send email to all recipients
        sender.send(html_content, recipients)

        logger.info(f"Email sent successfully to {len(recipients)} recipients")

        return jsonify({
            'success': True,
            'message': f'이메일 발송 완료: {len(recipients)}명 성공',
            'sent_count': len(recipients)
        }), 200

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 실패: {str(e)}'
        }), 500
