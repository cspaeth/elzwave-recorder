import pyaudio
import os

AUDIO_CHUNK_SIZE = int(os.environ.get('AUDIO_BUFFER_SIZE', 16384))
AUDIO_BIT_RATE = int(os.environ.get('AUDIO_BITRATE', pyaudio.paInt24))

AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', 48000))
AUDIO_CHANNELS = 2
AUDIO_PRERECORD_LENGTH = 31  # Sec

RECORD_DIR = os.environ.get('TEMP_DIR', "/media/usb0")
PROCESS_DIR = RECORD_DIR

DROPBOX_DEFAULT_DIR = "/default"
DROPBOX_TOKEN = os.environ.get('DROPBOX_TOKEN', None)

API_URL = os.environ.get('API_URL', "https://stage.elzwave.de/api/recorder/")
API_TOKEN = os.environ.get('API_TOKEN', None)
