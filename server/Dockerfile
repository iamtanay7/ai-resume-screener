FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server package (must be under /app/server/ so `server.*` imports resolve)
COPY server/ ./server/

# Cloud Run injects PORT env var; default to 8080
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port $PORT"]
