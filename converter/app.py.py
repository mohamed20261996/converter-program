import os
from flask import Flask, render_template, request, send_file
import pandas as pd
from docx import Document
import pdfplumber
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert_file():
    if "file" not in request.files:
        return "لم يتم اختيار ملف", 400
    
    file = request.files["file"]
    target_format = request.form.get("format", "").lower()

    if file.filename == "":
        return "اسم الملف غير صحيح", 400

    filename = file.filename
    src_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(src_path)

    base_name = os.path.splitext(filename)[0]
    src_ext = os.path.splitext(filename)[1].lower()
    out_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_converted.{target_format}")

    try:
        # 1. تحويل الجداول (Excel / CSV / JSON)
        if src_ext in [".xlsx", ".xls", ".csv"]:
            df = pd.read_csv(src_path) if src_ext == ".csv" else pd.read_excel(src_path)
            if target_format == "xlsx":
                df.to_excel(out_path, index=False)
            elif target_format == "csv":
                df.to_csv(out_path, index=False, encoding="utf-8-sig")
            elif target_format == "json":
                df.to_json(out_path, orient="records", force_ascii=False, indent=4)

        # 2. تحويل الصور
        elif src_ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            img = Image.open(src_path)
            if img.mode in ("RGBA", "P") and target_format in ["jpg", "jpeg"]:
                img = img.convert("RGB")
            img.save(out_path)

        # 3. تحويل PDF إلى Word
        elif src_ext == ".pdf" and target_format == "docx":
            doc = Document()
            with pdfplumber.open(src_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        doc.add_paragraph(text)
            doc.save(out_path)

        else:
            return "الصيغة غير مدعومة حالياً", 400

        return send_file(out_path, as_attachment=True)

    except Exception as e:
        return f"حدث خطأ أثناء التحويل: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)