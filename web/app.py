from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm Alive! Akari is running."

@app.route('/health')
def health():
    return {"status": "ok"}, 200

def run_flask():
    # Render는 PORT 환경 변수를 제공합니다. 없으면 8080
    import os
    port = int(os.environ.get("PORT", 8080))
    # host='0.0.0.0'은 외부 접속을 허용하기 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)

def start_web_server():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()