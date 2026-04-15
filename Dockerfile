FROM python:3.11-slim

# Install LibreOffice for PDF conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate the Word template on build
RUN python template/create_template.py

EXPOSE 5000
CMD ["python", "run.py"]
