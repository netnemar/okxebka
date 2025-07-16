#!/usr/bin/env python3
"""
Скрипт для тестирования соединения с OKX API
Запустите этот файл, чтобы убедиться, что API работает корректно
"""

from okx_trader import OKXTrader
import json


def test_connection():
    """Тестирование соединения с OKX API"""
    print("🔄 Тестирование соединения с OKX API...")
    
    try:
        # Инициализация трейдера
        trader = OKXTrader()
        print("✅ Трейдер инициализирован успешно")
        
        # Тест 1: Получение баланса аккаунта
        print("\n📊 Тест 1: Получение баланса аккаунта")
        balance = trader.get_account_balance()
        if balance:
            print(f"✅ Баланс получен успешно")
            print(f"   Общий баланс: {balance.get('totalEq', 'N/A')} USDT")
            print(f"   Доступные средства: {balance.get('availEq', 'N/A')} USDT")
        else:
            print("❌ Не удалось получить баланс")
            return False
            
        # Тест 1.1: Проверка конфигурации аккаунта
        print("\n⚙️ Тест 1.1: Конфигурация аккаунта")
        config = trader.get_account_config()
        if config:
            print(f"✅ Конфигурация получена")
            print(f"   Уровень аккаунта: {config.get('acctLv', 'N/A')}")
            print(f"   Режим позиций: {config.get('posMode', 'N/A')}")
            print(f"   Автоматическое занятие: {config.get('autoLoan', 'N/A')}")
        else:
            print("❌ Не удалось получить конфигурацию")
            return False
            
        # Тест 2: Поиск торговых пар
        print("\n🔍 Тест 2: Поиск торговых пар")
        pairs = trader.search_futures_pair("BTC")
        if pairs:
            print(f"✅ Найдено {len(pairs)} BTC пар")
            for pair in pairs[:3]:  # Показываем первые 3
                print(f"   - {pair['instId']}")
        else:
            print("❌ Не удалось найти торговые пары")
            return False
            
        # Тест 3: Получение цены
        print("\n💰 Тест 3: Получение текущей цены")
        if pairs:
            test_pair = pairs[0]['instId']
            price = trader.get_current_price(test_pair)
            if price:
                print(f"✅ Цена {test_pair}: ${price:,.2f}")
            else:
                print(f"❌ Не удалось получить цену для {test_pair}")
                return False
        
        # Тест 4: Получение позиций
        print("\n📈 Тест 4: Получение открытых позиций")
        positions = trader.get_positions()
        print(f"✅ Позиций найдено: {len(positions)}")
        if positions:
            for pos in positions:
                print(f"   - {pos['instId']}: {pos['pos']} (PnL: ${float(pos['upl']):.2f})")
        else:
            print("   Открытых позиций нет")
            
        print("\n🎉 Все тесты пройдены успешно!")
        print("🚀 Можете запускать основное приложение: python main.py")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Проверьте правильность API ключей в config.json")
        print("2. Убедитесь, что API ключи имеют права на торговлю")
        print("3. Проверьте интернет-соединение")
        print("4. Убедитесь, что IP-адрес не заблокирован в настройках OKX")
        return False


def print_config_info():
    """Вывод информации о конфигурации"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        print("⚙️ Текущая конфигурация:")
        print(f"   API Key: {config['okx']['api_key'][:10]}...")
        print(f"   Режим: {'Реальная торговля' if config['okx'].get('sandbox', True) == False else 'Демо торговля'}")
        print(f"   Плечо по умолчанию: {config.get('default_leverage', 'не задано')}")
        
    except Exception as e:
        print(f"⚠️ Не удалось прочитать конфигурацию: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 ТЕСТИРОВАНИЕ СОЕДИНЕНИЯ OKX API")
    print("=" * 50)
    
    print_config_info()
    print()
    
    success = test_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
    print("=" * 50) 