#Импортирование библиотек.Не забудь tkinter as tk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

#сервак.окно
class RestaurantSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления рестораном — Вход")
        self.root.geometry("420x320")
        self.root.resizable(False, False)

        #бдюда
        self.menu = [
            {"id": 1, "name": "Пельмени", "price": 10.0, "weight": "300 г", "desc": "пельмешки вкусные", "stop": False},
            {"id": 2, "name": "Паста Карбонара", "price": 15.0, "weight": "280 г", "desc": "Спагетти, бекон, пармезан, желток, сливки", "stop": False},
            {"id": 3, "name": "Салат Цезарь с курицей", "price": 40.0, "weight": "250 г", "desc": "Куриное филе, романо, черри, соус Цезарь", "stop": False},
            {"id": 4, "name": "Дошик с курицей", "price": 1.0, "weight": "400 мл", "desc": "дошик + курица", "stop": True},
            {"id": 5, "name": "Икра", "price": 1000.0, "weight": "350 мл", "desc": "Дорогая", "stop": False},
        ]
        self.next_menu_id = 6

        self.orders = []
        self.next_order_id = 101 #как в КФС

        self.promocodes = {"SALE10": 0.10, "VIP20": 0.20, "Baryshev": 0.99}
        self.payment_methods = {
            "Банковская карта": True,
            "СБП (QR-код)": True,
            "Наличные официанту": True,
            "Apple Pay / Google Pay (Шлюз недоступен)": False,
        }

        self.windows = []
        self.build_login_ui()

    def build_login_ui(self):
        frame = tk.Frame(self.root, padx=25, pady=25)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Ресторан «Вкус и Стиль»", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        tk.Label(frame, text="Выберите роль для входа в систему\n(можно открыть несколько окон сразу)", font=("Arial", 10), fg="#555").pack(pady=(0, 15))

        tk.Label(frame, text="Логин / Имя:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.login_entry = tk.Entry(frame, font=("Arial", 11))
        self.login_entry.insert(0, "Пользователь_1")
        self.login_entry.pack(fill=tk.X, pady=(2, 12))

        tk.Label(frame, text="Роль в системе:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.role_var = tk.StringVar(value="Клиент")
        roles_frame = tk.Frame(frame)
        roles_frame.pack(fill=tk.X, pady=5)

        for role in ["Клиент", "Администратор", "Повар"]:
            tk.Radiobutton(roles_frame, text=role, variable=self.role_var, value=role, font=("Arial", 10)).pack(side=tk.LEFT, padx=8)

        tk.Button(frame, text="Войти в систему", font=("Arial", 11, "bold"), bg="#2e7d32", fg="white", command=self.login).pack(fill=tk.X, pady=(18, 0), ipady=5)

    def login(self):
        role = self.role_var.get()
        user = self.login_entry.get().strip() or "Гость"

        if role == "Клиент":
            win = ClientWindow(self, user)
        elif role == "Администратор":
            win = AdminWindow(self, user)
        else:
            win = ChefWindow(self, user)

        self.windows.append(win)

    def broadcast_update(self):
        """Синхронизация данных во всех открытых окнах в реальном времени."""
        alive = []
        for w in self.windows:
            if w.win.winfo_exists():
                w.refresh_all()
                alive.append(w)
        self.windows = alive

    def is_dish_in_active_orders(self, dish_id):
        """Проверка, находится ли блюдо в активных заказах."""
        active_statuses = {"Новый", "Подтвержден", "В работе", "В процессе приготовления"}
        for order in self.orders:
            if order["status"] in active_statuses:
                for item in order["items"]:
                    if item["dish_id"] == dish_id:
                        return True
        return False
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ОКНО КЛИЕНТА
class ClientWindow:
    def __init__(self, app: RestaurantSystem, user_name: str, is_admin_embedded=False, parent_frame=None):
        self.app = app
        self.user_name = user_name
        self.cart = []

        if is_admin_embedded:
            self.win = parent_frame
        else:
            self.win = tk.Toplevel(app.root)
            self.win.title(f"Интерфейс Клиента — {user_name}")
            self.win.geometry("950x650")

        self.build_ui()
        self.update_clock()
        self.refresh_all()

    def build_ui(self):
        top_bar = tk.Frame(self.win, bg="#1b365d", padx=15, pady=8)
        top_bar.pack(fill=tk.X)

        tk.Label(top_bar, text="Ресторан «Вкус и Стиль» | Стол № 7", fg="white", bg="#1b365d", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        self.clock_lbl = tk.Label(top_bar, text="", fg="#ffd54f", bg="#1b365d", font=("Arial", 12, "bold"))
        self.clock_lbl.pack(side=tk.RIGHT)

        main_pane = tk.PanedWindow(self.win, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.LabelFrame(main_pane, text="Электронное меню (серым отмечен стоп-лист)", font=("Arial", 10, "bold"), padx=8, pady=8)
        main_pane.add(left_frame, width=580)

        cols = ("name", "price", "weight", "desc")
        self.menu_tree = ttk.Treeview(left_frame, columns=cols, show="headings", height=14)
        self.menu_tree.heading("name", text="Название блюда/напитка")
        self.menu_tree.heading("price", text="Цена (руб.)")
        self.menu_tree.heading("weight", text="Вес / Объем")
        self.menu_tree.heading("desc", text="Описание состава")

        self.menu_tree.column("name", width=160)
        self.menu_tree.column("price", width=85, anchor="center")
        self.menu_tree.column("weight", width=90, anchor="center")
        self.menu_tree.column("desc", width=220)

        self.menu_tree.tag_configure("stoplist", background="#e0e0e0", foreground="#757575")
        self.menu_tree.pack(fill=tk.BOTH, expand=True)

        tk.Button(left_frame, text="Добавить выбранное блюдо в корзину", bg="#1976d2", fg="white", font=("Arial", 10, "bold"), command=self.add_to_cart).pack(fill=tk.X, pady=(8, 0), ipady=4)

        right_frame = tk.Frame(main_pane)
        main_pane.add(right_frame)

        cart_box = tk.LabelFrame(right_frame, text="Актуальный состав корзины", font=("Arial", 10, "bold"), padx=8, pady=8)
        cart_box.pack(fill=tk.BOTH, expand=True)

        self.cart_tree = ttk.Treeview(cart_box, columns=("name", "qty", "sum"), show="headings", height=7)
        self.cart_tree.heading("name", text="Блюдо")
        self.cart_tree.heading("qty", text="Кол-во")
        self.cart_tree.heading("sum", text="Сумма")
        self.cart_tree.column("name", width=160)
        self.cart_tree.column("qty", width=60, anchor="center")
        self.cart_tree.column("sum", width=80, anchor="center")
        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        self.total_lbl = tk.Label(cart_box, text="Итого: 0.00 руб.", font=("Arial", 11, "bold"), anchor="e")
        self.total_lbl.pack(fill=tk.X, pady=5)

        btn_row = tk.Frame(cart_box)
        btn_row.pack(fill=tk.X)
        tk.Button(btn_row, text="Удалить из корзины", command=self.remove_from_cart).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))
        tk.Button(btn_row, text="Оформить заказ", bg="#2e7d32", fg="white", font=("Arial", 10, "bold"), command=self.open_checkout).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 0))

        orders_box = tk.LabelFrame(right_frame, text="Мои заказы и статусы", font=("Arial", 10, "bold"), padx=8, pady=8)
        orders_box.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.orders_tree = ttk.Treeview(orders_box, columns=("id", "status", "total", "paid"), show="headings", height=6)
        self.orders_tree.heading("id", text="№")
        self.orders_tree.heading("status", text="Статус заказа")
        self.orders_tree.heading("total", text="Счет")
        self.orders_tree.heading("paid", text="Оплата")
        self.orders_tree.column("id", width=45, anchor="center")
        self.orders_tree.column("status", width=130)
        self.orders_tree.column("total", width=75, anchor="center")
        self.orders_tree.column("paid", width=80, anchor="center")
        self.orders_tree.pack(fill=tk.BOTH, expand=True)

    def update_clock(self):
        if self.win.winfo_exists():
            now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
            self.clock_lbl.config(text=f"Текущее время: {now}")
            self.win.after(1000, self.update_clock)

    def refresh_all(self):
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)

        for dish in self.app.menu:
            tag = ("stoplist",) if dish["stop"] else ()
            name_display = f"{dish['name']} [СТОП-ЛИСТ]" if dish["stop"] else dish["name"]
            self.menu_tree.insert("", tk.END, iid=str(dish["id"]), values=(name_display, f"{dish['price']:.2f}", dish["weight"], dish["desc"]), tags=tag)

        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        for order in self.app.orders:
            paid_str = "Оплачен" if order["paid"] else "Ожидает"
            self.orders_tree.insert("", tk.END, values=(order["id"], order["status"], f"{order['final_total']:.2f}", paid_str))

    def add_to_cart(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите блюдо из меню!", parent=self.win)
            return

        dish_id = int(selected[0])
        dish = next((d for d in self.app.menu if d["id"] == dish_id), None)
        if not dish:
            return

        if dish["stop"]:
            messagebox.showerror("Стоп-лист", "Это блюдо временно отсутствует на кухне и недоступно для заказа!", parent=self.win)
            return

        for item in self.cart:
            if item["dish_id"] == dish_id:
                item["qty"] += 1
                self.refresh_cart()
                return

        self.cart.append({"dish_id": dish_id, "name": dish["name"], "price": dish["price"], "qty": 1})
        self.refresh_cart()

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        self.cart.pop(idx)
        self.refresh_cart()

    def refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        total = 0.0
        for idx, item in enumerate(self.cart):
            line_sum = item["price"] * item["qty"]
            total += line_sum
            self.cart_tree.insert("", tk.END, iid=str(idx), values=(item["name"], item["qty"], f"{line_sum:.2f}"))
        self.total_lbl.config(text=f"Итого: {total:.2f} руб.")

    def open_checkout(self):
        if not self.cart:
            messagebox.showwarning("Корзина пуста", "Добавьте блюда перед оформлением заказа!", parent=self.win)
            return

        checkout_win = tk.Toplevel(self.win)
        checkout_win.title("Оформление заказа и оплата")
        checkout_win.geometry("440x430")
        checkout_win.grab_set()

        raw_total = sum(i["price"] * i["qty"] for i in self.cart)
        discount_var = tk.DoubleVar(value=0.0)
        selected_method = tk.StringVar(value="")

        tk.Label(checkout_win, text="Оформление заказа", font=("Arial", 14, "bold")).pack(pady=10)

        sum_lbl = tk.Label(checkout_win, text=f"Итоговая сумма к оплате: {raw_total:.2f} руб.", font=("Arial", 12, "bold"), fg="#1b365d")
        sum_lbl.pack(pady=5)

        promo_frame = tk.Frame(checkout_win)
        promo_frame.pack(pady=8, padx=20, fill=tk.X)
        tk.Label(promo_frame, text="Промокод (SALE10 / VIP20):").pack(anchor="w")
        promo_entry = tk.Entry(promo_frame, font=("Arial", 10))
        promo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def apply_promo():
            code = promo_entry.get().strip().upper()
            if code in self.app.promocodes:
                disc = self.app.promocodes[code]
                discount_var.set(disc)
                new_sum = raw_total * (1 - disc)
                sum_lbl.config(text=f"Итого с учетом скидки ({int(disc*100)}%): {new_sum:.2f} руб.")
                messagebox.showinfo("Успех", f"Промокод применен! Скидка {int(disc*100)}%", parent=checkout_win)
            else:
                messagebox.showerror("Ошибка", "Недействительный промокод", parent=checkout_win)

        tk.Button(promo_frame, text="Применить", command=apply_promo).pack(side=tk.RIGHT)

        tk.Label(checkout_win, text="Выберите способ оплаты:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        methods_frame = tk.Frame(checkout_win, padx=20)
        methods_frame.pack(fill=tk.X)

        method_buttons = {}

        def select_payment(m_name):
            selected_method.set(m_name)
            for name, btn in method_buttons.items():
                if self.app.payment_methods[name]:
                    if name == m_name:
                        btn.config(bg="#4caf50", fg="white")
                    else:
                        btn.config(bg="#f0f0f0", fg="black")

        for method, available in self.app.payment_methods.items():
            if available:
                btn = tk.Button(methods_frame, text=method, anchor="w", bg="#f0f0f0", font=("Arial", 10),
                                command=lambda m=method: select_payment(m))
            else:
                btn = tk.Button(methods_frame, text=method, anchor="w", bg="#bdbdbd", fg="#616161", font=("Arial", 10), state=tk.DISABLED)
            btn.pack(fill=tk.X, pady=3, ipady=3)
            method_buttons[method] = btn

        def confirm_order():
            if not selected_method.get():
                messagebox.showwarning("Оплата", "Выберите доступный способ оплаты!", parent=checkout_win)
                return

            final_sum = raw_total * (1 - discount_var.get())
            new_order = {
                "id": self.app.next_order_id,
                "client": self.user_name,
                "table": "Стол № 7",
                "items": [dict(i) for i in self.cart],
                "final_total": final_sum,
                "payment_method": selected_method.get(),
                "status": "Новый",
                "paid": True,
            }
            self.app.next_order_id += 1
            self.app.orders.append(new_order)
            self.cart.clear()
            self.refresh_cart()
            checkout_win.destroy()
            self.app.broadcast_update()
            messagebox.showinfo("Заказ оформлен", f"Заказ №{new_order['id']} отправлен администратору на проверку!", parent=self.win)

        tk.Button(checkout_win, text="Оплатить и отправить заказ", bg="#2e7d32", fg="white", font=("Arial", 11, "bold"), command=confirm_order).pack(fill=tk.X, padx=20, pady=20, ipady=5)


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ОКНО АДМИНИСТРАТОРА
class AdminWindow:
    def __init__(self, app: RestaurantSystem, user_name: str):
        self.app = app
        self.user_name = user_name
        self.win = tk.Toplevel(app.root)
        self.win.title(f"Интерфейс Администратора — {user_name}")
        self.win.geometry("1050x700")

        self.active_editor = None
        self.new_row_id = None
        self.new_row_data = {}

        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        notebook = ttk.Notebook(self.win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_orders = tk.Frame(notebook)
        notebook.add(tab_orders, text="Управление заказами и счетами")
        self.build_orders_tab(tab_orders)

        tab_menu = tk.Frame(notebook)
        notebook.add(tab_menu, text="Редактирование меню ресторана")
        self.build_menu_tab(tab_menu)

        tab_client = tk.Frame(notebook)
        notebook.add(tab_client, text="Режим клиента (просмотр меню и заказ)")
        self.embedded_client = ClientWindow(self.app, self.user_name, is_admin_embedded=True, parent_frame=tab_client)

    def build_orders_tab(self, parent):
        tk.Label(parent, text="Список текущих заказов клиентов", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        cols = ("id", "table", "items", "total", "status", "paid")
        self.admin_orders_tree = ttk.Treeview(parent, columns=cols, show="headings", height=14)
        self.admin_orders_tree.heading("id", text="№ Заказа")
        self.admin_orders_tree.heading("table", text="Стол / Клиент")
        self.admin_orders_tree.heading("items", text="Состав заказа")
        self.admin_orders_tree.heading("total", text="Сумма счета (руб.)")
        self.admin_orders_tree.heading("status", text="Статус")
        self.admin_orders_tree.heading("paid", text="Статус оплаты")

        self.admin_orders_tree.column("id", width=75, anchor="center")
        self.admin_orders_tree.column("table", width=140)
        self.admin_orders_tree.column("items", width=360)
        self.admin_orders_tree.column("total", width=120, anchor="center")
        self.admin_orders_tree.column("status", width=160, anchor="center")
        self.admin_orders_tree.column("paid", width=110, anchor="center")
        self.admin_orders_tree.pack(fill=tk.BOTH, expand=True, padx=10)

        btn_panel = tk.Frame(parent, pady=12, padx=10)
        btn_panel.pack(fill=tk.X)

        tk.Button(btn_panel, text="Подтвердить заказ (на кухню)", bg="#2e7d32", fg="white", font=("Arial", 10, "bold"), command=self.confirm_order).pack(side=tk.LEFT, padx=5, ipady=4)
        tk.Button(btn_panel, text="Отклонить заказ", bg="#c62828", fg="white", font=("Arial", 10, "bold"), command=self.reject_order).pack(side=tk.LEFT, padx=5, ipady=4)
        tk.Button(btn_panel, text="Выставить счет", bg="#1565c0", fg="white", font=("Arial", 10, "bold"), command=self.issue_invoice).pack(side=tk.LEFT, padx=5, ipady=4)
        tk.Button(btn_panel, text="Удалить позицию", bg="#ef6c00", fg="white", font=("Arial", 10, "bold"), command=self.delete_order_item).pack(side=tk.LEFT, padx=5, ipady=4)

    def build_menu_tab(self, parent):
        info = tk.Label(parent, text="Двойной клик по ячейке — редактирование (если блюдо не в активном заказе). Tab — переход к следующему полю и сохранение в последней колонке.",
                        font=("Arial", 9), fg="#444")
        info.pack(anchor="w", padx=10, pady=(10, 5))

        cols = ("name", "price", "weight", "desc", "stop")
        self.admin_menu_tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        self.admin_menu_tree.heading("name", text="Название блюда")
        self.admin_menu_tree.heading("price", text="Цена (руб.)")
        self.admin_menu_tree.heading("weight", text="Вес / Объем")
        self.admin_menu_tree.heading("desc", text="Описание состава")
        self.admin_menu_tree.heading("stop", text="Стоп-лист (Да/Нет)")

        self.admin_menu_tree.column("name", width=190)
        self.admin_menu_tree.column("price", width=100, anchor="center")
        self.admin_menu_tree.column("weight", width=100, anchor="center")
        self.admin_menu_tree.column("desc", width=420)
        self.admin_menu_tree.column("stop", width=120, anchor="center")

        self.admin_menu_tree.pack(fill=tk.BOTH, expand=True, padx=10)
        self.admin_menu_tree.bind("<Double-1>", self.on_double_click_cell)

        bottom_bar = tk.Frame(parent, pady=10, padx=10)
        bottom_bar.pack(fill=tk.X)
        tk.Button(bottom_bar, text="Добавить", bg="#2e7d32", fg="white", font=("Arial", 10, "bold"), width=15, command=self.add_new_menu_row).pack(side=tk.LEFT)

    def get_selected_order(self):
        sel = self.admin_orders_tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ из таблицы!", parent=self.win)
            return None
        oid = int(sel[0])
        return next((o for o in self.app.orders if o["id"] == oid), None)

    def confirm_order(self):
        order = self.get_selected_order()
        if not order:
            return
        if order["status"] != "Новый":
            messagebox.showinfo("Информация", f"Заказ уже имеет статус «{order['status']}».", parent=self.win)
            return
        order["status"] = "В работе"
        self.app.broadcast_update()
        messagebox.showinfo("Подтверждено", f"Заказ №{order['id']} подтвержден и передан на кухню (статус: «В работе»).", parent=self.win)

    def reject_order(self):
        order = self.get_selected_order()
        if not order:
            return
        order["status"] = "Отклонен"
        self.app.broadcast_update()

    def issue_invoice(self):
        order = self.get_selected_order()
        if not order:
            return

        inv_win = tk.Toplevel(self.win)
        inv_win.title(f"Формирование счета — Заказ №{order['id']}")
        inv_win.geometry("360x220")
        inv_win.grab_set()

        tk.Label(inv_win, text=f"Электронный счет для заказа №{order['id']}", font=("Arial", 11, "bold")).pack(pady=10)
        tk.Label(inv_win, text="Сумма к оплате (руб.):").pack()
        sum_entry = tk.Entry(inv_win, font=("Arial", 11), justify="center")
        sum_entry.insert(0, f"{order['final_total']:.2f}")
        sum_entry.pack(pady=5)

        paid_var = tk.BooleanVar(value=order["paid"])
        tk.Checkbutton(inv_win, text="Счет оплачен", variable=paid_var).pack(pady=5)

        def save_invoice():
            try:
                val = float(sum_entry.get().replace(",", "."))
                if val < 0:
                    raise ValueError
                order["final_total"] = val
                order["paid"] = paid_var.get()
                inv_win.destroy()
                self.app.broadcast_update()
                messagebox.showinfo("Счет", "Электронный счет сформирован и обновлен!", parent=self.win)
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную неотрицательную сумму!", parent=self.win)

        tk.Button(inv_win, text="Сохранить и выставить счет", bg="#1565c0", fg="white", command=save_invoice).pack(pady=12)

    def delete_order_item(self):
        order = self.get_selected_order()
        if not order:
            return
        if order["status"] != "Новый":
            messagebox.showerror("Запрещено", "Удалить позицию можно только из заказа со статусом «Новый» (до отправки на кухню)!", parent=self.win)
            return
        if not order["items"]:
            return

        del_win = tk.Toplevel(self.win)
        del_win.title("Удаление позиции из заказа")
        del_win.geometry("360x240")
        del_win.grab_set()

        tk.Label(del_win, text="Выберите позицию для удаления:", font=("Arial", 10, "bold")).pack(pady=8)
        lb = tk.Listbox(del_win, font=("Arial", 10))
        lb.pack(fill=tk.BOTH, expand=True, padx=15)
        for idx, it in enumerate(order["items"]):
            lb.insert(tk.END, f"{it['name']} x{it['qty']} ({it['price']*it['qty']:.2f} руб.)")

        def confirm_del():
            cur = lb.curselection()
            if not cur:
                return
            idx = cur[0]
            removed = order["items"].pop(idx)
            order["final_total"] = max(0.0, order["final_total"] - removed["price"] * removed["qty"])
            del_win.destroy()
            self.app.broadcast_update()

        tk.Button(del_win, text="Удалить выбранную позицию", bg="#c62828", fg="white", command=confirm_del).pack(pady=10)

    def add_new_menu_row(self):
        if self.new_row_id is not None:
            messagebox.showwarning("Внимание", "Сначала завершите заполнение новой строки!", parent=self.win)
            return
        self.new_row_id = f"new_{self.app.next_menu_id}"
        self.admin_menu_tree.insert("", tk.END, iid=self.new_row_id, values=("", "", "", "", "Нет"))
        self.start_cell_edit(self.new_row_id, 0)

    def on_double_click_cell(self, event):
        region = self.admin_menu_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.admin_menu_tree.identify_row(event.y)
        col_str = self.admin_menu_tree.identify_column(event.x)
        col_idx = int(col_str.replace("#", "")) - 1

        if not row_id.startswith("new_"):
            dish_id = int(row_id)
            if self.app.is_dish_in_active_orders(dish_id):
                messagebox.showerror("Блокировка", "Нельзя изменять блюдо, которое находится в активном заказе клиента!", parent=self.win)
                return

        self.start_cell_edit(row_id, col_idx)

    def start_cell_edit(self, row_id, col_idx):
        if self.active_editor:
            self.active_editor.destroy()
            self.active_editor = None

        col_id = f"#{col_idx + 1}"
        bbox = self.admin_menu_tree.bbox(row_id, col_id)
        if not bbox:
            return

        x, y, w, h = bbox
        current_vals = list(self.admin_menu_tree.item(row_id, "values"))

        entry = tk.Entry(self.admin_menu_tree, font=("Arial", 10), bg="white")
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, current_vals[col_idx])
        entry.select_range(0, tk.END)
        entry.focus_set()
        self.active_editor = entry

        def validate_and_commit(move_next=False):
            val = entry.get().strip()
            current_vals[col_idx] = val
            self.admin_menu_tree.item(row_id, values=current_vals)

            if col_idx == 4 or not move_next:
                if self.validate_and_save_row(row_id, current_vals, entry):
                    entry.destroy()
                    self.active_editor = None
            else:
                entry.destroy()
                self.active_editor = None
                self.start_cell_edit(row_id, col_idx + 1)

        entry.bind("<Tab>", lambda e: (validate_and_commit(move_next=True), "break"))
        entry.bind("<Return>", lambda e: validate_and_commit(move_next=False))
        entry.bind("<Escape>", lambda e: (entry.destroy(), setattr(self, "active_editor", None)))

    def validate_and_save_row(self, row_id, vals, entry_widget):
        name, price_str, weight, desc, stop_str = vals

        if not name:
            entry_widget.config(bg="#ffcdd2")
            messagebox.showerror("Ошибка валидации", "Название блюда не может быть пустым!", parent=self.win)
            return False

        try:
            price = float(price_str.replace(",", "."))
            if price <= 0:
                raise ValueError
        except ValueError:
            entry_widget.config(bg="#ffcdd2")
            messagebox.showerror("Ошибка валидации", "Некорректная стоимость блюда (должна быть больше 0)!", parent=self.win)
            return False

        is_stop = stop_str.lower() in ("да", "yes", "true", "1", "+")

        if row_id.startswith("new_"):
            new_dish = {
                "id": self.app.next_menu_id,
                "name": name,
                "price": price,
                "weight": weight or "100 г",
                "desc": desc or "Состав не указан",
                "stop": is_stop,
            }
            self.app.next_menu_id += 1
            self.app.menu.append(new_dish)
            self.new_row_id = None
        else:
            dish_id = int(row_id)
            dish = next((d for d in self.app.menu if d["id"] == dish_id), None)
            if dish:
                dish["name"] = name
                dish["price"] = price
                dish["weight"] = weight
                dish["desc"] = desc
                dish["stop"] = is_stop

        self.app.broadcast_update()
        return True

    def refresh_all(self):
        for item in self.admin_orders_tree.get_children():
            self.admin_orders_tree.delete(item)
        for o in self.app.orders:
            items_str = ", ".join(f"{i['name']} x{i['qty']}" for i in o["items"])
            paid_str = "Оплачен" if o["paid"] else "Не оплачен"
            self.admin_orders_tree.insert("", tk.END, iid=str(o["id"]), values=(o["id"], f"{o['table']} ({o['client']})", items_str, f"{o['final_total']:.2f}", o["status"], paid_str))

        if self.new_row_id is None:
            for item in self.admin_menu_tree.get_children():
                self.admin_menu_tree.delete(item)
            for d in self.app.menu:
                stop_txt = "Да" if d["stop"] else "Нет"
                self.admin_menu_tree.insert("", tk.END, iid=str(d["id"]), values=(d["name"], f"{d['price']:.2f}", d["weight"], d["desc"], stop_txt))

        self.embedded_client.refresh_all()


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ОКНО ПОВАРА
class ChefWindow:
    def __init__(self, app: RestaurantSystem, user_name: str):
        self.app = app
        self.user_name = user_name
        self.win = tk.Toplevel(app.root)
        self.win.title(f"Интерфейс Повара (Кухня) — {user_name}")
        self.win.geometry("780x480")

        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        header = tk.Frame(self.win, bg="#f4acac", padx=15, pady=10)
        header.pack(fill=tk.X)
        tk.Label(header, text="Кухонный монитор (KDS) — Подтвержденные заказы", fg="white", bg="#37474f", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        cols = ("id", "table", "items", "status")
        self.chef_tree = ttk.Treeview(self.win, columns=cols, show="headings", height=14)
        self.chef_tree.heading("id", text="№ Заказа")
        self.chef_tree.heading("table", text="Стол")
        self.chef_tree.heading("items", text="Состав заказа (блюда и количество)")
        self.chef_tree.heading("status", text="Статус приготовления")

        self.chef_tree.column("id", width=80, anchor="center")
        self.chef_tree.column("table", width=100, anchor="center")
        self.chef_tree.column("items", width=380)
        self.chef_tree.column("status", width=180, anchor="center")
        self.chef_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.win, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Принять в работу («В процессе приготовления»)", bg="#ef6c00", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self.set_status("В процессе приготовления")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5), ipady=5)

        tk.Button(btn_frame, text="Готово к выдаче", bg="#2e7d32", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self.set_status("Готово к выдаче")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0), ipady=5)

    def set_status(self, new_status):
        sel = self.chef_tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ из списка!", parent=self.win)
            return
        oid = int(sel[0])
        order = next((o for o in self.app.orders if o["id"] == oid), None)
        if order:
            order["status"] = new_status
            self.app.broadcast_update()

    def refresh_all(self):
        for item in self.chef_tree.get_children():
            self.chef_tree.delete(item)

        kitchen_statuses = {"В работе", "Подтвержден", "В процессе приготовления", "Готово к выдаче"}
        for o in self.app.orders:
            if o["status"] in kitchen_statuses:
                items_str = ", ".join(f"{i['name']} — {i['qty']} шт." for i in o["items"])
                self.chef_tree.insert("", tk.END, iid=str(o["id"]), values=(o["id"], o["table"], items_str, o["status"]))


if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantSystem(root)
    root.mainloop()