from flask import Flask, jsonify
import time
app = Flask(__name__)
@app.route("/")
def handle():
    start = time.time()
    time.sleep(2.0)
    return jsonify({"server": "checkout", "delay": 2.0, "time": round(time.time() - start, 2)})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
