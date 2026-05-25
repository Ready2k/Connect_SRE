# Stage 1: Build React UI
FROM node:20-alpine AS ui-builder
WORKDIR /app/ui
COPY ui/package*.json ./
RUN npm install
COPY ui/ .
RUN npm run build

# Stage 2: Build FastAPI Backend
FROM python:3.11-slim
WORKDIR /app
COPY runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY runtime/ .

# Copy built UI static files from Stage 1
COPY --from=ui-builder /app/ui/dist /app/ui/dist

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
