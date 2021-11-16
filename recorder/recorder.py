import os

from datetime import datetime
from dataclasses import dataclass
from threading import Thread

import dropbox
import pyaudio
import wave

import requests
from pyaudio import Stream
import logging

from pydub import effects, AudioSegment

from recorder import config

log = logging.getLogger(__name__)


PREBUFFER_SIZE = config.AUDIO_SAMPLE_RATE / config.AUDIO_CHUNK_SIZE * config.AUDIO_PRERECORD_LENGTH

API_HEADERS = {'Authorization': f'Token {config.API_TOKEN}'}


@dataclass
class SessionContext:
    upload_path: str
    title: str = None
    id: int = None


class CaptureThread(Thread):
    recording: bool = False
    keep_prerecording: bool = False

    filename: str

    pyaudio: pyaudio.PyAudio
    input: Stream

    def run(self):
        self.pyaudio = pyaudio.PyAudio()

        while True:
            self.capture_file()

        # self.pyaudio.close()

    def capture_file(self):
        stream = self.pyaudio.open(input=True,
                                   format=config.AUDIO_BIT_RATE,
                                   channels=config.AUDIO_CHANNELS,
                                   rate=config.AUDIO_SAMPLE_RATE,
                                   input_device_index=self.find_device(),
                                   frames_per_buffer=config.AUDIO_CHUNK_SIZE)

        prerecord_buffer = self.pre_record(stream)
        self.compute_filename()
        self.record(prerecord_buffer, stream)

        stream.stop_stream()
        stream.close()

    def record(self, prerecord_buffer, stream):
        print(f"Recording to {self.filename}")
        with self.wave_out(self.filename) as out:
            if self.keep_prerecording:
                self.keep_prerecording = False
                out.writeframes(b''.join(prerecord_buffer))

            while self.recording:
                out.writeframes(stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False))

    def pre_record(self, stream):
        print("Buffering")
        prerecord_buffer = []
        while not self.recording:
            data = stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False)
            prerecord_buffer.append(data)
            if len(prerecord_buffer) > PREBUFFER_SIZE:
                prerecord_buffer.pop(0)
        return prerecord_buffer

    def compute_filename(self):
        i = 0
        candidate = os.path.join(config.RECORD_DIR, f'{datetime.now():%Y-%m-%d_%H-%M}.wav')
        while os.path.exists(candidate):
            i += 1
            candidate = os.path.join(config.RECORD_DIR, f'{datetime.now():%Y-%m-%d_%H-%M}-{i}.wav')

        self.filename = candidate

    def wave_out(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(config.AUDIO_CHANNELS)
        wf.setsampwidth(self.pyaudio.get_sample_size(config.AUDIO_BIT_RATE))
        wf.setframerate(config.AUDIO_SAMPLE_RATE)
        return wf

    def start_recording(self, keep_prerecording):
        self.keep_prerecording = keep_prerecording
        self.recording = True

    def stop_recording(self):
        self.recording = False
        # wait til done
        return self.filename

    def is_recording(self):
        return self.recording

    def find_device(self, ):
        devices = self.pyaudio.get_host_api_info_by_index(0)
        first = None
        for i in range(0, devices.get('deviceCount')):
            device_info = self.pyaudio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') < config.AUDIO_CHANNELS:
                continue  # Ignore interfaces with to few inputs
            if device_info.get('name').startswith(config.AUDIO_DEVICE):
                print(f"Found Device: {device_info.get('name')}")
                return i  # Found match - return index
            if first is None:
                print(f"Fallback Device: {device_info.get('name')}")
                first = i  # Remember first interface with enough input channels
        return first


class SessionRecorder:
    recoder: CaptureThread
    context: SessionContext

    def __init__(self):
        self.recoder = CaptureThread()
        self.recoder.start()
        self.context = SessionContext(upload_path=config.DROPBOX_DEFAULT_DIR)

    def record(self, pre_capture=False):
        if self.recoder.is_recording():
            return

        self.recoder.start_recording(pre_capture)
        self.update_session_context()

    def stop(self, canceld=False):
        if not self.recoder.is_recording():
            return

        recorded_file = self.recoder.stop_recording()

        if canceld:
            return

        Thread(target=self.post_process, args=(recorded_file, self.context)).start()

    def update_session_context(self):
        if not config.API_TOKEN:
            print("No API_TOKEN configured - using default profile")
            return

        result = requests.get(config.API_URL, headers=API_HEADERS)
        if result.status_code == 200:
            data = result.json()
            self.context = SessionContext(upload_path=data['path'], id=data['id'])
        else:
            self.context = SessionContext(upload_path=config.DROPBOX_DEFAULT_DIR)

    def post_process(self, source_file: str, context: SessionContext):
        processed_file = self.convert(source_file)
        self.upload(processed_file, context.upload_path)
        self.notify(context)

    def notify(self, context: SessionContext):
        if config.API_TOKEN and context.id:
            requests.post(config.API_URL, headers=API_HEADERS, data={'id': context.id})

    def convert(self, source: str) -> str:
        raw = AudioSegment.from_file(source)
        filename = os.path.basename(source)
        target = os.path.join(config.PROCESS_DIR, os.path.splitext(filename)[0] + ".mp3")
        print(f"Processing {source} to {target}")
        normalized = effects.normalize(raw)
        normalized.export(target, format='mp3')
        return target

    def upload(self, file, path):
        if not config.DROPBOX_TOKEN:
            print("No dropbox token configured - skipping upload ")
            return

        print(f"Uploading {file} to {path}")
        filename = os.path.basename(file)

        with dropbox.Dropbox(config.DROPBOX_TOKEN) as db:
            with open(file, 'rb') as f:
                db.files_upload(f.read(), os.path.join(path, filename))

    def is_recording(self):
        return self.recoder.is_recording()
