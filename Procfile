web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 300 --worker-class eventlet -w 1 'trexima.web.app:create_app()'
