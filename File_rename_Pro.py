import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Renamer")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        
        # Устанавливаем иконку (если есть)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Переменные
        self.folder_path = tk.StringVar()
        self.files = []
        self.tree_items = {}  # Словарь для связи id дерева с индексами файлов
        
        # Стили
        self.setup_styles()
        
        # Создаем интерфейс с панелями
        self.create_widgets()
        
        # Биндим прокрутку колесиком мыши
        self.bind_mouse_scroll()
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настраиваем шрифт для кнопок
        style.configure("TButton", font=('Arial', 9))
        style.configure("Accent.TButton", font=('Arial', 10, 'bold'))
        
        # Цвета
        self.bg_color = "#f0f0f0"
    
    def bind_mouse_scroll(self):
        """Привязка прокрутки колесиком мыши ко всем элементам"""
        def on_mouse_wheel(event):
            widget = event.widget.winfo_containing(event.x_root, event.y_root)
            
            if widget:
                if hasattr(widget, 'yview'):
                    delta = -1 if event.delta > 0 else 1
                    widget.yview_scroll(delta, "units")
                elif widget.winfo_parent() and hasattr(widget.master, 'yview'):
                    delta = -1 if event.delta > 0 else 1
                    widget.master.yview_scroll(delta, "units")
            
            return "break"
        
        self.root.bind("<MouseWheel>", on_mouse_wheel)
        self.root.bind("<Button-4>", lambda e: on_mouse_wheel(type('Event', (), {'delta': 120, 'widget': e.widget})()))
        self.root.bind("<Button-5>", lambda e: on_mouse_wheel(type('Event', (), {'delta': -120, 'widget': e.widget})()))
    
    def create_widgets(self):
        """Создание виджетов интерфейса с панелями"""
        # Главный контейнер с возможностью разделения
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ВЕРХНЯЯ ЧАСТЬ - Выбор папки и список файлов
        self.create_top_section()
        
        # СРЕДНЯЯ ЧАСТЬ - Режимы и параметры (фиксированной высоты)
        self.create_middle_section()
        
        # НИЖНЯЯ ЧАСТЬ - Предпросмотр и кнопка переименования
        self.create_bottom_section()
    
    def create_top_section(self):
        """Создание верхней секции с выбором папки и списком файлов"""
        top_frame = ttk.Frame(self.main_paned)
        
        # ПАНЕЛЬ ВЫБОРА ПАПКИ
        folder_frame = ttk.LabelFrame(top_frame, text="Папка с файлами", padding="8")
        folder_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        folder_inner = ttk.Frame(folder_frame)
        folder_inner.pack(fill=tk.X, expand=True)
        
        ttk.Label(folder_inner, text="Путь:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.folder_entry = ttk.Entry(folder_inner, textvariable=self.folder_path, width=70)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(folder_inner, 
                  text="Обзор...", 
                  command=self.browse_folder,
                  width=12).pack(side=tk.LEFT, padx=(5, 0))
        
        # Кнопки управления файлами
        buttons_frame = ttk.Frame(folder_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_btn = ttk.Button(buttons_frame,
                                     text="Обновить список файлов",
                                     command=self.load_files,
                                     width=25)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.confirm_selection_btn = ttk.Button(buttons_frame,
                                               text="Подтвердить выделение",
                                               command=self.confirm_selection,
                                               width=25,
                                               state=tk.DISABLED)
        self.confirm_selection_btn.pack(side=tk.LEFT, padx=10)
        
        self.select_all_btn = ttk.Button(buttons_frame,
                                        text="Выделить все",
                                        command=self.select_all,
                                        width=15)
        self.select_all_btn.pack(side=tk.LEFT, padx=10)
        
        self.deselect_btn = ttk.Button(buttons_frame,
                                      text="Снять выделение",
                                      command=self.deselect_all,
                                      width=15)
        self.deselect_btn.pack(side=tk.LEFT, padx=10)
        
        # Информация о файлах
        info_frame = ttk.Frame(folder_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.file_count_label = ttk.Label(info_frame, text="Файлов: 0", font=('Arial', 9))
        self.file_count_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.selected_count_label = ttk.Label(info_frame, text="Выбрано: 0", font=('Arial', 9))
        self.selected_count_label.pack(side=tk.LEFT)
        
        # СПИСОК ФАЙЛОВ С ПРОКРУТКОЙ (панель с изменяемой высотой)
        list_frame = ttk.LabelFrame(top_frame, text="Список файлов", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Внутренний фрейм для Treeview и скроллбара
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview для отображения файлов
        columns = ('name', 'size', 'modified', 'selected')
        self.file_tree = ttk.Treeview(tree_container, columns=columns, show='tree headings', selectmode='extended')
        
        # Настраиваем колонки
        self.file_tree.heading('#0', text='№')
        self.file_tree.column('#0', width=50, stretch=False, anchor='center')
        
        self.file_tree.heading('name', text='Имя файла')
        self.file_tree.column('name', width=450, anchor='w')
        
        self.file_tree.heading('size', text='Размер')
        self.file_tree.column('size', width=100, anchor='center', stretch=False)
        
        self.file_tree.heading('modified', text='Изменен')
        self.file_tree.column('modified', width=150, anchor='center', stretch=False)
        
        self.file_tree.heading('selected', text='✓')
        self.file_tree.column('selected', width=50, anchor='center', stretch=False)
        
        # Полосы прокрутки
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Размещаем Treeview и скроллбары
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # Привязываем обработчик выделения
        self.file_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Кнопка инвертирования выделения
        list_buttons_frame = ttk.Frame(list_frame)
        list_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(list_buttons_frame,
                  text="Инвертировать",
                  command=self.invert_selection,
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        # Добавляем верхнюю секцию в панель
        self.main_paned.add(top_frame, weight=2)
    
    def create_middle_section(self):
        """Создание средней секции с режимами и параметрами (фиксированной высоты)"""
        middle_frame = ttk.Frame(self.main_paned)
        
        # РЕЖИМЫ ПЕРЕИМЕНОВАНИЯ (в одну строку)
        mode_frame = ttk.LabelFrame(middle_frame, text="Режим переименования", padding="8")
        mode_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Переменная для выбора режима
        self.rename_mode = tk.StringVar(value="replace")
        
        # Радиокнопки для выбора режима в одну строку
        modes_frame = ttk.Frame(mode_frame)
        modes_frame.pack(fill=tk.X, expand=True)
        
        modes = [
            ("Заменить текст", "replace"),
            ("Добавить префикс", "prefix"),
            ("Добавить суффикс", "suffix"),
            ("Удалить с начала", "remove_start"),
            ("Удалить с конца", "remove_end"),
            ("Нумерация", "numbering")
        ]
        
        for i, (text, mode) in enumerate(modes):
            rb = ttk.Radiobutton(modes_frame, 
                                text=text, 
                                variable=self.rename_mode, 
                                value=mode,
                                command=self.on_mode_change)
            rb.pack(side=tk.LEFT, padx=10, pady=2)
        
        # ПАНЕЛЬ ПАРАМЕТРОВ (фиксированной высоты, подстраивается под режим)
        self.params_frame = ttk.LabelFrame(middle_frame, text="Параметры", padding="8")
        self.params_frame.pack(fill=tk.X, padx=5)
        
        # Фрейм для параметров с фиксированной высотой
        self.params_container = ttk.Frame(self.params_frame)
        self.params_container.pack(fill=tk.X, expand=True)
        
        # Кнопка обновления предпросмотра (в правой части)
        preview_btn_frame = ttk.Frame(self.params_frame)
        preview_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Пустое пространство слева для выравнивания кнопки вправо
        ttk.Label(preview_btn_frame, text="").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.update_preview_btn = ttk.Button(preview_btn_frame,
                                            text="Обновить предпросмотр",
                                            command=self.update_preview,
                                            width=20)
        self.update_preview_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Создаем виджеты параметров (изначально для режима replace)
        self.create_param_widgets()
        
        # Устанавливаем фиксированную высоту для средней секции
        middle_frame.configure(height=150)
        
        # Добавляем среднюю секцию в панель
        self.main_paned.add(middle_frame, weight=0)  # weight=0 для фиксированной высоты
    
    def create_param_widgets(self):
        """Создание виджетов параметров для разных режимов"""
        # Очищаем контейнер параметров
        for widget in self.params_container.winfo_children():
            widget.destroy()
        
        mode = self.rename_mode.get()
        
        if mode == "replace":
            # Первая строка: поля ввода
            row1 = ttk.Frame(self.params_container)
            row1.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(row1, text="Заменить:").pack(side=tk.LEFT, padx=(0, 5))
            self.old_text = ttk.Entry(row1, width=20)
            self.old_text.pack(side=tk.LEFT, padx=5)
            self.old_text.insert(0, "старое")
            
            ttk.Label(row1, text="На:").pack(side=tk.LEFT, padx=(10, 5))
            self.new_text = ttk.Entry(row1, width=20)
            self.new_text.pack(side=tk.LEFT, padx=5)
            self.new_text.insert(0, "новое")
            
            # Вторая строка: чекбокс "Учитывать регистр"
            row2 = ttk.Frame(self.params_container)
            row2.pack(fill=tk.X)
            
            self.case_sensitive = tk.BooleanVar(value=True)
            ttk.Checkbutton(row2, 
                           text="Учитывать регистр",
                           variable=self.case_sensitive).pack(side=tk.LEFT, padx=(0, 0))
            
        elif mode == "prefix":
            ttk.Label(self.params_container, text="Префикс:").pack(side=tk.LEFT, padx=(0, 5))
            self.prefix_text = ttk.Entry(self.params_container, width=30)
            self.prefix_text.pack(side=tk.LEFT, padx=5)
            self.prefix_text.insert(0, "префикс_")
            
        elif mode == "suffix":
            ttk.Label(self.params_container, text="Суффикс:").pack(side=tk.LEFT, padx=(0, 5))
            self.suffix_text = ttk.Entry(self.params_container, width=30)
            self.suffix_text.pack(side=tk.LEFT, padx=5)
            self.suffix_text.insert(0, "_суффикс")
            
            ttk.Label(self.params_container, text="(перед расширением)").pack(side=tk.LEFT, padx=(10, 5))
            
        elif mode == "remove_start":
            ttk.Label(self.params_container, text="Удалить символов с начала:").pack(side=tk.LEFT, padx=(0, 5))
            self.remove_start_var = tk.IntVar(value=3)
            ttk.Spinbox(self.params_container, 
                       from_=1, 
                       to=100, 
                       textvariable=self.remove_start_var,
                       width=8).pack(side=tk.LEFT, padx=5)
            
        elif mode == "remove_end":
            ttk.Label(self.params_container, text="Удалить символов с конца:").pack(side=tk.LEFT, padx=(0, 5))
            self.remove_end_var = tk.IntVar(value=3)
            ttk.Spinbox(self.params_container, 
                       from_=1, 
                       to=100, 
                       textvariable=self.remove_end_var,
                       width=8).pack(side=tk.LEFT, padx=5)
            
            ttk.Label(self.params_container, text="(перед расширением)").pack(side=tk.LEFT, padx=(10, 5))
            
        elif mode == "numbering":
            # Первая строка: начальный номер и шаг
            row1 = ttk.Frame(self.params_container)
            row1.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(row1, text="Начальный номер:").pack(side=tk.LEFT, padx=(0, 5))
            self.start_num_var = tk.IntVar(value=1)
            ttk.Spinbox(row1,
                       from_=1,
                       to=9999,
                       textvariable=self.start_num_var,
                       width=8).pack(side=tk.LEFT, padx=5)
            
            ttk.Label(row1, text="Шаг:").pack(side=tk.LEFT, padx=(20, 5))
            self.step_var = tk.IntVar(value=1)
            ttk.Spinbox(row1,
                       from_=1,
                       to=10,
                       textvariable=self.step_var,
                       width=8).pack(side=tk.LEFT, padx=5)
            
            # Вторая строка: формат и разделитель
            row2 = ttk.Frame(self.params_container)
            row2.pack(fill=tk.X)
            
            ttk.Label(row2, text="Формат:").pack(side=tk.LEFT, padx=(0, 5))
            self.format_var = tk.StringVar(value="01")
            format_combo = ttk.Combobox(row2,
                                       textvariable=self.format_var,
                                       values=["1", "01", "001", "0001"],
                                       width=8,
                                       state="readonly")
            format_combo.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(row2, text="Разделитель:").pack(side=tk.LEFT, padx=(20, 5))
            self.separator_var = tk.StringVar(value="_")
            ttk.Entry(row2,
                     textvariable=self.separator_var,
                     width=8).pack(side=tk.LEFT, padx=5)
    
    def create_bottom_section(self):
        """Создание нижней секции с предпросмотром и кнопкой переименования"""
        bottom_frame = ttk.Frame(self.main_paned)
        
        # ПАНЕЛЬ ПРЕДПРОСМОТРА (маленькая по умолчанию, но можно менять)
        preview_frame = ttk.LabelFrame(bottom_frame, text="Предпросмотр изменений", padding="8")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, 
                                                     font=('Courier New', 9),
                                                     wrap=tk.WORD,
                                                     height=6)  # Маленькая высота по умолчанию
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # КНОПКА ПЕРЕИМЕНОВАНИЯ (под предпросмотром, больше ничего нет)
        rename_frame = ttk.Frame(bottom_frame)
        rename_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Пустое пространство слева для выравнивания кнопки вправо
        ttk.Label(rename_frame, text="").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.rename_btn = ttk.Button(rename_frame,
                                    text="ПЕРЕИМЕНОВАТЬ",
                                    command=self.perform_rename,
                                    style="Accent.TButton",
                                    width=25,
                                    state=tk.DISABLED)
        self.rename_btn.pack(side=tk.RIGHT)
        
        # СТАТУС БАР
        status_frame = ttk.Frame(bottom_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.status_bar = ttk.Label(status_frame, 
                                   text="Готов к работе. Выберите папку с файлами.", 
                                   relief=tk.SUNKEN,
                                   anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Кнопка статистики (маленькая, справа)
        ttk.Button(status_frame,
                  text="Статистика",
                  command=self.show_stats,
                  width=12).pack(side=tk.RIGHT)
        
        # Добавляем нижнюю секцию в панель
        self.main_paned.add(bottom_frame, weight=1)
    
    def browse_folder(self):
        """Выбор папки через диалог"""
        folder = filedialog.askdirectory(title="Выберите папку с файлами")
        if folder:
            self.folder_path.set(folder)
            self.load_files()
    
    def load_files(self):
        """Загрузка списка файлов из папки"""
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Ошибка", "Укажите существующую папку!")
            return
        
        try:
            self.files = []
            self.tree_items = {}
            
            # Получаем все файлы из папки
            for item in sorted(os.listdir(folder)):
                item_path = os.path.join(folder, item)
                if os.path.isfile(item_path):
                    # Получаем информацию о файле
                    stat = os.stat(item_path)
                    size = self.format_size(stat.st_size)
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    self.files.append({
                        'name': item,
                        'path': item_path,
                        'size': size,
                        'modified': modified,
                        'selected': False,
                        'tree_id': None
                    })
            
            self.update_file_list()
            self.update_status(f"Загружено файлов: {len(self.files)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файлы:\n{str(e)}")
    
    def update_file_list(self):
        """Обновление списка файлов в Treeview"""
        # Очищаем Treeview
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.tree_items = {}
        
        # Добавляем файлы
        for i, file_info in enumerate(self.files):
            values = (
                file_info['name'],
                file_info['size'],
                file_info['modified'],
                '✓' if file_info['selected'] else ''
            )
            
            item_id = self.file_tree.insert('', 'end', 
                                          text=str(i+1),
                                          values=values)
            
            # Сохраняем связь
            self.tree_items[item_id] = i
            file_info['tree_id'] = item_id
            
            # Настраиваем цвет для выбранных
            if file_info['selected']:
                self.file_tree.item(item_id, tags=('selected',))
            else:
                self.file_tree.item(item_id, tags=())
        
        # Настраиваем теги для выделения
        self.file_tree.tag_configure('selected', background='#e0f7fa')
        
        # Обновляем счетчики
        self.file_count_label.config(text=f"Файлов: {len(self.files)}")
        selected_count = sum(1 for f in self.files if f['selected'])
        self.selected_count_label.config(text=f"Выбрано: {selected_count}")
        
        # Обновляем состояние кнопок
        if selected_count > 0:
            self.confirm_selection_btn.config(state=tk.NORMAL)
            self.rename_btn.config(state=tk.NORMAL)
            self.rename_btn.config(text=f"ПЕРЕИМЕНОВАТЬ ({selected_count})")
        else:
            self.confirm_selection_btn.config(state=tk.DISABLED)
            self.rename_btn.config(state=tk.DISABLED)
            self.rename_btn.config(text="ПЕРЕИМЕНОВАТЬ")
    
    def on_tree_select(self, event):
        """Обработчик выделения в Treeview"""
        selected_items = self.file_tree.selection()
        if selected_items:
            self.confirm_selection_btn.config(state=tk.NORMAL)
        else:
            self.confirm_selection_btn.config(state=tk.DISABLED)
    
    def confirm_selection(self):
        """Подтвердить выделение (после выбора через Ctrl/Shift)"""
        selected_items = self.file_tree.selection()
        
        # Сначала снимаем выделение со всех
        for file_info in self.files:
            file_info['selected'] = False
        
        # Затем отмечаем выбранные
        for item_id in selected_items:
            if item_id in self.tree_items:
                index = self.tree_items[item_id]
                self.files[index]['selected'] = True
        
        self.update_file_list()
        self.update_preview()
        self.update_status(f"Выбрано файлов: {sum(1 for f in self.files if f['selected'])}")
    
    def format_size(self, size_bytes):
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def select_all(self):
        """Выбрать все файлы"""
        for file_info in self.files:
            file_info['selected'] = True
        self.update_file_list()
        self.update_preview()
    
    def deselect_all(self):
        """Снять выделение со всех файлов"""
        for file_info in self.files:
            file_info['selected'] = False
        self.update_file_list()
        self.update_preview()
    
    def invert_selection(self):
        """Инвертировать выделение"""
        for file_info in self.files:
            file_info['selected'] = not file_info['selected']
        self.update_file_list()
        self.update_preview()
    
    def on_mode_change(self):
        """Обработчик изменения режима"""
        self.create_param_widgets()
        self.update_preview()
    
    def generate_new_name(self, filename, index=None):
        """Генерация нового имени файла"""
        name, ext = os.path.splitext(filename)
        mode = self.rename_mode.get()
        
        try:
            if mode == "replace":
                old = self.old_text.get()
                new = self.new_text.get()
                if old:
                    if self.case_sensitive.get():
                        return filename.replace(old, new)
                    else:
                        # Без учета регистра
                        import re
                        return re.sub(re.escape(old), new, filename, flags=re.IGNORECASE)
                    
            elif mode == "prefix":
                prefix = self.prefix_text.get()
                return prefix + filename
                
            elif mode == "suffix":
                suffix = self.suffix_text.get()
                return name + suffix + ext
                
            elif mode == "remove_start":
                count = self.remove_start_var.get()
                if count < len(filename):
                    return filename[count:]
                else:
                    return ext if ext else filename
                
            elif mode == "remove_end":
                count = self.remove_end_var.get()
                if count < len(name):
                    return name[:-count] + ext
                else:
                    return ext
                    
            elif mode == "numbering" and index is not None:
                # Нумерация только для выбранных файлов
                selected_files = [f for f in self.files if f['selected']]
                if filename in [f['name'] for f in selected_files]:
                    file_index = [f['name'] for f in selected_files].index(filename)
                    start = self.start_num_var.get()
                    step = self.step_var.get()
                    fmt = self.format_var.get()
                    sep = self.separator_var.get()
                    
                    num = start + (file_index * step)
                    num_str = f"{num:{fmt}}"
                    return f"{num_str}{sep}{filename}"
                
        except Exception as e:
            print(f"Error generating new name: {e}")
            
        return filename
    
    def update_preview(self):
        """Обновление предпросмотра изменений"""
        self.preview_text.delete(1.0, tk.END)
        
        selected_files = [f for f in self.files if f['selected']]
        if not selected_files:
            self.preview_text.insert(tk.END, "Нет выбранных файлов для предпросмотра\n")
            self.preview_text.insert(tk.END, "Выделите файлы в списке и нажмите 'Подтвердить выделение'")
            return
        
        self.preview_text.insert(tk.END, f"БУДЕТ ПЕРЕИМЕНОВАНО: {len(selected_files)} файл(ов)\n")
        self.preview_text.insert(tk.END, "="*70 + "\n\n")
        
        for i, file_info in enumerate(selected_files[:10]):
            old_name = file_info['name']
            new_name = self.generate_new_name(old_name, i)
            
            self.preview_text.insert(tk.END, f"{i+1:3}. {old_name}\n")
            self.preview_text.insert(tk.END, f"     -> {new_name}\n")
            
            if old_name == new_name:
                self.preview_text.insert(tk.END, f"     (имя не изменится)\n")
            
            self.preview_text.insert(tk.END, "\n")
        
        if len(selected_files) > 10:
            self.preview_text.insert(tk.END, f"\n... и еще {len(selected_files) - 10} файлов\n")
        
        self.update_status(f"Предпросмотр для {len(selected_files)} выбранных файлов")
    
    def perform_rename(self):
        """Выполнение переименования"""
        selected_files = [f for f in self.files if f['selected']]
        if not selected_files:
            messagebox.showwarning("Внимание", "Не выбраны файлы для переименования!")
            return
        
        # Проверяем параметры
        mode = self.rename_mode.get()
        if mode == "replace" and not self.old_text.get():
            messagebox.showwarning("Внимание", "Не указана строка для замены!")
            return
        elif mode == "prefix" and not self.prefix_text.get():
            messagebox.showwarning("Внимание", "Не указан префикс!")
            return
        elif mode == "suffix" and not self.suffix_text.get():
            messagebox.showwarning("Внимание", "Не указан суффикс!")
            return
        
        # Подтверждение
        confirm = messagebox.askyesno("Подтверждение", 
                                     f"Вы уверены, что хотите переименовать {len(selected_files)} файлов?\n\n"
                                     f"Режим: {self.get_mode_name(mode)}\n"
                                     f"Операция необратима!")
        if not confirm:
            return
        
        success_count = 0
        error_count = 0
        errors = []
        renamed_files = []
        
        if mode == "numbering":
            success_count, error_count, errors, renamed_files = self.perform_numbering(selected_files)
        else:
            for i, file_info in enumerate(selected_files):
                old_path = file_info['path']
                old_name = file_info['name']
                new_name = self.generate_new_name(old_name, i)
                
                if old_name != new_name:
                    new_path = os.path.join(os.path.dirname(old_path), new_name)
                    
                    if os.path.exists(new_path) and old_path != new_path:
                        error_count += 1
                        errors.append(f"{old_name}: Файл '{new_name}' уже существует")
                        continue
                    
                    try:
                        os.rename(old_path, new_path)
                        success_count += 1
                        
                        renamed_files.append({
                            'old_name': old_name,
                            'new_name': new_name,
                            'index': self.files.index(file_info)
                        })
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"{old_name}: {str(e)}")
        
        # Обновляем информацию о файлах
        for rename_info in renamed_files:
            idx = rename_info['index']
            self.files[idx]['name'] = rename_info['new_name']
            self.files[idx]['path'] = os.path.join(os.path.dirname(self.files[idx]['path']), 
                                                  rename_info['new_name'])
        
        # Обновляем список
        self.update_file_list()
        
        # Показываем результат
        if error_count == 0:
            messagebox.showinfo("Успешно", f"Успешно переименовано: {success_count} файлов")
            self.update_status(f"Успешно переименовано: {success_count} файлов")
        else:
            error_msg = f"Результат:\nУспешно: {success_count}\nОшибок: {error_count}"
            if errors:
                error_msg += f"\n\nПервые ошибки:\n" + "\n".join(errors[:3])
                if len(errors) > 3:
                    error_msg += f"\n... и еще {len(errors) - 3} ошибок"
            
            messagebox.showerror("Результат", error_msg)
            self.update_status(f"Переименовано: {success_count}, Ошибок: {error_count}")
    
    def get_mode_name(self, mode):
        """Получение читаемого имени режима"""
        names = {
            'replace': 'Замена части текста',
            'prefix': 'Добавление префикса',
            'suffix': 'Добавление суффикса',
            'remove_start': 'Удаление с начала',
            'remove_end': 'Удаление с конца',
            'numbering': 'Нумерация'
        }
        return names.get(mode, mode)
    
    def perform_numbering(self, selected_files):
        """Выполнение нумерации файлов"""
        start = self.start_num_var.get()
        step = self.step_var.get()
        fmt = self.format_var.get()
        sep = self.separator_var.get()
        
        success_count = 0
        error_count = 0
        errors = []
        renamed_files = []
        
        # Проверяем уникальность имен
        planned_renames = []
        used_names = set()
        
        for i, file_info in enumerate(selected_files):
            old_name = file_info['name']
            num = start + (i * step)
            num_str = f"{num:{fmt}}"
            new_name = f"{num_str}{sep}{old_name}"
            
            if new_name in used_names:
                error_count += 1
                errors.append(f"{old_name}: Имя '{new_name}' будет дублироваться")
            else:
                used_names.add(new_name)
                planned_renames.append((file_info, old_name, new_name, i))
        
        if error_count > 0:
            return 0, error_count, errors, []
        
        # Выполняем переименование
        for file_info, old_name, new_name, order_idx in planned_renames:
            old_path = file_info['path']
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            if os.path.exists(new_path) and old_path != new_path:
                error_count += 1
                errors.append(f"{old_name}: Файл '{new_name}' уже существует")
                continue
            
            try:
                os.rename(old_path, new_path)
                success_count += 1
                
                renamed_files.append({
                    'old_name': old_name,
                    'new_name': new_name,
                    'index': self.files.index(file_info)
                })
                
            except Exception as e:
                error_count += 1
                errors.append(f"{old_name}: {str(e)}")
        
        return success_count, error_count, errors, renamed_files
    
    def show_stats(self):
        """Показать статистику"""
        total = len(self.files)
        selected = sum(1 for f in self.files if f['selected'])
        
        stats = f"""
        Статистика:
        
        Всего файлов в папке: {total}
        Выбрано для переименования: {selected}
        
        Папка: {self.folder_path.get() or 'Не выбрана'}
        
        Текущий режим: {self.get_mode_name(self.rename_mode.get())}
        
        Инструкция:
        1. Выберите папку
        2. Выделите файлы (Ctrl/Shift + клик)
        3. Нажмите "Подтвердить выделение"
        4. Выберите режим и параметры
        5. Нажмите "Обновить предпросмотр"
        6. Нажмите "ПЕРЕИМЕНОВАТЬ"
        """
        
        messagebox.showinfo("Статистика и инструкция", stats)
    
    def update_status(self, message):
        """Обновление статус-бара"""
        self.status_bar.config(text=message)

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()