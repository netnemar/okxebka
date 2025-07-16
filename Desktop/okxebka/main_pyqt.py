import sys
import threading
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLineEdit, 
                             QListWidget, QTableWidget, QTableWidgetItem, 
                             QTextEdit, QLabel, QButtonGroup, QFrame, QSplitter,
                             QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
from okx_trader import OKXTrader, format_currency, format_percentage


class PnLUpdateWorker(QObject):
    """Воркер для обновления PnL в отдельном потоке"""
    update_signal = pyqtSignal(list, float, float)
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, trader):
        super().__init__()
        self.trader = trader
        self.running = True
        
    def run(self):
        while self.running:
            try:
                positions = self.trader.get_positions()
                total_pnl = sum(float(pos.get('upl', 0)) for pos in positions)
                total_pnl_percentage = 0
                
                if positions:
                    total_margin = sum(float(pos.get('margin', 0)) for pos in positions)
                    if total_margin > 0:
                        total_pnl_percentage = (total_pnl / total_margin) * 100
                
                self.update_signal.emit(positions, total_pnl, total_pnl_percentage)
            except Exception as e:
                self.log_signal.emit(f"Ошибка обновления PnL: {e}", "ERROR")
                
            time.sleep(2)
    
    def stop(self):
        self.running = False


class TradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трейдер")
        self.setGeometry(100, 100, 1400, 900)
        
        # Инициализация трейдера
        try:
            self.trader = OKXTrader()
            self.connected = True
        except Exception as e:
            self.log_message(f"Ошибка подключения: {e}", "ERROR")
            self.connected = False
        
        # Переменные
        self.selected_pair = None
        self.pairs_data = []
        self.logs = []
        
        # Настройка темной темы
        self.setup_theme()
        
        # Настройка UI
        self.setup_ui()
        
        # Запуск обновления PnL
        if self.connected:
            self.setup_pnl_worker()
        
        self.log_message("Добро пожаловать в трейдер", "INFO")
    
    def setup_theme(self):
        """Настройка минималистичной черно-белой темы"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(15, 15, 15))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        
        self.setPalette(palette)
        
        # Стили для виджетов
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f0f;
                color: white;
            }
            QWidget {
                background-color: #0f0f0f;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 500;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #555;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
            QPushButton.buy {
                background-color: #1e3a2e;
                border: 1px solid #2d5a3d;
                color: #4caf50;
            }
            QPushButton.buy:hover {
                background-color: #2d5a3d;
                color: white;
            }
            QPushButton.sell {
                background-color: #3a1e1e;
                border: 1px solid #5a2d2d;
                color: #f44336;
            }
            QPushButton.sell:hover {
                background-color: #5a2d2d;
                color: white;
            }
            QPushButton.preset {
                padding: 8px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QTableWidget {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                gridline-color: #333;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3a3a3a;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: white;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #ccc;
            }
            QLabel {
                color: #ccc;
            }
            QLabel.header {
                font-size: 14px;
                font-weight: 600;
                color: white;
                margin: 5px 0;
            }
            QLabel.pnl {
                font-size: 16px;
                font-weight: 700;
                padding: 8px;
                border-radius: 6px;
                background-color: #1a1a1a;
            }
            QFrame.separator {
                background-color: #333;
                max-height: 1px;
                margin: 10px 0;
            }
        """)
    
    def setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Левая панель - торговля
        left_widget = QWidget()
        left_widget.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        
        self.setup_search_panel(left_layout)
        self.setup_presets_panel(left_layout)
        self.setup_trading_panel(left_layout)
        
        # Правая панель - позиции и логи
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        self.setup_positions_panel(right_layout)
        self.setup_logs_panel(right_layout)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 1000])
        splitter.setChildrenCollapsible(False)
        
        main_layout.addWidget(splitter)
    
    def setup_search_panel(self, layout):
        """Панель поиска пар"""
        # Заголовок
        header = QLabel("Поиск пары")
        header.setProperty("class", "header")
        layout.addWidget(header)
        
        # Поиск
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите символ (например: SOL)")
        self.search_input.returnPressed.connect(self.search_pairs)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍")
        search_btn.setMaximumWidth(50)
        search_btn.clicked.connect(self.search_pairs)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Результаты поиска
        self.pairs_list = QListWidget()
        self.pairs_list.setMaximumHeight(150)
        self.pairs_list.itemClicked.connect(self.select_pair)
        layout.addWidget(self.pairs_list)
        
        # Выбранная пара
        self.selected_pair_label = QLabel("Пара не выбрана")
        self.selected_pair_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.selected_pair_label)
        
        # Разделитель
        separator = QFrame()
        separator.setProperty("class", "separator")
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
    
    def setup_presets_panel(self, layout):
        """Панель быстрых пресетов"""
        header = QLabel("Быстрый вход")
        header.setProperty("class", "header")
        layout.addWidget(header)
        
        presets_layout = QGridLayout()
        presets_layout.setSpacing(8)
        
        # Пресеты
        presets = [
            ("300", 300, 10),
            ("500", 500, 10), 
            ("1500", 1500, 10)
        ]
        
        for i, (label, amount, leverage) in enumerate(presets):
            # LONG кнопка
            long_btn = QPushButton(f"↗ {label}")
            long_btn.setProperty("class", "buy preset")
            long_btn.clicked.connect(lambda checked, a=amount, l=leverage: self.place_preset_order("buy", a, l))
            presets_layout.addWidget(long_btn, 0, i)
            
            # SHORT кнопка  
            short_btn = QPushButton(f"↘ {label}")
            short_btn.setProperty("class", "sell preset")
            short_btn.clicked.connect(lambda checked, a=amount, l=leverage: self.place_preset_order("sell", a, l))
            presets_layout.addWidget(short_btn, 1, i)
        
        layout.addLayout(presets_layout)
        
        # Разделитель
        separator = QFrame()
        separator.setProperty("class", "separator")
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
    
    def setup_trading_panel(self, layout):
        """Панель ручной торговли"""
        header = QLabel("Ручная торговля")
        header.setProperty("class", "header")
        layout.addWidget(header)
        
        # Маржа
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Маржа (USD):"))
        self.margin_input = QLineEdit("100")
        margin_layout.addWidget(self.margin_input)
        layout.addLayout(margin_layout)
        
        # Плечо
        leverage_layout = QHBoxLayout()
        leverage_layout.addWidget(QLabel("Плечо:"))
        
        self.leverage_group = QButtonGroup()
        leverages = [5, 10, 20, 50, 100]
        leverage_buttons_layout = QHBoxLayout()
        
        for i, lev in enumerate(leverages):
            btn = QPushButton(f"{lev}x")
            btn.setCheckable(True)
            if lev == 10:  # По умолчанию 10x
                btn.setChecked(True)
            self.leverage_group.addButton(btn, lev)
            leverage_buttons_layout.addWidget(btn)
        
        layout.addLayout(leverage_layout)
        layout.addLayout(leverage_buttons_layout)
        
        # Кнопки торговли
        trading_layout = QHBoxLayout()
        trading_layout.setSpacing(10)
        
        long_btn = QPushButton("LONG")
        long_btn.setProperty("class", "buy")
        long_btn.setMinimumHeight(50)
        long_btn.clicked.connect(lambda: self.place_order("buy"))
        trading_layout.addWidget(long_btn)
        
        short_btn = QPushButton("SHORT")
        short_btn.setProperty("class", "sell")
        short_btn.setMinimumHeight(50)
        short_btn.clicked.connect(lambda: self.place_order("sell"))
        trading_layout.addWidget(short_btn)
        
        layout.addLayout(trading_layout)
        
        # Растягиваем оставшееся пространство
        layout.addStretch()
    
    def setup_positions_panel(self, layout):
        """Панель позиций"""
        header_layout = QHBoxLayout()
        header = QLabel("Активные позиции")
        header.setProperty("class", "header")
        header_layout.addWidget(header)
        
        # Общий PnL
        self.total_pnl_label = QLabel("PnL: $0.00")
        self.total_pnl_label.setProperty("class", "pnl")
        self.total_pnl_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.total_pnl_label)
        
        layout.addLayout(header_layout)
        
        # Таблица позиций
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            "Пара", "Сторона", "Размер", "Входная цена", "Текущая цена", "PnL", "PnL%"
        ])
        
        # Настройка таблицы
        header = self.positions_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.positions_table)
        
        # Кнопка закрытия всех позиций
        close_all_btn = QPushButton("Закрыть все позиции")
        close_all_btn.clicked.connect(self.close_all_positions)
        layout.addWidget(close_all_btn)
    
    def setup_logs_panel(self, layout):
        """Панель логов"""
        header_layout = QHBoxLayout()
        header = QLabel("Логи")
        header.setProperty("class", "header")
        header_layout.addWidget(header)
        
        clear_btn = QPushButton("Очистить")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Текстовое поле логов
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
    def setup_pnl_worker(self):
        """Настройка воркера для обновления PnL"""
        self.pnl_thread = QThread()
        self.pnl_worker = PnLUpdateWorker(self.trader)
        self.pnl_worker.moveToThread(self.pnl_thread)
        
        # Подключение сигналов
        self.pnl_thread.started.connect(self.pnl_worker.run)
        self.pnl_worker.update_signal.connect(self.update_positions)
        self.pnl_worker.log_signal.connect(self.log_message)
        
        self.pnl_thread.start()
    
    def search_pairs(self):
        """Поиск торговых пар"""
        query = self.search_input.text().strip().upper()
        if not query:
            return
        
        self.log_message(f"Поиск пар: {query}", "INFO")
        
        try:
            # Получаем все пары через API
            instruments = self.trader.trading_api.get_instruments(instType="SWAP")
            
            if instruments['code'] != '0':
                self.log_message("Ошибка получения инструментов", "ERROR")
                return
            
            # Фильтруем пары по запросу
            self.pairs_data = []
            self.pairs_list.clear()
            
            for instrument in instruments['data']:
                inst_id = instrument['instId']
                if query in inst_id:
                    self.pairs_data.append(instrument)
                    self.pairs_list.addItem(inst_id)
            
            self.log_message(f"Найдено {len(self.pairs_data)} пар", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Ошибка поиска: {e}", "ERROR")
    
    def select_pair(self, item):
        """Выбор торговой пары"""
        selected_text = item.text()
        
        # Находим данные выбранной пары
        for pair_data in self.pairs_data:
            if pair_data['instId'] == selected_text:
                self.selected_pair = pair_data
                break
        
        if self.selected_pair:
            # Получаем текущую цену
            try:
                ticker = self.trader.public_api.get_tickers(instType="SWAP", instId=selected_text)
                if ticker['code'] == '0' and ticker['data']:
                    price = float(ticker['data'][0]['last'])
                    self.selected_pair_label.setText(f"✓ {selected_text} | Цена: ${price:.4f}")
                    self.selected_pair_label.setStyleSheet("color: #4caf50; font-weight: 600;")
                    self.log_message(f"Выбрана пара: {selected_text}", "INFO")
                    self.log_message(f"Цена {selected_text}: ${price:.4f}", "INFO")
            except Exception as e:
                self.selected_pair_label.setText(f"✓ {selected_text}")
                self.log_message(f"Ошибка получения цены: {e}", "WARNING")
    
    def place_preset_order(self, side, amount, leverage):
        """Размещение ордера через пресет"""
        if not self.selected_pair:
            self.log_message("Выберите торговую пару", "WARNING")
            return
        
        self.log_message(f"ПРЕСЕТ {side.upper()}: {self.selected_pair['instId']}, маржа ${amount}, плечо {leverage}x", "INFO")
        
        try:
            # Устанавливаем плечо
            self.trader.set_leverage(self.selected_pair['instId'], leverage)
            
            # Размещаем ордер
            result = self.trader.place_market_order(
                inst_id=self.selected_pair['instId'],
                side=side,
                margin_usd=amount,
                leverage=leverage
            )
            
            if result:
                self.log_message(f"ПРЕСЕТ {side.upper()} размещен! ID: {result}", "SUCCESS")
                # Обновляем поля
                self.margin_input.setText(str(amount))
                # Устанавливаем плечо в группе кнопок
                for btn in self.leverage_group.buttons():
                    if self.leverage_group.id(btn) == leverage:
                        btn.setChecked(True)
                        break
            else:
                self.log_message(f"Ошибка размещения пресета {side.upper()}", "ERROR")
                
        except Exception as e:
            self.log_message(f"Ошибка пресета: {e}", "ERROR")
    
    def place_order(self, side):
        """Размещение ордера"""
        if not self.selected_pair:
            self.log_message("Выберите торговую пару", "WARNING")
            return
        
        try:
            margin = float(self.margin_input.text())
        except ValueError:
            self.log_message("Введите корректную маржу", "WARNING")
            return
        
        # Получаем выбранное плечо
        selected_leverage = None
        for btn in self.leverage_group.buttons():
            if btn.isChecked():
                selected_leverage = self.leverage_group.id(btn)
                break
        
        if not selected_leverage:
            self.log_message("Выберите плечо", "WARNING")
            return
        
        self.log_message(f"{side.upper()}: {self.selected_pair['instId']}, маржа ${margin}, плечо {selected_leverage}x", "INFO")
        
        try:
            # Устанавливаем плечо
            self.trader.set_leverage(self.selected_pair['instId'], selected_leverage)
            
            # Размещаем ордер
            result = self.trader.place_market_order(
                inst_id=self.selected_pair['instId'],
                side=side,
                margin_usd=margin,
                leverage=selected_leverage
            )
            
            if result:
                self.log_message(f"Ордер {side.upper()} размещен! ID: {result}", "SUCCESS")
            else:
                self.log_message(f"Ошибка размещения ордера {side.upper()}", "ERROR")
                
        except Exception as e:
            self.log_message(f"Ошибка ордера: {e}", "ERROR")
    
    def update_positions(self, positions, total_pnl, total_pnl_percentage):
        """Обновление таблицы позиций"""
        self.positions_table.setRowCount(len(positions))
        
        for i, pos in enumerate(positions):
            inst_id = pos.get('instId', '')
            side = "LONG" if float(pos.get('pos', 0)) > 0 else "SHORT"
            size = abs(float(pos.get('pos', 0)))
            avg_px = float(pos.get('avgPx', 0))
            mark_px = float(pos.get('markPx', 0))
            upl = float(pos.get('upl', 0))
            upl_ratio = float(pos.get('uplRatio', 0)) * 100
            
            # Заполняем строку
            self.positions_table.setItem(i, 0, QTableWidgetItem(inst_id))
            self.positions_table.setItem(i, 1, QTableWidgetItem(side))
            self.positions_table.setItem(i, 2, QTableWidgetItem(f"{size:.4f}"))
            self.positions_table.setItem(i, 3, QTableWidgetItem(f"${avg_px:.4f}"))
            self.positions_table.setItem(i, 4, QTableWidgetItem(f"${mark_px:.4f}"))
            
            # PnL с цветом
            pnl_item = QTableWidgetItem(format_currency(upl))
            pnl_item.setForeground(QColor("#4caf50" if upl >= 0 else "#f44336"))
            self.positions_table.setItem(i, 5, pnl_item)
            
            pnl_percent_item = QTableWidgetItem(format_percentage(upl_ratio))
            pnl_percent_item.setForeground(QColor("#4caf50" if upl_ratio >= 0 else "#f44336"))
            self.positions_table.setItem(i, 6, pnl_percent_item)
        
        # Обновляем общий PnL
        color = "#4caf50" if total_pnl >= 0 else "#f44336"
        pnl_text = f"PnL: {format_currency(total_pnl)} ({format_percentage(total_pnl_percentage)})"
        self.total_pnl_label.setText(pnl_text)
        self.total_pnl_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 16px; padding: 8px; border-radius: 6px; background-color: #1a1a1a;")
    
    def close_all_positions(self):
        """Закрытие всех позиций"""
        try:
            closed_count = self.trader.close_all_positions()
            if closed_count > 0:
                self.log_message(f"Закрыто позиций: {closed_count}", "SUCCESS")
            else:
                self.log_message("Нет позиций для закрытия", "INFO")
        except Exception as e:
            self.log_message(f"Ошибка закрытия позиций: {e}", "ERROR")
    
    def log_message(self, message, level="INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        
        # Ограничиваем количество логов
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        # Обновляем текстовое поле
        self.log_text.setPlainText("\n".join(self.logs))
        
        # Прокручиваем вниз
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_logs(self):
        """Очистка логов"""
        self.logs = []
        self.log_text.clear()
    
    def closeEvent(self, event):
        """Обработка закрытия приложения"""
        if hasattr(self, 'pnl_worker'):
            self.pnl_worker.stop()
        if hasattr(self, 'pnl_thread'):
            self.pnl_thread.quit()
            self.pnl_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Трейдер")
    
    # Установка темной темы для всего приложения
    app.setStyle('Fusion')
    
    window = TradingApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 