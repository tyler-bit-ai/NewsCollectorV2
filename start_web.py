"""
Web Server Launcher for News Collector Dashboard
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start the Flask web server"""
    try:
        # Import Flask app
        from web.app import create_app

        # Create app instance
        app = create_app()

        # Get configuration
        host = '0.0.0.0'
        port = 5000
        debug = True

        logger.info("=" * 60)
        logger.info("뉴스 수집기 웹 대시보드 시작")
        logger.info("=" * 60)
        logger.info(f"서버 주소: http://localhost:{port}")
        logger.info(f"대시보드: http://localhost:{port}/")
        logger.info("=" * 60)
        logger.info("서버를 종료하려면 Ctrl+C를 누르세요")
        logger.info("")

        # Start server
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )

    except KeyboardInterrupt:
        logger.info("\n서버가 사용자에 의해 종료되었습니다")
        sys.exit(0)
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
