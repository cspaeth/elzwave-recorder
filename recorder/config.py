import pyaudio
import os

AUDIO_CHUNK_SIZE = int(os.environ.get('AUDIO_BUFFER_SIZE', 4096))
AUDIO_BIT_RATE = int(os.environ.get('AUDIO_BITRATE', pyaudio.paInt24))

AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', 48000))
AUDIO_CHANNELS = 2
AUDIO_PRERECORD_LENGTH = 30  # Sec
AUDIO_DEVICE = os.environ.get('AUDIO_DEVICE', None)

LOG_TARGET = None

if os.environ.get('LOG_TARGET', None):
    host, port = os.environ.get('LOG_TARGET').split(':')
    LOG_TARGET = (host, int(port))
    print(f"Logging to: {LOG_TARGET}")

RECORD_DIR = "./record"
PROCESS_DIR = "./record"

DROPBOX_DEFAULT_DIR = "/default"
DROPBOX_TOKEN = os.environ.get('DROPBOX_TOKEN', None)

API_URL = os.environ.get('API_URL', "https://stage.elzwave.de/api/recorder/")
API_TOKEN = os.environ.get('API_TOKEN', None)
