"""
API Routes for News Collector Dashboard
"""
from flask import Blueprint, jsonify, request
import threading
import uuid
from pathlib import Path
import sys
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from config.recipient_store import (
    GROUP_TO_KEY,
    add_group_recipient,
    get_group_recipients,
    remove_group_recipient,
)

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global task storage
analysis_tasks = {}
task_lock = threading.Lock()

def _resolve_group():
    group = request.args.get("group", "report").strip()
    if group not in GROUP_TO_KEY:
        return None, (
            jsonify({
                'success': False,
                'message': '유효하지 않은 group 입니다. report 또는 safety_alert를 사용하세요.'
            }),
            400
        )
    return group, None


def run_analysis_task(task_id):
    """Run news collection and analysis task in background"""
    try:
        with task_lock:
            analysis_tasks[task_id]['status'] = 'running'
            analysis_tasks[task_id]['start_time'] = datetime.now().isoformat()
            analysis_tasks[task_id]['progress'] = 0

        # Import main collector
        from main import NewsCollector, send_safety_alert_notification

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
        analyzed_news['external_alerts'] = collector.collect_external_alerts()

        with task_lock:
            analysis_tasks[task_id]['progress'] = 80
            analysis_tasks[task_id]['news_analyzed'] = len(analyzed_news)

        # Save results
        logger.info(f"Task {task_id}: Saving results")
        collector.save_results(analyzed_news)

        # 해외 안전 공지 자동 메일 발송
        if analyzed_news.get('external_alerts'):
            logger.info(f"Task {task_id}: Sending safety alert digest")
            send_safety_alert_notification(analyzed_news['external_alerts'], collector.settings)

        with task_lock:
            analysis_tasks[task_id]['status'] = 'completed'
            analysis_tasks[task_id]['progress'] = 100
            analysis_tasks[task_id]['end_time'] = datetime.now().isoformat()
            analysis_tasks[task_id]['result'] = {
                'total': 'Analysis completed',
                'message': '분석이 완료되었습니다'
            }

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
        group, error_response = _resolve_group()
        if error_response:
            return error_response
        recipients = get_group_recipients(group)

        return jsonify({
            'success': True,
            'group': group,
            'recipients': recipients,
            'count': len(recipients)
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
        group, error_response = _resolve_group()
        if error_response:
            return error_response

        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip()

        success, message, recipients = add_group_recipient(email=email, group=group)
        if not success:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        logger.info(f"Added recipient ({group}): {email}")
        return jsonify({
            'success': True,
            'message': message,
            'email': email,
            'group': group,
            'count': len(recipients)
        }), 200

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
        group, error_response = _resolve_group()
        if error_response:
            return error_response

        success, message, recipients = remove_group_recipient(email=email, group=group)
        if success:
            logger.info(f"Removed recipient ({group}): {email}")
            return jsonify({
                'success': True,
                'message': message,
                'group': group,
                'count': len(recipients)
            }), 200
        return jsonify({
            'success': False,
            'message': message
        }), 400

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
            recipients = get_group_recipients("report")

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
        html_files = list(output_dir.glob('**/*.html'))  # 하위 폴더 포함 모든 HTML 파일 검색

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


@api_bp.route('/latest-report', methods=['GET'])
def get_latest_report():
    """Get the latest HTML report file path"""
    try:
        output_dir = Path(__file__).parent.parent / 'output'
        html_files = list(output_dir.glob('**/*.html'))

        if not html_files:
            return jsonify({
                'success': False,
                'message': '생성된 리포트가 없습니다'
            }), 404

        # Get latest HTML file by modification time
        latest_html = max(html_files, key=lambda f: f.stat().st_mtime)

        # Get relative path from output directory
        relative_path = latest_html.relative_to(output_dir)

        return jsonify({
            'success': True,
            'filename': latest_html.name,
            'relative_path': str(relative_path),
            'url': f'/output/{relative_path}'
        }), 200

    except Exception as e:
        logger.error(f"Error getting latest report: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
