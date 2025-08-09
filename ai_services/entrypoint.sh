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

echo "Redis is ready. Starting Celery Beat scheduler in background..."

# Чистим возможные "залипшие" pid/schedule от предыдущих перезапусков
if [ -f /tmp/celerybeat.pid ]; then
    echo "Found stale /tmp/celerybeat.pid, removing..."
    rm -f /tmp/celerybeat.pid
fi
if [ -f /tmp/celerybeat-schedule ]; then
    echo "Found stale /tmp/celerybeat-schedule, removing..."
    rm -f /tmp/celerybeat-schedule
fi

# Запуск Celery Beat в фоне для автоматических задач
celery -A celery_app beat \
    --loglevel=INFO \
    --pidfile=/tmp/celerybeat.pid \
    --schedule=/tmp/celerybeat-schedule &

echo "Celery Beat started. Starting Celery worker..."

# Запуск Celery worker с новой очередью monitoring
exec celery -A celery_app worker \
    --loglevel=$CELERY_WORKER_LOGLEVEL \
    --concurrency=$CELERY_WORKER_CONCURRENCY \
    --pool=threads \
    --queues=default,categorization,summarization,processing,orchestration,monitoring,testing,celery \
    --hostname=ai-services@%h 