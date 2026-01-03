"""Authentication Module"""

import yaml
from functools import wraps
from flask import session, redirect

def load_config():
    """Load configuration from YAML"""
    try:
        with open('config/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

config = load_config()
USERS = config.get('users', {'admin': 'admin123', 'demo': 'demo123'})

def check_auth(username, password):
    """Check if username/password is valid"""
    return USERS.get(username) == password

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def is_authenticated():
    """Check if user is logged in"""
    return session.get('logged_in', False)

def get_current_user():
    """Get current logged in username"""
    return session.get('username', 'Guest')