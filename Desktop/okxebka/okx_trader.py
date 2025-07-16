import json
import okx.Account as Account
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.PublicData as PublicData
from datetime import datetime
import time


class OKXTrader:
    def __init__(self, config_file="config.json"):
        """Инициализация трейдера с настройками из конфигурационного файла"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # API ключи
        self.api_key = self.config['okx']['api_key']
        self.secret_key = self.config['okx']['secret_key']
        self.passphrase = self.config['okx']['passphrase']
        
        # Флаг торговли: 0 - реальная торговля, 1 - демо
        self.flag = "0"  # Реальная торговля
        
        # Инициализация API клиентов
        self.account_api = Account.AccountAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag)
        self.trade_api = Trade.TradeAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag)
        self.market_api = MarketData.MarketAPI(flag=self.flag)
        self.public_api = PublicData.PublicAPI(flag=self.flag)
        
    def search_futures_pair(self, symbol):
        """Поиск фьючерсной пары по символу (например SOL -> SOL-USDT-SWAP)"""
        try:
            result = self.public_api.get_instruments(instType="SWAP")
            if result['code'] == '0':
                instruments = result['data']
                
                # Поиск подходящих пар
                found_pairs = []
                for inst in instruments:
                    inst_id = inst['instId']
                    if symbol.upper() in inst_id and 'USDT' in inst_id:
                        found_pairs.append({
                            'instId': inst_id,
                            'baseCcy': inst['ctVal'],
                            'quoteCcy': inst['quoteCcy'],
                            'tickSz': inst['tickSz'],
                            'lotSz': inst['lotSz']
                        })
                
                return found_pairs
            else:
                print(f"Ошибка при получении инструментов: {result}")
                return []
        except Exception as e:
            print(f"Ошибка поиска пары: {e}")
            return []
    
    def get_current_price(self, inst_id):
        """Получение текущей цены инструмента"""
        try:
            result = self.market_api.get_ticker(instId=inst_id)
            if result['code'] == '0' and result['data']:
                return float(result['data'][0]['last'])
            return None
        except Exception as e:
            print(f"Ошибка получения цены: {e}")
            return None
    
    def get_account_config(self):
        """Получение конфигурации аккаунта"""
        try:
            result = self.account_api.get_account_config()
            if result['code'] == '0':
                return result['data'][0]
            return None
        except Exception as e:
            print(f"Ошибка получения конфигурации: {e}")
            return None
    
    def set_position_mode(self, mode="net_mode"):
        """Установка режима позиций"""
        try:
            result = self.account_api.set_position_mode(posMode=mode)
            if result['code'] == '0':
                print(f"Режим позиций установлен: {mode}")
                return True
            else:
                print(f"Ошибка установки режима позиций: {result}")
                return False
        except Exception as e:
            print(f"Ошибка установки режима позиций: {e}")
            return False

    def set_leverage(self, inst_id, leverage, margin_mode="cross"):
        """Установка плеча для инструмента"""
        try:
            result = self.account_api.set_leverage(
                instId=inst_id,
                lever=str(leverage),
                mgnMode=margin_mode
            )
            if result['code'] == '0':
                print(f"Плечо {leverage}x установлено для {inst_id}")
                return True
            else:
                print(f"Ошибка установки плеча: {result}")
                return False
        except Exception as e:
            print(f"Ошибка установки плеча: {e}")
            return False
    
    def calculate_position_size(self, inst_id, usd_amount, leverage, current_price):
        """
        Расчет размера позиции в контрактах
        usd_amount - это МАРЖА в долларах (без учета плеча)
        leverage - плечо, которое умножает позицию
        """
        try:
            # Получаем информацию об инструменте
            result = self.public_api.get_instruments(instType="SWAP", instId=inst_id)
            print(f"Информация об инструменте: {result}")
            
            if result['code'] == '0' and result['data']:
                inst_info = result['data'][0]
                ct_val = float(inst_info['ctVal'])  # Размер контракта (обычно 1 для большинства пар)
                lot_sz = float(inst_info['lotSz'])  # Минимальный размер лота
                
                print(f"ctVal: {ct_val}, lotSz: {lot_sz}, цена: {current_price}")
                print(f"Маржа: ${usd_amount}, Плечо: {leverage}x")
                
                # usd_amount это маржа (собственные средства)
                # Полная стоимость позиции = маржа * плечо
                total_position_value = usd_amount * leverage
                
                # Для SWAP контрактов количество = полная стоимость / цена
                contracts = total_position_value / current_price
                
                # Округляем до минимального размера лота
                contracts = max(lot_sz, round(contracts / lot_sz) * lot_sz)
                
                print(f"Полная стоимость позиции: ${total_position_value:.2f}")
                print(f"Количество контрактов (базовая валюта): {contracts}")
                
                return str(contracts)
            else:
                print(f"Ошибка получения данных инструмента: {result}")
                return None
        except Exception as e:
            print(f"Ошибка расчета размера позиции: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def place_market_order(self, inst_id, side, size, leverage=None, margin_mode="cross"):
        """Размещение рыночного ордера"""
        try:
            # Установка плеча если указано
            if leverage:
                self.set_leverage(inst_id, leverage, margin_mode)
            
            # Получаем конфигурацию аккаунта для определения режима позиций
            config = self.get_account_config()
            print(f"Конфигурация аккаунта: {config}")
            
            # Определяем правильный posSide в зависимости от режима
            if config and 'posMode' in config:
                pos_mode = config['posMode']
                print(f"Режим позиций: {pos_mode}")
                
                if pos_mode == 'net_mode':
                    pos_side = "net"
                else:  # long_short_mode
                    pos_side = "long" if side == "buy" else "short"
            else:
                # По умолчанию пробуем net режим
                pos_side = "net"
                
            print(f"Используем posSide: {pos_side}")
            
            # Размещение ордера с правильным posSide
            result = self.trade_api.place_order(
                instId=inst_id,
                tdMode=margin_mode,
                side=side,
                posSide=pos_side,
                ordType="market",
                sz=size
            )
            
            # Если все еще ошибка posSide, пробуем переключить режим и повторить
            if result['code'] != '0' and 'posSide' in str(result):
                print("Ошибка posSide, пробуем переключить в net_mode...")
                if self.set_position_mode("net_mode"):
                    result = self.trade_api.place_order(
                        instId=inst_id,
                        tdMode=margin_mode,
                        side=side,
                        posSide="net",
                        ordType="market",
                        sz=size
                    )
            
            if result['code'] == '0':
                order_id = result['data'][0]['ordId']
                print(f"Ордер успешно размещен! ID: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'data': result['data'][0]
                }
            else:
                error_msg = result['data'][0]['sMsg'] if result['data'] else result['msg']
                print(f"Ошибка размещения ордера: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            print(f"Ошибка размещения ордера: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_positions(self):
        """Получение всех открытых позиций"""
        try:
            result = self.account_api.get_positions()
            if result['code'] == '0':
                positions = []
                for pos in result['data']:
                    if float(pos['pos']) != 0:  # Только открытые позиции
                        positions.append({
                            'instId': pos['instId'],
                            'posSide': pos['posSide'],
                            'pos': pos['pos'],
                            'avgPx': pos['avgPx'],
                            'upl': pos['upl'],
                            'uplRatio': pos['uplRatio'],
                            'notionalUsd': pos['notionalUsd'],
                            'lever': pos['lever'],
                            'markPx': pos['markPx']
                        })
                return positions
            else:
                print(f"Ошибка получения позиций: {result}")
                return []
        except Exception as e:
            print(f"Ошибка получения позиций: {e}")
            return []
    
    def get_account_balance(self):
        """Получение баланса аккаунта"""
        try:
            result = self.account_api.get_account_balance()
            if result['code'] == '0':
                return result['data'][0]
            return None
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return None
    
    def close_position(self, inst_id, size):
        """Закрытие позиции"""
        try:
            # Получаем текущие позиции
            positions = self.get_positions()
            current_position = None
            
            for pos in positions:
                if pos['instId'] == inst_id:
                    current_position = pos
                    break
            
            if not current_position:
                return {'success': False, 'error': 'Позиция не найдена'}
            
            # Получаем конфигурацию аккаунта для определения режима позиций
            config = self.get_account_config()
            print(f"Конфигурация аккаунта для закрытия: {config}")
            
            # Определяем сторону для закрытия
            current_pos = float(current_position['pos'])
            current_pos_side = current_position['posSide']
            
            # В зависимости от режима позиций определяем параметры
            if config and 'posMode' in config:
                pos_mode = config['posMode']
                print(f"Режим позиций: {pos_mode}")
                
                if pos_mode == 'net_mode':
                    # В net режиме противоположная сторона
                    side = "sell" if current_pos > 0 else "buy"
                    pos_side = "net"
                else:  # long_short_mode
                    # В long/short режиме закрываем используя противоположную сторону но тот же posSide
                    if current_pos_side == "long":
                        side = "sell"
                        pos_side = "long"
                    else:  # short
                        side = "buy"  
                        pos_side = "short"
            else:
                # По умолчанию net режим
                side = "sell" if current_pos > 0 else "buy"
                pos_side = "net"
                
            print(f"Закрываем позицию: side={side}, posSide={pos_side}, размер={abs(current_pos)}")
            
            # Закрываем позицию рыночным ордером
            result = self.trade_api.place_order(
                instId=inst_id,
                tdMode="cross",
                side=side,
                posSide=pos_side,
                ordType="market",
                sz=str(abs(current_pos))
            )
            
            if result['code'] == '0':
                print(f"Позиция успешно закрыта! ID ордера: {result['data'][0]['ordId']}")
                return {
                    'success': True,
                    'order_id': result['data'][0]['ordId']
                }
            else:
                error_msg = result['data'][0]['sMsg'] if result['data'] else result['msg']
                print(f"Ошибка закрытия позиции: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            print(f"Ошибка закрытия позиции: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_all_positions(self):
        """Закрытие всех открытых позиций"""
        try:
            positions = self.get_positions()
            if not positions:
                return {'success': True, 'message': 'Нет открытых позиций'}
            
            results = []
            for position in positions:
                inst_id = position['instId']
                result = self.close_position(inst_id, None)
                results.append({
                    'instId': inst_id,
                    'success': result['success'],
                    'error': result.get('error', '')
                })
                
            # Проверяем результаты
            all_success = all(r['success'] for r in results)
            return {
                'success': all_success,
                'results': results,
                'message': f'Закрыто позиций: {sum(1 for r in results if r["success"])}/{len(results)}'
            }
            
        except Exception as e:
            print(f"Ошибка закрытия всех позиций: {e}")
            return {'success': False, 'error': str(e)}


# Вспомогательные функции
def format_currency(amount):
    """Форматирование валютных сумм"""
    try:
        return f"${float(amount):,.2f}"
    except:
        return "$0.00"

def format_percentage(percentage):
    """Форматирование процентов"""
    try:
        pct = float(percentage) * 100
        color = "green" if pct >= 0 else "red"
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.2f}%", color
    except:
        return "0.00%", "black" 