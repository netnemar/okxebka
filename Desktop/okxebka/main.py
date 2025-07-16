import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from okx_trader import OKXTrader, format_currency, format_percentage


class OKXTradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OKX Фьючерс Трейдер Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0e1a')
        
        # Инициализация трейдера
        try:
            self.trader = OKXTrader()
            self.connected = True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к OKX API: {e}")
            self.connected = False
            return
        
        # Переменные
        self.selected_pair = None
        self.current_positions = []
        self.pnl_update_thread = None
        self.stop_pnl_updates = False
        self.logs = []  # Хранение логов
        
        self.setup_ui()
        self.start_pnl_updates()
        
    def log_message(self, message, level="INFO"):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        
        # Ограничиваем количество логов (последние 100)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
            
        # Обновляем виджет логов если он существует
        if hasattr(self, 'log_text'):
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "\n".join(self.logs))
            self.log_text.see(tk.END)
            
    def setup_logs_panel(self, parent):
        """Настройка панели логов"""
        # Заголовок
        header = tk.Label(parent, text="📋 Логи торговли", bg='#1a1f2e', fg='#64b5f6', 
                         font=('Arial', 12, 'bold'))
        header.pack(pady=(0, 10))
        
        # Текстовое поле для логов
        log_frame = tk.Frame(parent, bg='#1a1f2e')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            height=8,
            bg='#0d1421', 
            fg='#e0e0e0',
            insertbackground='white',
            font=('Consolas', 9),
            relief=tk.FLAT,
            borderwidth=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Кнопка очистки логов
        clear_btn = tk.Button(parent, text="🗑️ Очистить", command=self.clear_logs,
                             bg='#b0bec5', fg='black', font=('Arial', 9),
                             relief=tk.FLAT, bd=0, padx=10, pady=5)
        clear_btn.pack(pady=(5, 0))
        
        # Добавляем приветственное сообщение
        self.log_message("Добро пожаловать в OKX Трейдер Pro!", "INFO")
        
    def clear_logs(self):
        """Очистка логов"""
        self.logs = []
        if hasattr(self, 'log_text'):
            self.log_text.delete(1.0, tk.END)
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Современные стили
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), background='#0a0e1a', foreground='#64b5f6')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), background='#1a1f2e', foreground='#81c784')
        style.configure('Info.TLabel', font=('Arial', 10), background='#1a1f2e', foreground='#b0bec5')
        
        # Стильный заголовок с градиентом
        title_frame = tk.Frame(self.root, bg='#0a0e1a', height=60)
        title_frame.pack(fill=tk.X, pady=(10, 20))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🚀 OKX Фьючерс Трейдер Pro", 
                              bg='#0a0e1a', fg='#64b5f6',
                              font=('Arial', 20, 'bold'))
        title_label.pack(expand=True)
        
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='#0a0e1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель - торговля
        left_frame = tk.Frame(main_frame, bg='#1a1f2e', relief=tk.RAISED, bd=1, highlightbackground='#3a4a5e', highlightthickness=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10), ipadx=10, ipady=10)
        left_frame.configure(width=400)  # Фиксированная ширина
        
        # Правая панель (вертикальная компоновка)
        right_container = tk.Frame(main_frame, bg='#0a0e1a')
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Правая верхняя панель - позиции
        right_upper_frame = tk.Frame(right_container, bg='#1a1f2e', relief=tk.RAISED, bd=1, highlightbackground='#3a4a5e', highlightthickness=1)
        right_upper_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5), ipadx=10, ipady=10)
        
        # Правая нижняя панель - логи
        right_lower_frame = tk.Frame(right_container, bg='#1a1f2e', relief=tk.RAISED, bd=1, highlightbackground='#3a4a5e', highlightthickness=1)
        right_lower_frame.pack(fill=tk.BOTH, expand=False, ipadx=10, ipady=10)
        right_lower_frame.configure(height=200)  # Фиксированная высота для логов
        
        self.setup_trading_panel(left_frame)
        self.setup_positions_panel(right_upper_frame)
        self.setup_logs_panel(right_lower_frame)
        
    def setup_trading_panel(self, parent):
        """Настройка панели торговли"""
        # Стильный заголовок
        header = tk.Label(parent, text="⚡ Быстрая торговля", bg='#1a1f2e', fg='#81c784', 
                         font=('Arial', 14, 'bold'))
        header.pack(pady=(0, 15))
        
        # Поиск пары
        search_frame = tk.Frame(parent, bg='#1a1f2e')
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Поиск пары:", bg='#1a1f2e', fg='#b0bec5', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        search_entry_frame = tk.Frame(search_frame, bg='#1a1f2e')
        search_entry_frame.pack(fill=tk.X, pady=5)
        
        self.search_entry = tk.Entry(search_entry_frame, font=('Arial', 12), width=20, 
                                    bg='#2a3441', fg='white', insertbackground='#64b5f6',
                                    relief=tk.FLAT, bd=0, highlightbackground='#3a4a5e', highlightthickness=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=8)
        self.search_entry.bind('<Return>', lambda e: self.search_pairs())
        
        search_btn = tk.Button(search_entry_frame, text="🔍", command=self.search_pairs, 
                              bg='#64b5f6', fg='black', font=('Arial', 10, 'bold'),
                              relief=tk.FLAT, bd=0, padx=15, pady=8,
                              cursor='hand2')
        search_btn.pack(side=tk.RIGHT)
        
        # Результаты поиска
        self.pairs_listbox = tk.Listbox(search_frame, height=6, font=('Arial', 10), 
                                       bg='#2a3441', fg='#e0e0e0', selectbackground='#64b5f6',
                                       relief=tk.FLAT, bd=0, highlightbackground='#3a4a5e', highlightthickness=1)
        self.pairs_listbox.pack(fill=tk.X, pady=5, ipady=5)
        self.pairs_listbox.bind('<<ListboxSelect>>', self.on_pair_select)
        
        # Информация о выбранной паре
        self.pair_info_label = tk.Label(parent, text="➤ Выберите торговую пару", 
                                       bg='#1a1f2e', fg='#ffcc02', font=('Arial', 11, 'bold'))
        self.pair_info_label.pack(pady=10)
        
        # Быстрые пресеты
        presets_frame = tk.Frame(parent, bg='#1a1f2e')
        presets_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        tk.Label(presets_frame, text="⚡ Быстрый вход:", bg='#1a1f2e', fg='#b0bec5', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        presets_buttons_frame = tk.Frame(presets_frame, bg='#1a1f2e')
        presets_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Пресет 1: 300 USD 10x
        preset1_frame = tk.Frame(presets_buttons_frame, bg='#1a1f2e')
        preset1_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        long_btn_300 = tk.Button(preset1_frame, text="📈 300$", command=lambda: self.place_preset_order("buy", 300, 10),
                                bg='#00c853', fg='black', font=('Arial', 10, 'bold'), 
                                relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        long_btn_300.pack(fill=tk.X, pady=(0, 2))
        
        short_btn_300 = tk.Button(preset1_frame, text="📉 300$", command=lambda: self.place_preset_order("sell", 300, 10),
                                 bg='#d32f2f', fg='black', font=('Arial', 10, 'bold'), 
                                 relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        short_btn_300.pack(fill=tk.X)
        
        # Пресет 2: 500 USD 10x
        preset2_frame = tk.Frame(presets_buttons_frame, bg='#1a1f2e')
        preset2_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        long_btn_500 = tk.Button(preset2_frame, text="📈 500$", command=lambda: self.place_preset_order("buy", 500, 10),
                                bg='#00c853', fg='black', font=('Arial', 10, 'bold'), 
                                relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        long_btn_500.pack(fill=tk.X, pady=(0, 2))
        
        short_btn_500 = tk.Button(preset2_frame, text="📉 500$", command=lambda: self.place_preset_order("sell", 500, 10),
                                 bg='#d32f2f', fg='black', font=('Arial', 10, 'bold'), 
                                 relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        short_btn_500.pack(fill=tk.X)
        
        # Пресет 3: 1500 USD 10x
        preset3_frame = tk.Frame(presets_buttons_frame, bg='#1a1f2e')
        preset3_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))
        
        long_btn_1500 = tk.Button(preset3_frame, text="📈 1500$", command=lambda: self.place_preset_order("buy", 1500, 10),
                                 bg='#00c853', fg='black', font=('Arial', 10, 'bold'), 
                                 relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        long_btn_1500.pack(fill=tk.X, pady=(0, 2))
        
        short_btn_1500 = tk.Button(preset3_frame, text="📉 1500$", command=lambda: self.place_preset_order("sell", 1500, 10),
                                  bg='#d32f2f', fg='black', font=('Arial', 10, 'bold'), 
                                  relief=tk.FLAT, bd=0, cursor='hand2', pady=6)
        short_btn_1500.pack(fill=tk.X)
        
        # Параметры торговли
        params_frame = tk.Frame(parent, bg='#1a1f2e')
        params_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Маржа в USD
        tk.Label(params_frame, text="💰 Маржа (USD):", bg='#1a1f2e', fg='#b0bec5', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.amount_entry = tk.Entry(params_frame, font=('Arial', 12, 'bold'), 
                                   bg='#2a3441', fg='white', insertbackground='#64b5f6',
                                   relief=tk.FLAT, bd=0, highlightbackground='#3a4a5e', highlightthickness=1)
        self.amount_entry.pack(fill=tk.X, pady=(5, 15), ipady=8)
        self.amount_entry.insert(0, "100")
        
        # Плечо
        tk.Label(params_frame, text="⚡ Плечо:", bg='#1a1f2e', fg='#b0bec5', font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.leverage_var = tk.StringVar(value="10")
        leverage_frame = tk.Frame(params_frame, bg='#1a1f2e')
        leverage_frame.pack(fill=tk.X, pady=(0, 15))
        
        for lev in ["5", "10", "20", "50", "100"]:
            tk.Radiobutton(leverage_frame, text=f"{lev}x", variable=self.leverage_var, value=lev,
                          bg='#1a1f2e', fg='#e0e0e0', selectcolor='#64b5f6', activebackground='#2a3441',
                          activeforeground='white', font=('Arial', 10, 'bold'), cursor='hand2',
                          relief=tk.FLAT, bd=0).pack(side=tk.LEFT, padx=8)
        
        # Стильные торговые кнопки
        buttons_frame = tk.Frame(params_frame, bg='#1a1f2e')
        buttons_frame.pack(fill=tk.X, pady=15)
        
        self.long_btn = tk.Button(buttons_frame, text="📈 LONG", command=lambda: self.place_order("buy"),
                                 bg='#00c853', fg='black', font=('Arial', 13, 'bold'), 
                                 relief=tk.FLAT, bd=0, cursor='hand2', pady=12,
                                 activebackground='#4caf50')
        self.long_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        self.short_btn = tk.Button(buttons_frame, text="📉 SHORT", command=lambda: self.place_order("sell"),
                                  bg='#d32f2f', fg='black', font=('Arial', 13, 'bold'), 
                                  relief=tk.FLAT, bd=0, cursor='hand2', pady=12,
                                  activebackground='#f44336')
        self.short_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))
        
    def setup_positions_panel(self, parent):
        """Настройка панели позиций"""
        # Стильный заголовок
        header = tk.Label(parent, text="📊 Активные позиции", bg='#1a1f2e', fg='#81c784', 
                         font=('Arial', 14, 'bold'))
        header.pack(pady=(0, 15))
        
        # Общий PnL с современным дизайном
        pnl_frame = tk.Frame(parent, bg='#2a3441', relief=tk.FLAT, bd=0)
        pnl_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.total_pnl_label = tk.Label(pnl_frame, text="💰 Общий PnL: $0.00 (0.00%)", 
                                       bg='#2a3441', fg='#ffcc02', font=('Arial', 12, 'bold'))
        self.total_pnl_label.pack(pady=8)
        
        # Таблица позиций
        positions_frame = tk.Frame(parent, bg='#1a1f2e')
        positions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создание Treeview для позиций
        columns = ('Пара', 'Сторона', 'Размер', 'Цена входа', 'Текущая цена', 'PnL', 'PnL%')
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=10)
        
        # Настройка заголовков
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100, anchor=tk.CENTER)
        
        # Scrollbar для таблицы
        scrollbar = ttk.Scrollbar(positions_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Стильная кнопка закрытия всех позиций
        close_all_btn = tk.Button(parent, text="🚫 Закрыть все позиции", 
                                 command=self.close_all_positions,
                                 bg='#ff7043', fg='black', font=('Arial', 11, 'bold'),
                                 relief=tk.FLAT, bd=0, cursor='hand2', pady=8,
                                 activebackground='#ff5722')
        close_all_btn.pack(pady=15, padx=10, fill=tk.X)
        
        # Контекстное меню для позиций
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Закрыть позицию", command=self.close_selected_position)
        self.positions_tree.bind("<Button-3>", self.show_context_menu)
        

    def search_pairs(self):
        """Поиск торговых пар"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.log_message("⚠️ Введите символ для поиска", "WARNING")
            return
            
        try:
            self.log_message(f"🔍 Поиск пар по запросу: {search_term}")
            pairs = self.trader.search_futures_pair(search_term)
            
            # Очистка списка
            self.pairs_listbox.delete(0, tk.END)
            
            # Добавление найденных пар
            for pair in pairs:
                self.pairs_listbox.insert(tk.END, pair['instId'])
                
            if not pairs:
                self.pairs_listbox.insert(tk.END, "Пары не найдены")
                self.log_message(f"❌ Пары не найдены для '{search_term}'", "WARNING")
            else:
                self.log_message(f"✅ Найдено {len(pairs)} пар", "SUCCESS")
                
        except Exception as e:
            self.log_message(f"❌ Ошибка поиска: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
            
    def on_pair_select(self, event):
        """Обработка выбора пары"""
        selection = self.pairs_listbox.curselection()
        if selection:
            selected_pair = self.pairs_listbox.get(selection[0])
            if selected_pair != "Пары не найдены":
                self.selected_pair = selected_pair
                self.log_message(f"📍 Выбрана пара: {selected_pair}")
                
                # Получение текущей цены
                current_price = self.trader.get_current_price(selected_pair)
                if current_price:
                    self.pair_info_label.config(
                        text=f"✅ {selected_pair} | Цена: ${current_price:,.4f}",
                        fg='#4CAF50'
                    )
                    self.log_message(f"💰 Цена {selected_pair}: ${current_price:,.4f}")
                else:
                    self.pair_info_label.config(
                        text=f"⚠️ {selected_pair} | Цена: не доступна",
                        fg='#ffcc02'
                    )
                    self.log_message(f"⚠️ Не удалось получить цену для {selected_pair}", "WARNING")
                    
    def place_order(self, side):
        """Размещение ордера"""
        if not self.selected_pair:
            messagebox.showwarning("Предупреждение", "Выберите торговую пару")
            return
            
        try:
            amount = float(self.amount_entry.get())
            leverage = int(self.leverage_var.get())
            
            if amount <= 0:
                messagebox.showwarning("Предупреждение", "Введите корректную сумму")
                return
                
            # Получение текущей цены
            current_price = self.trader.get_current_price(self.selected_pair)
            if not current_price:
                messagebox.showerror("Ошибка", "Не удалось получить текущую цену")
                return
                
            # Расчет размера позиции
            size = self.trader.calculate_position_size(
                self.selected_pair, amount, leverage, current_price
            )
            
            if not size or size == "0":
                messagebox.showerror("Ошибка", "Не удалось рассчитать размер позиции")
                return
                
            # Размещение ордера без подтверждения
            side_text = "LONG" if side == "buy" else "SHORT"
            self.log_message(f"Размещение {side_text} ордера: {self.selected_pair}, маржа ${amount}, плечо {leverage}x")
            
            result = self.trader.place_market_order(
                self.selected_pair, side, size, leverage
            )
            
            if result['success']:
                self.log_message(f"✅ Ордер размещен! ID: {result['order_id']}", "SUCCESS")
                self.update_positions()
            else:
                self.log_message(f"❌ Ошибка размещения: {result['error']}", "ERROR")
                messagebox.showerror("Ошибка", f"Ошибка размещения ордера: {result['error']}")
                    
        except ValueError:
            messagebox.showwarning("Предупреждение", "Введите корректную сумму")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def place_preset_order(self, side, amount, leverage):
        """Размещение ордера по пресету"""
        if not self.selected_pair:
            self.log_message("⚠️ Сначала выберите торговую пару!", "WARNING")
            messagebox.showwarning("Предупреждение", "Выберите торговую пару")
            return
            
        try:
            side_text = "LONG" if side == "buy" else "SHORT"
            self.log_message(f"🚀 ПРЕСЕТ {side_text}: {self.selected_pair}, маржа ${amount}, плечо {leverage}x")
            
            # Получаем текущую цену
            current_price = self.trader.get_current_price(self.selected_pair)
            if not current_price:
                self.log_message("❌ Не удалось получить цену для пресета", "ERROR")
                messagebox.showerror("Ошибка", "Не удалось получить текущую цену")
                return
            
            # Рассчитываем размер позиции
            size = self.trader.calculate_position_size(
                self.selected_pair, amount, leverage, current_price
            )
            
            if not size or size == "0":
                self.log_message("❌ Не удалось рассчитать размер позиции для пресета", "ERROR")
                messagebox.showerror("Ошибка", "Не удалось рассчитать размер позиции")
                return
            
            # Размещение ордера
            result = self.trader.place_market_order(
                self.selected_pair, side, size, leverage
            )
            
            if result['success']:
                self.log_message(f"✅ ПРЕСЕТ {side_text} размещен! ID: {result['order_id']}", "SUCCESS")
                # Обновляем поля с использованными значениями
                self.amount_entry.delete(0, tk.END)
                self.amount_entry.insert(0, str(amount))
                self.leverage_var.set(str(leverage))
                self.update_positions()
            else:
                self.log_message(f"❌ Ошибка пресета: {result['error']}", "ERROR")
                messagebox.showerror("Ошибка", f"Ошибка размещения ордера: {result['error']}")
                
        except Exception as e:
            self.log_message(f"❌ Ошибка пресета: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
            
    def update_positions(self):
        """Обновление таблицы позиций"""
        try:
            positions = self.trader.get_positions()
            
            # Очистка таблицы
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
                
            total_pnl = 0
            
            # Добавление позиций
            for pos in positions:
                inst_id = pos['instId']
                side = "LONG" if float(pos['pos']) > 0 else "SHORT"
                size = abs(float(pos['pos']))
                avg_price = float(pos['avgPx'])
                mark_price = float(pos['markPx'])
                pnl = float(pos['upl'])
                pnl_ratio = float(pos['uplRatio'])
                
                total_pnl += pnl
                
                # Цвет для PnL
                pnl_color = 'green' if pnl >= 0 else 'red'
                pnl_text = f"${pnl:,.2f}"
                pnl_ratio_text = f"{pnl_ratio*100:+.2f}%"
                
                # Добавление строки
                item = self.positions_tree.insert('', 'end', values=(
                    inst_id, side, f"{size:,.0f}", f"${avg_price:,.4f}", 
                    f"${mark_price:,.4f}", pnl_text, pnl_ratio_text
                ))
                
                # Установка цвета для PnL
                if pnl >= 0:
                    self.positions_tree.set(item, 'PnL', pnl_text)
                    self.positions_tree.set(item, 'PnL%', pnl_ratio_text)
                
            # Обновление общего PnL
            total_pnl_color = 'green' if total_pnl >= 0 else 'red'
            self.total_pnl_label.config(
                text=f"Общий PnL: ${total_pnl:,.2f}",
                fg=total_pnl_color
            )
            
            self.current_positions = positions
            
        except Exception as e:
            print(f"Ошибка обновления позиций: {e}")
            
    def start_pnl_updates(self):
        """Запуск обновления PnL в реальном времени"""
        def update_loop():
            while not self.stop_pnl_updates:
                self.update_positions()
                time.sleep(2)  # Обновление каждые 2 секунды
                
        self.pnl_update_thread = threading.Thread(target=update_loop, daemon=True)
        self.pnl_update_thread.start()
        
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def close_selected_position(self):
        """Закрытие выбранной позиции"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.positions_tree.item(item, 'values')
        inst_id = values[0]
        
        confirm = messagebox.askyesno("Подтверждение", f"Закрыть позицию {inst_id}?")
        if confirm:
            try:
                result = self.trader.close_position(inst_id, None)
                if result['success']:
                    messagebox.showinfo("Успех", "Позиция закрыта")
                    self.update_positions()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка закрытия: {result['error']}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
                
    def close_all_positions(self):
        """Закрытие всех позиций"""
        if not self.current_positions:
            messagebox.showinfo("Информация", "Нет открытых позиций")
            return
            
        confirm = messagebox.askyesno("Подтверждение", 
                                    f"Закрыть все позиции ({len(self.current_positions)} шт.)?")
        if confirm:
            try:
                result = self.trader.close_all_positions()
                
                if result['success']:
                    messagebox.showinfo("Успех", result['message'])
                else:
                    # Показываем детали по каждой позиции
                    error_details = []
                    for r in result.get('results', []):
                        if not r['success']:
                            error_details.append(f"{r['instId']}: {r['error']}")
                    
                    if error_details:
                        messagebox.showwarning("Ошибки закрытия", 
                                             f"{result['message']}\n\nОшибки:\n" + "\n".join(error_details))
                    else:
                        messagebox.showerror("Ошибка", result.get('error', 'Неизвестная ошибка'))
                    
                self.update_positions()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
                
    def close_all_positions(self):
        """Закрытие всех позиций"""
        if not self.current_positions:
            self.log_message("ℹ️ Нет открытых позиций для закрытия", "INFO")
            messagebox.showinfo("Информация", "Нет открытых позиций")
            return
            
        self.log_message(f"🚫 Закрытие всех позиций ({len(self.current_positions)} шт.)")
        
        try:
            result = self.trader.close_all_positions()
            
            if result['success']:
                self.log_message(f"✅ {result['message']}", "SUCCESS")
                messagebox.showinfo("Успех", result['message'])
            else:
                # Показываем детали по каждой позиции
                error_details = []
                for r in result.get('results', []):
                    if not r['success']:
                        error_details.append(f"{r['instId']}: {r['error']}")
                        self.log_message(f"❌ {r['instId']}: {r['error']}", "ERROR")
                
                if error_details:
                    self.log_message(f"⚠️ Частичное закрытие: {result['message']}", "WARNING")
                    messagebox.showwarning("Ошибки закрытия", 
                                         f"{result['message']}\n\nОшибки:\n" + "\n".join(error_details))
                else:
                    self.log_message(f"❌ {result.get('error', 'Неизвестная ошибка')}", "ERROR")
                    messagebox.showerror("Ошибка", result.get('error', 'Неизвестная ошибка'))
                
            self.update_positions()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка закрытия позиций: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def close_selected_position(self):
        """Закрытие выбранной позиции из контекстного меню"""
        selected_item = self.positions_tree.selection()
        if not selected_item:
            return
            
        # Получаем данные выбранной позиции
        item_values = self.positions_tree.item(selected_item[0], 'values')
        if not item_values:
            return
            
        inst_id = item_values[0]  # Первая колонка - пара
        self.log_message(f"🚫 Закрытие позиции: {inst_id}")
        
        try:
            result = self.trader.close_position(inst_id, None)
            
            if result['success']:
                self.log_message(f"✅ Позиция {inst_id} закрыта! ID: {result['order_id']}", "SUCCESS")
                messagebox.showinfo("Успех", f"Позиция {inst_id} закрыта!")
            else:
                self.log_message(f"❌ Ошибка закрытия {inst_id}: {result['error']}", "ERROR")
                messagebox.showerror("Ошибка", f"Ошибка закрытия позиции: {result['error']}")
                
            self.update_positions()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка закрытия {inst_id}: {e}", "ERROR")
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def show_context_menu(self, event):
        """Показать контекстное меню для позиций"""
        # Выбираем элемент при правом клике
        item = self.positions_tree.identify_row(event.y)
        if item:
            self.positions_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_closing(self):
        """Обработка закрытия приложения"""
        self.log_message("👋 Закрытие приложения")
        self.stop_pnl_updates = True
        if self.pnl_update_thread:
            self.pnl_update_thread.join(timeout=1)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = OKXTradingApp(root)
    
    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Запуск приложения
    root.mainloop() 