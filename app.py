from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import PyPDF2
from transformers import pipeline
from keybert import KeyBERT
import os
import re
import logging
import time
# Tambahan untuk pemrosesan kalimat
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Batas file 10MB

# mengunakan model summarizer yang lebih ringan agar proses lebih cepat
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)  # device=-1 = CPU
kw_model = KeyBERT()

# Fungsi untuk membersihkan teks hasil ekstraksi PDF
def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Fungsi untuk menghapus bagian referensi/daftar pustaka
def remove_references(text):
    return re.sub(r'(References|Bibliography|Daftar Pustaka)(.*)', '', text, flags=re.DOTALL)

# Fungsi ekstraksi teks dari PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        empty_pages = 0
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            else:
                empty_pages += 1
        if empty_pages == len(reader.pages):
            logging.warning("Semua halaman kosong atau tidak dapat diekstrak.")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None

# Format dan filter hasil ringkasan agar hanya kalimat lengkap
def format_summary(raw_summary):
    sentences = sent_tokenize(raw_summary)
    clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 40 and s.strip().endswith(".")]
    return " ".join(clean_sentences)

@app.route("/", methods=["GET"])
def home():
    return "Smart Document Analyzer API is running. Please send a POST request to /analyze with a PDF file."

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".pdf"):
        return jsonify({"error": "File tidak valid. Harus PDF."}), 400

    try:
        text = extract_text_from_pdf(file)
        if not text:
            return jsonify({"error": "Tidak ada teks yang dapat diekstrak dari PDF."}), 400

        text = clean_text(remove_references(text))

        chunk_size = 1024
        overlap = 100
        max_chunks = 10
        chunks, start, count = [], 0, 0

        while start < len(text) and count < max_chunks:
            chunks.append(text[start:start+chunk_size])
            start += chunk_size - overlap
            count += 1

        summary_parts = []
        total_start = time.time()
        for idx, chunk in enumerate(chunks):
            try:
                chunk_start = time.time()
                result = summarizer(chunk, max_length=150, min_length=40, do_sample=False)
                summary_parts.append(result[0]["summary_text"])
                logging.info(f"Chunk {idx+1} diringkas dalam {time.time() - chunk_start:.2f} detik")
            except Exception as e:
                logging.warning(f"Gagal meringkas chunk {idx+1}: {e}")
                summary_parts.append("[Ringkasan gagal pada bagian ini]")

        processing_time = round(time.time() - total_start, 2)
        logging.info(f"Total waktu summarization: {processing_time:.2f} detik")

        summary = format_summary(" ".join(summary_parts))

        highlights = []
        try:
            keywords = kw_model.extract_keywords(text, top_n=5)
            highlights = [kw[0].capitalize() for kw in keywords if len(kw[0].split()) <= 4]
        except Exception as e:
            logging.warning(f"Gagal mengekstrak keyword: {e}")
            highlights = list(set(text.split()[:5]))

        return jsonify({
            "summary": summary,
            "highlights": highlights,
            "processing_time": processing_time,
            "formatted": {
                "summary": summary.strip(),
                "highlights": highlights[:5]
            }
        })

    except Exception as e:
        logging.error(f"Kesalahan server: {e}")
        return jsonify({"error": f"Gagal memproses file: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
