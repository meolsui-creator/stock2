# -*- coding: utf-8 -*-
"""
stock2 웹 — 종목명만 입력하면 PPTX 리포트를 만들어 주는 간단한 Flask 앱.

흐름: 입력 → pipeline.generate_md (FDR 주가·차트 / DART 재무) →
      기존 report-pptx 스킬(build_pptx.py)로 PPTX 생성 → 다운로드.

실행:
  python -m pip install -r web/requirements.txt
  python web/app.py
  → http://127.0.0.1:5000
"""
import os
import sys
import subprocess
from urllib.parse import quote

from flask import Flask, request, render_template, send_file, abort

# 프로젝트 루트 = 이 파일(web/app.py)의 상위 폴더
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_PPTX = os.path.join(ROOT, ".claude", "skills", "report-pptx", "build_pptx.py")

# .env 로드 (DART_KEY 등) — python-dotenv 있으면 사용, 없으면 수동 파싱
def _load_env():
    env_path = os.path.join(ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except Exception:
        pass
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import generate_md  # noqa: E402

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    name = (request.form.get("name") or "").strip()
    if not name:
        return render_template("index.html", error="종목명을 입력해 주세요.")

    try:
        md_path, info = generate_md(name, ROOT)
    except Exception as e:
        return render_template("index.html", error=f"데이터 처리 중 오류: {e}", name=name)

    # 기존 PPTX 스킬 재사용
    proc = subprocess.run(
        [sys.executable, BUILD_PPTX, name, "--root", ROOT],
        capture_output=True, text=True, encoding="utf-8",
    )
    pptx_path = os.path.join(ROOT, "reports", "pptx", f"{name}.pptx")
    if proc.returncode != 0 or not os.path.isfile(pptx_path):
        return render_template(
            "index.html", name=name,
            error="PPTX 생성 실패: " + (proc.stderr or proc.stdout or "원인 불명"),
        )

    return render_template(
        "index.html",
        result=True,
        name=name,
        official=info["official"],
        code=info["code"],
        has_price=info["has_price"],
        has_fins=info["has_fins"],
        chart_url=("/chart?name=" + quote(name)) if info.get("chart_rel") else None,
        download_url="/download?name=" + quote(name),
    )


@app.route("/download")
def download():
    name = (request.args.get("name") or "").strip()
    path = os.path.join(ROOT, "reports", "pptx", f"{name}.pptx")
    if not name or not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"{name}.pptx")


@app.route("/chart")
def chart():
    name = (request.args.get("name") or "").strip()
    path = os.path.join(ROOT, "reports", "charts", f"{name}_price.png")
    if not name or not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
