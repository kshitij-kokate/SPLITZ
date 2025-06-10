import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from database import init_db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Initialize MongoDB
mongo = init_db(app)

# Import routes
from api_routes import api
from web_routes import web

# Register blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(web)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
