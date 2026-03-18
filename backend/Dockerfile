FROM python:3.12-slim

# Dépendances système pour OCR, PDF, OpenCV
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Vérifier que pydantic v1 n'est pas en conflit puis télécharger modèles spaCy
RUN pip install --no-cache-dir --force-reinstall pydantic>=2.7 \
    && python -m spacy download fr_core_news_sm \
    && python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
