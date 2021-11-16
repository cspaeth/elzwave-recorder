import pyaudio
import os

AUDIO_CHUNK_SIZE = 1024
AUDIO_BIT_RATE = pyaudio.paInt16  # 16 Bit
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
AUDIO_PRERECORD_LENGTH = 30  # Sec
AUDIO_DEVICE = "KT-USB"

RECORD_DIR = "./record"
PROCESS_DIR = "./record"

DROPBOX_DEFAULT_DIR = "/default"
DROPBOX_TOKEN = os.environ.get('DROPBOX_TOKEN', None)

API_URL = "https://stage.elzwave.de/api/recorder/"
API_TOKEN = os.environ.get('API_TOKEN', None)
