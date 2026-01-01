import time
import pickle
import threading
from pynput import mouse, keyboard

# Автор: qwww.ru
# Версия: 1.0
# Сайт: https://qwww.ru

class ActionRecorder:
    def __init__(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.actions = []
        self.start_time = time.time()
        self.stop_flag = threading.Event()

    def on_click(self, x, y, button, pressed):
        if self.stop_flag.is_set():
            return False
        action = {
            'type': 'click',
            'position': (x, y),
            'button': button,
            'pressed': pressed,
            'time': time.time() - self.start_time
        }
        self.actions.append(action)
        print(f"Recorded click at {(x, y)} with button {button} {'pressed' if pressed else 'released'}")

    def on_press(self, key):
        if self.stop_flag.is_set():
            return False
        # ОСНОВНОЕ ИСПРАВЛЕНИЕ: не записываем Esc, а останавливаем запись
        if key == keyboard.Key.esc:
            self.stop()
            return False  # ← не добавляем в действия!
        # Записываем только обычные клавиши
        action = {
            'type': 'keypress',
            'key': key,
            'time': time.time() - self.start_time
        }
        self.actions.append(action)
        print(f"Recorded keypress: {key}")

    def start_recording(self, delay):
        print(f"Recording will start in {delay} seconds...")
        time.sleep(delay)
        print("Recording started. Press 'esc' to stop.")
        self.start_time = time.time()
        self.mouse_listener.start()
        self.keyboard_listener.start()

        while not self.stop_flag.is_set():
            time.sleep(0.1)

        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.save_actions()

    def save_actions(self):
        with open('actions.pkl', 'wb') as f:
            pickle.dump(self.actions, f)
        print("Recording stopped and saved to actions.pkl.")

    def stop(self):
        self.stop_flag.set()


class ActionPlayer:
    def __init__(self, repetitions):
        self.repetitions = repetitions
        self.stop_flag = threading.Event()

    def play_actions(self, delay):
        with open('actions.pkl', 'rb') as f:
            actions = pickle.load(f)
        mouse_controller = mouse.Controller()
        keyboard_controller = keyboard.Controller()

        print(f"Playback will start in {delay} seconds...")
        time.sleep(delay)
        print(f"Playing actions {self.repetitions} times. Press 'esc' to stop.")

        try:
            for _ in range(self.repetitions):
                start_time = time.time()
                for action in actions:
                    if self.stop_flag.is_set():
                        raise KeyboardInterrupt
                    elapsed = time.time() - start_time
                    if action['time'] > elapsed:
                        time.sleep(action['time'] - elapsed)
                    if action['type'] == 'click':
                        mouse_controller.position = action['position']
                        if action['pressed']:
                            mouse_controller.press(action['button'])
                        else:
                            mouse_controller.release(action['button'])
                        print(f"Clicking at {action['position']} with button {action['button']} {'pressed' if action['pressed'] else 'released'}")
                    elif action['type'] == 'keypress':
                        print(f"Pressing key: {action['key']}")
                        keyboard_controller.press(action['key'])
                        keyboard_controller.release(action['key'])
        except KeyboardInterrupt:
            print("\nPlayback interrupted by user.")

    def stop(self):
        self.stop_flag.set()


# Глобальный обработчик для остановки воспроизведения (не для записи!)
def on_press_global(key):
    if key == keyboard.Key.esc:
        global recorder, player
        if player is not None:
            player.stop()
        # При записи остановка идёт через ActionRecorder.on_press, не через этот обработчик


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Record and play mouse and keyboard actions.')
    parser.add_argument('--record', action='store_true', help='Record actions')
    parser.add_argument('--play', type=int, help='Play actions N times')
    parser.add_argument('--delay', type=int, default=5, help='Delay in seconds before starting recording or playback')
    args = parser.parse_args()

    recorder = None
    player = None

    # Запускаем глобальный слушатель ТОЛЬКО для воспроизведения
    global_listener = keyboard.Listener(on_press=on_press_global)
    # Но запускаем его всегда (без вреда), т.к. при записи он ничего не делает
    global_listener.start()

    if args.record:
        recorder = ActionRecorder()
        recorder.start_recording(args.delay)
    elif args.play:
        player = ActionPlayer(args.play)
        player.play_actions(args.delay)

    global_listener.stop()
