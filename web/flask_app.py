from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "Discord Tournament Bot is running ✅"

@app.get("/health")
def health():
    return {"status": "ok"}
