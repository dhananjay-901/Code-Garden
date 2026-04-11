from flask import Flask, render_template, request, jsonify
import os, base64, time

app = Flask(__name__)
os.makedirs("web_captures", exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json.get("image")
    if not data:
        return jsonify({"ok": False}), 400

    _, encoded = data.split(',', 1)
    img = base64.b64decode(encoded)

    name = f"web_captures/capture_{int(time.time())}.jpg"
    with open(name, 'wb') as f:
        f.write(img)

    return jsonify({"ok": True, "file": name})

if __name__ == '__main__':
    app.run(debug=True)
