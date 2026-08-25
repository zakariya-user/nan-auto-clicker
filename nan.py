import random
import threading
import tkinter as tk
from tkinter import ttk

import pyautogui
from pynput import keyboard


clicking = threading.Event()
stop_requested = threading.Event()
settings_lock = threading.Lock()
settings = {
    "mode": "Keyboard",
    "key": "f",
    "button": "left",
    "minimum": 55,
    "maximum": 65,
}

def click_loop():
    while not stop_requested.is_set():
        if not clicking.is_set():
            stop_requested.wait(0.05)
            continue

        with settings_lock:
            current = settings.copy()

        if current["mode"] == "Keyboard":
            pyautogui.press(current["key"])
        else:
            pyautogui.click(button=current["button"])

        delay = random.uniform(current["minimum"], current["maximum"])
        stop_requested.wait(delay / 1000)


def set_status(status_var, text):
    status_var.set(text)


def build_gui():
    root = tk.Tk()
    root.title("Auto Clicker")
    root.geometry("390x330")
    root.minsize(350, 300)
    root.resizable(True, True)

    mode_var = tk.StringVar(value="Keyboard")
    key_var = tk.StringVar(value="f")
    button_var = tk.StringVar(value="left")
    minimum_var = tk.StringVar(value="55")
    maximum_var = tk.StringVar(value="65")
    status_var = tk.StringVar(value="Stopped")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)
    ttk.Label(main, text="Auto Clicker", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ttk.Label(main, text="F6: start / stop    Esc: exit").pack(anchor="w", pady=(2, 14))

    click_frame = ttk.LabelFrame(main, text="Click options", padding=10)
    click_frame.pack(fill="x")
    ttk.Label(click_frame, text="Type:").grid(row=0, column=0, sticky="w", pady=3)
    ttk.Combobox(
        click_frame, textvariable=mode_var, values=("Keyboard", "Mouse"),
        state="readonly", width=14
    ).grid(row=0, column=1, sticky="w", padx=8, pady=3)
    ttk.Label(click_frame, text="Key:").grid(row=1, column=0, sticky="w", pady=3)
    key_entry = ttk.Entry(click_frame, textvariable=key_var, width=16)
    key_entry.grid(row=1, column=1, sticky="w", padx=8, pady=3)
    ttk.Label(click_frame, text="Mouse button:").grid(row=2, column=0, sticky="w", pady=3)
    button_menu = ttk.Combobox(
        click_frame, textvariable=button_var, values=("left", "right", "middle"),
        state="readonly", width=14
    )
    button_menu.grid(row=2, column=1, sticky="w", padx=8, pady=3)

    interval_frame = ttk.LabelFrame(main, text="Random interval (milliseconds)", padding=10)
    interval_frame.pack(fill="x", pady=12)
    ttk.Label(interval_frame, text="Minimum:").grid(row=0, column=0, sticky="w", pady=3)
    ttk.Entry(interval_frame, textvariable=minimum_var, width=10).grid(row=0, column=1, padx=8)
    ttk.Label(interval_frame, text="Maximum:").grid(row=0, column=2, sticky="w", pady=3)
    ttk.Entry(interval_frame, textvariable=maximum_var, width=10).grid(row=0, column=3, padx=8)
    ttk.Label(interval_frame, text="Each action uses a new random delay under 1000 ms.").grid(
        row=1, column=0, columnspan=4, sticky="w", pady=(7, 0)
    )

    status_row = ttk.Frame(main)
    status_row.pack(fill="x")
    ttk.Label(status_row, text="Status:").pack(side="left")
    ttk.Label(status_row, textvariable=status_var).pack(side="left", padx=6)

    def read_settings():
        mode = mode_var.get()
        key = key_var.get().strip().lower()
        if mode == "Keyboard" and not key:
            raise ValueError("Enter a keyboard key.")
        try:
            minimum = max(1, min(999, float(minimum_var.get())))
            maximum = max(1, min(999, float(maximum_var.get())))
        except ValueError as error:
            raise ValueError("Intervals must be numbers below 1000.") from error
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        with settings_lock:
            settings.update({
                "mode": mode, "key": key, "button": button_var.get(),
                "minimum": minimum, "maximum": maximum,
            })

    def toggle():
        if clicking.is_set():
            clicking.clear()
            set_status(status_var, "Stopped")
            return
        try:
            read_settings()
        except ValueError as error:
            set_status(status_var, str(error))
            return
        clicking.set()
        set_status(status_var, "Running")

    def close():
        stop_requested.set()
        clicking.clear()
        root.destroy()

    ttk.Button(main, text="Start / Stop (F6)", command=toggle).pack(fill="x", ipady=4, pady=(10, 0))
    root.protocol("WM_DELETE_WINDOW", close)
    return root, toggle, close, status_var


if __name__ == "__main__":
    root, toggle, close, status_var = build_gui()
    click_thread = threading.Thread(target=click_loop, daemon=True)
    click_thread.start()

    def on_release(key):
        if key == keyboard.Key.f6:
            root.after(0, toggle)
        elif key == keyboard.Key.esc:
            root.after(0, close)
            return False

    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    root.mainloop()
    listener.stop()