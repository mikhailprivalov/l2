#!/bin/bash

set -e

echo "🔥 Запускаю HMR режим..."

if lsof -ti:8000 >/dev/null 2>&1 || lsof -ti:8081 >/dev/null 2>&1; then
    read -r -p "Найдены занятые порты 8000/8081. Очистить? [y/N]: " answer
    case "$answer" in
        [yY]|[yY][eE][sS])
            echo "🧹 Очищаю порты 8000 и 8081..."
            lsof -ti:8000 | xargs kill -9 2>/dev/null || true
            lsof -ti:8081 | xargs kill -9 2>/dev/null || true
            echo "✅ Порты очищены."
            ;;
        *)
            echo "⏭ Пропускаю и завершаю скрипт."
            exit 0
            ;;
    esac
fi

echo "Для остановки нажмите Ctrl+C"

cleanup() {
    echo ""
    echo "🛑 Останавливаю процессы..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

export FRONTEND_HMR=1

echo "🚀 Запускаю Django на порту 8000..."
poetry run python manage.py runserver 8000 &
DJANGO_PID=$!

sleep 2

echo "🔧 Запускаю Vue dev-server..."
cd l2-frontend
yarn serve:hmr &
VUE_PID=$!

cd ..

echo "✅ Оба сервера запущены! Открой http://127.0.0.1:8000 в браузере"

wait
