@echo off
echo ==========================================
echo       OKX Futures Trader
echo ==========================================
echo.

REM Проверка установки Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен!
    echo Скачайте Python с https://python.org
    pause
    exit /b 1
)

REM Создание виртуального окружения если его нет
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call .venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt

echo.
echo Проверка соединения с OKX API...
python test_connection.py

echo.
echo Запуск приложения...
python main.py

echo.
echo Приложение закрыто.
pause 