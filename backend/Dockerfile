FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Windows checkouts may produce CRLF. Normalize before executing inside Linux.
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod 755 /app/entrypoint.sh
EXPOSE 8000
# Invoking /bin/sh explicitly also avoids relying on shebang interpreter lookup.
CMD ["/bin/sh", "/app/entrypoint.sh"]
