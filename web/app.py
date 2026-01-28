"""
Flask Web Application for News Collector Dashboard
"""
from flask import Flask, render_template
from flask_cors import CORS
import logging

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config['SECRET_KEY'] = 'news-collector-secret-key-2024'

    # Enable CORS for all routes
    CORS(app)

    # Register blueprints
    from web.routes import api_bp
    app.register_blueprint(api_bp)

    # Main dashboard route
    @app.route('/')
    def dashboard():
        """Render main dashboard page"""
        return render_template('dashboard.html')

    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy'}, 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
