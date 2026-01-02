import time
import pickle
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from pynput import mouse, keyboard

class DejaClickGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DejaClick GUI v1.0")
        self.root.geometry("400x500")

        self.actions = []
        self.stop_flag = threading.Event()
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        # Поля ввода
        tk.Label(self.root, text="Задержка перед стартом (сек):").pack(pady=5)
        self.delay_entry = tk.Entry(self.root)
        self.delay_entry.insert(0, "5")
        self.delay_entry.pack()

        tk.Label(self.root, text="Количество повторов (для игры):").pack(pady=5)
        self.repeat_entry = tk.Entry(self.root)
        self.repeat_entry.insert(0, "1")
        self.repeat_entry.pack()

        # Кнопки управления
        self.record_btn = tk.Button(self.root, text="Начать запись", bg="red", fg="white", 
                                   command=self.start_record_thread, width=20, height=2)
        self.record_btn.pack(pady=10)

        self.play_btn = tk.Button(self.root, text="Воспроизвести", bg="green", fg="white", 
                                 command=self.start_play_thread, width=20, height=2)
        self.play_btn.pack(pady=5)

        tk.Label(self.root, text="Лог событий:").pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, width=45)
        self.log_area.pack(padx=10, pady=5)
        
        tk.Label(self.root, text="Нажмите ESC для остановки", fg="gray").pack()

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    # --- Логика записи ---
    def on_click(self, x, y, button, pressed):
        if self.stop_flag.is_set(): return False
        self.actions.append({
            'type': 'click', 'position': (x, y), 'button': button,
            'pressed': pressed, 'time': time.time() - self.start_time
        })

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self.stop_flag.set()
            return False
        if not self.stop_flag.is_set():
            self.actions.append({
                'type': 'keypress', 'key': key, 'time': time.time() - self.start_time
            })

    def start_record_thread(self):
        if self.is_running: return
        threading.Thread(target=self.record_task, daemon=True).start()

    def record_task(self):
        self.is_running = True
        self.stop_flag.clear()
        self.actions = []
        
        delay = int(self.delay_entry.get())
        self.log(f"Запись начнется через {delay} сек...")
        time.sleep(delay)
        
        self.start_time = time.time()
        self.log("ЗАПИСЬ ИДЕТ... (ESC - стоп)")
        
        with mouse.Listener(on_click=self.on_click) as m_l, \
             keyboard.Listener(on_press=self.on_press) as k_l:
            while not self.stop_flag.is_set():
                time.sleep(0.1)
            m_l.stop()
            k_l.stop()

        with open('actions.pkl', 'wb') as f:
            pickle.dump(self.actions, f)
        
        self.log(f"Сохранено {len(self.actions)} действий.")
        self.is_running = False
        messagebox.showinfo("Готово", "Запись сохранена в actions.pkl")

    # --- Логика воспроизведения ---
    def start_play_thread(self):
        if self.is_running: return
        threading.Thread(target=self.play_task, daemon=True).start()

    def play_task(self):
        try:
            with open('actions.pkl', 'rb') as f:
                actions = pickle.load(f)
        except:
            messagebox.showerror("Ошибка", "Файл actions.pkl не найден!")
            return

        self.is_running = True
        self.stop_flag.clear()
        
        delay = int(self.delay_entry.get())
        repeats = int(self.repeat_entry.get())
        
        self.log(f"Старт через {delay} сек...")
        time.sleep(delay)

        m_ctrl = mouse.Controller()
        k_ctrl = keyboard.Controller()

        # Слушатель для ESC во время игры
        def escape_watch(key):
            if key == keyboard.Key.esc:
                self.stop_flag.set()
                return False
        
        esc_listener = keyboard.Listener(on_press=escape_watch)
        esc_listener.start()

        try:
            for i in range(repeats):
                if self.stop_flag.is_set(): break
                self.log(f"Цикл {i+1}/{repeats}")
                start_time = time.time()
                for action in actions:
                    if self.stop_flag.is_set(): break
                    
                    elapsed = time.time() - start_time
                    if action['time'] > elapsed:
                        time.sleep(action['time'] - elapsed)
                    
                    if action['type'] == 'click':
                        m_ctrl.position = action['position']
                        m_ctrl.press(action['button']) if action['pressed'] else m_ctrl.release(action['button'])
                    elif action['type'] == 'keypress':
                        k_ctrl.press(action['key'])
                        k_ctrl.release(action['key'])
            self.log("Воспроизведение завершено.")
        finally:
            esc_listener.stop()
            self.is_running = False

if __name__ == '__main__':
    root = tk.Tk()
    app = DejaClickGUI(root)
    root.mainloop()
