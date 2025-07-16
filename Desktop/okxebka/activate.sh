#!/bin/bash

echo "🔧 Активация виртуального окружения OKX Трейдера..."

# Переход в директорию проекта
cd "$(dirname "$0")"

# Проверка существования виртуального окружения
if [ ! -d ".venv" ]; then
    echo "❌ Виртуальное окружение не найдено!"
    echo "Создание нового окружения..."
    python3 -m venv .venv
fi

# Активация виртуального окружения
source .venv/bin/activate

echo "✅ Виртуальное окружение активировано!"
echo "Теперь вы можете использовать:"
echo "  pip install -r requirements.txt"
echo "  python test_connection.py"  
echo "  python main.py"
echo ""
echo "Для выхода из окружения введите: deactivate"

# Запуск новой оболочки с активированным окружением
exec $SHELL 