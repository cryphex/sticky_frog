from flask import Flask
from threading import Thread
from waitress import serve
import os
app = Flask('')

@app.route('/')
def index():
    return 'Discord Bot ok'

def run():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
