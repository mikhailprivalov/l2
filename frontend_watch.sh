#!/bin/bash

set -e

FRONTEND_DIR="l2-frontend"
ASSETS_DIR="assets/webpack_bundles"

echo "🚀 Запускаю frontend watch режим..."

cleanup() {
    echo "🛑 Останавливаю процессы..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

cd $FRONTEND_DIR
yarn build:watch &
YARN_PID=$!

cd ..

echo "👀 Отслеживаю изменения в $ASSETS_DIR..."

if command -v fswatch >/dev/null 2>&1; then
    fswatch -o $ASSETS_DIR | while read num; do
        echo "🔄 Обнаружены изменения, собираю статику..."
        poetry run python manage.py collectstatic --no-input --verbosity=0
        echo "✅ Статика обновлена"
    done
elif command -v inotifywait >/dev/null 2>&1; then
    while inotifywait -r -e modify,create,delete $ASSETS_DIR >/dev/null 2>&1; do
        echo "🔄 Обнаружены изменения, собираю статику..."
        poetry run python manage.py collectstatic --no-input --verbosity=0
        echo "✅ Статика обновлена"
    done
else
    echo "⚠️  fswatch или inotifywait не найдены, использую polling..."
    LAST_CHANGE=$(find $ASSETS_DIR -type f -name "*.js" -o -name "*.css" -o -name "*.json" | xargs stat -f "%m %N" 2>/dev/null | sort -n | tail -1 | cut -d' ' -f1)
    
    while true; do
        sleep 2
        CURRENT_CHANGE=$(find $ASSETS_DIR -type f -name "*.js" -o -name "*.css" -o -name "*.json" | xargs stat -f "%m %N" 2>/dev/null | sort -n | tail -1 | cut -d' ' -f1)
        
        if [ "$CURRENT_CHANGE" != "$LAST_CHANGE" ]; then
            echo "🔄 Обнаружены изменения, собираю статику..."
            poetry run python manage.py collectstatic --no-input --verbosity=0
            echo "✅ Статика обновлена"
            LAST_CHANGE=$CURRENT_CHANGE
        fi
    done
fi &

wait
