#!/bin/bash

echo "=========================================="
echo "       OKX Futures Trader"
echo "=========================================="
echo

# Проверка установки Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не установлен!"
    echo "Установите Python 3 с https://python.org"
    exit 1
fi

# Создание виртуального окружения если его нет
if [ ! -d ".venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv .venv
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source .venv/bin/activate

echo "Установка зависимостей..."
pip install -r requirements.txt

echo
echo "Проверка соединения с OKX API..."
python test_connection.py

echo
echo "Запуск приложения..."
python main.py

echo
echo "Приложение закрыто."
read -p "Нажмите Enter для выхода..." 