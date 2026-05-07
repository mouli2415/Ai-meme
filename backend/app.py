"""
app.py
------
Flask backend for the AI Meme Generator.

Endpoints:
    POST /generate          — accepts {"topic": "..."}, returns meme data
    GET  /output/<filename> — serves generated images

Run:
    cd backend
    python app.py
"""

import os
import random
import textwrap
import traceback
import platform
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont

from model import generate_caption

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
@app.route("/")
def home():
    return "AI Meme Generator Backend Running!"
CORS(app)  # Allow the HTML frontend (opened as file://) to call this server

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "templates"))
OUTPUT_DIR    = os.path.abspath(os.path.join(BASE_DIR, "..", "output"))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Meme drawing settings ─────────────────────────────────────────────────────
SUPPORTED_EXT  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
FONT_SIZE      = 30
MAX_LINE_CHARS = 22
TEXT_COLOR     = "white"
OUTLINE_COLOR  = "black"
OUTLINE_WIDTH  = 2


# ── Helper: draw text with an outline ────────────────────────────────────────
def draw_outlined_text(draw, xy, text, font):
    x, y = xy
    for dx in range(-OUTLINE_WIDTH, OUTLINE_WIDTH + 1):
        for dy in range(-OUTLINE_WIDTH, OUTLINE_WIDTH + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=OUTLINE_COLOR)
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)


# ── Helper: split caption into top and bottom halves ─────────────────────────
def split_caption(caption: str):
    words = caption.split()
    if len(words) <= 3:
        return caption, ""
    mid    = len(words) // 2
    top    = " ".join(words[:mid])
    bottom = " ".join(words[mid:])
    return top, bottom


# ── Helper: load best available font ─────────────────────────────────────────
def load_font(size: int):
    system = platform.system()
    candidates = {
        "Windows": [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "Darwin": [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ],
    }.get(system, [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ])

    for path in candidates:
        if os.path.isfile(path):
            try:
                font = ImageFont.truetype(path, size)
                print(f"[app] Font loaded: {path}")
                return font
            except Exception:
                continue

    print("[app] No TTF font found — using PIL default font")
    return ImageFont.load_default()


# ── Core: draw caption onto a template image and save ────────────────────────
def create_meme(caption: str) -> str:
    # Pick random template
    all_files = [
        f for f in os.listdir(TEMPLATES_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXT
    ]
    if not all_files:
        raise FileNotFoundError(
            f"No images found in {TEMPLATES_DIR}. "
            "Add at least one .jpg or .png file to the templates/ folder."
        )

    chosen = random.choice(all_files)
    print(f"[app] Template: {chosen}")

    img = Image.open(os.path.join(TEMPLATES_DIR, chosen)).convert("RGB")
    w, h = img.size

    # Resize if too wide
    if w > 700:
        ratio = 700 / w
        img   = img.resize((700, int(h * ratio)), Image.LANCZOS)
        w, h  = img.size

    draw = ImageDraw.Draw(img)
    font = load_font(FONT_SIZE)
    line_h = FONT_SIZE + 8

    top_text, bottom_text = split_caption(caption)

    # ── Draw TOP text ──────────────────────────────────────────────────────
    top_lines = textwrap.wrap(top_text, width=MAX_LINE_CHARS) or [top_text]
    y = 10
    for line in top_lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw   = bbox[2] - bbox[0]
        except AttributeError:
            lw = len(line) * (FONT_SIZE // 2)
        x = max(0, (w - lw) // 2)
        draw_outlined_text(draw, (x, y), line, font)
        y += line_h

    # ── Draw BOTTOM text ──────────────────────────────────────────────────
    if bottom_text:
        bottom_lines = textwrap.wrap(bottom_text, width=MAX_LINE_CHARS) or [bottom_text]
        total_h = len(bottom_lines) * line_h
        y = h - total_h - 14
        for line in bottom_lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                lw   = bbox[2] - bbox[0]
            except AttributeError:
                lw = len(line) * (FONT_SIZE // 2)
            x = max(0, (w - lw) // 2)
            draw_outlined_text(draw, (x, y), line, font)
            y += line_h

    # Save
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"meme_{ts}.jpg"
    out_path = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path, "JPEG", quality=92)
    print(f"[app] Saved: {out_path}")
    return filename


# ── Route: POST /generate ─────────────────────────────────────────────────────
@app.route("/generate", methods=["POST"])
def generate():
    print("\n[app] POST /generate")

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Could not parse JSON body"}), 400

    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Missing required field: topic"}), 400

    print(f"[app] Topic: {topic}")

    try:
        caption = generate_caption(topic)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Caption generation failed: {e}"}), 500

    try:
        filename = create_meme(caption)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Meme creation failed: {e}"}), 500

    return jsonify({
        "caption":   caption,
        "image_url": f"http://localhost:5000/output/{filename}?t={datetime.now().timestamp()}",
    }), 200


# ── Route: GET /output/<filename> ─────────────────────────────────────────────
@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# ── Route: GET /health ────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  AI Meme Generator — Flask Backend")
    print("  http://localhost:5000")
    print(f"  Templates : {TEMPLATES_DIR}")
    print(f"  Output    : {OUTPUT_DIR}")
    print("=" * 55)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)