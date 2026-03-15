from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "SERVER IS RUNNING"

if __name__ == "__main__":
    print("✅ Server starting...")
    app.run(port=5500)