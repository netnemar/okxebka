#!/bin/bash

# Скрипт быстрого запуска PyQt версии трейдера

echo "🚀 Запуск трейдера (PyQt интерфейс)..."
echo ""

# Проверяем, существует ли виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv .venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source .venv/bin/activate

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Проверяем конфиг файл
if [ ! -f "config.json" ]; then
    echo "⚠️  Файл config.json не найден!"
    echo "📝 Пожалуйста, настройте API ключи в config.json"
    exit 1
fi

# Проверяем, заполнены ли API ключи
if grep -q "YOUR_API_KEY_HERE" config.json; then
    echo "⚠️  API ключи не настроены!"
    echo "📝 Отредактируйте config.json и укажите ваши OKX API ключи"
    exit 1
fi

echo "✅ Все готово!"
echo ""
echo "🎯 Запуск PyQt интерфейса..."
python3 main_pyqt.py 