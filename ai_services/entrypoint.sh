#!/bin/bash
set -e

echo "Starting AI Services with Celery..."
echo "Redis URL: $CELERY_BROKER_URL"
echo "Worker concurrency: $CELERY_WORKER_CONCURRENCY"

# Ожидание готовности Redis
until redis-cli -h redis -p 6379 ping | grep -q "PONG"; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "Redis is ready. Starting Celery worker..."

# Запуск Celery worker
exec celery -A celery_app worker \
    --loglevel=$CELERY_WORKER_LOGLEVEL \
    --concurrency=$CELERY_WORKER_CONCURRENCY \
    --pool=threads \
    --queues=default,categorization,summarization,processing \
    --hostname=ai-services@%h 