# Stage 1: Build the React SPA
FROM node:20-alpine AS frontend
WORKDIR /app
COPY src/ui/package*.json ./
RUN npm ci
COPY src/ui/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY --from=frontend /app/dist ./src/ui/dist/
EXPOSE 8000
CMD ["python", "-m", "src.main"]
