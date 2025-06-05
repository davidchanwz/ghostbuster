FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set default environment variables
ENV TELEGRAM_API_TOKEN="TOKEN"
ENV USE_WEBHOOK="false"
ENV WEBHOOK_HOST="localhost"
ENV WEBHOOK_PORT="8443"
# SSL is optional for development
ENV WEBHOOK_SSL_CERT=""
ENV WEBHOOK_SSL_PRIV=""
# Supabase environment variables (replace with your actual values in production)
ENV SUPABASE_URL="https://your-project-id.supabase.co"
ENV SUPABASE_API_KEY="your_supabase_api_key"

# Expose the webhook port
EXPOSE 8443

CMD ["python", "main.py"]
