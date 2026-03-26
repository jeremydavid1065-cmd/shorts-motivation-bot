from flask import Flask, jsonify
import subprocess
import sys

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.post("/generate")
def generate():
    # Run the existing job generator module
    cmd = [sys.executable, "-m", "src.pipeline.generate_job"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return jsonify(
        ok=(result.returncode == 0),
        returncode=result.returncode,
        stdout=result.stdout[-4000:],  # keep response small
        stderr=result.stderr[-4000:],
    ), (200 if result.returncode == 0 else 500)
