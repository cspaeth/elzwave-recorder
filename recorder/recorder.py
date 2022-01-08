import os
from builtins import PermissionError
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from threading import Thread, Lock, Event
import dropbox
import pyaudio
import wave
import requests
from pyaudio import Stream, get_sample_size
import logging
from pydub import effects, AudioSegment
from recorder import config

log = logging.getLogger("recorder")

BUFFER_SIZE = int(config.AUDIO_SAMPLE_RATE / config.AUDIO_CHUNK_SIZE * config.AUDIO_PRERECORD_LENGTH)

API_HEADERS = {'Authorization': f'Token {config.API_TOKEN}'}


@dataclass
class SessionContext:
    upload_path: str
    title: str = None
    id: int = None


class NoDeviceFoundException(Exception):
    pass


class CaptureCycle:
    stream: Stream
    buffer: deque = None

    keep_prerecording: bool = False
    filename: str  # = None

    start_capture: Event
    end_capture: Event
    started: Event
    completed: Event

    def __init__(self, stream):
        self.stream = stream
        self.start_capture = Event()
        self.started = Event()
        self.end_capture = Event()
        self.completed = Event()

    def capture(self):
        try:
            self.pre_record()
            self.compute_filename()
            self.started.set()
            self.record()
            self.completed.set()
        finally:
            self.stream.stop_stream()
            self.stream.close()

    def record(self):
        log.info(f"Recording to {self.filename}")
        with self.wave_out(self.filename) as out:
            if self.keep_prerecording:
                out.writeframes(b''.join(self.buffer))

            while not self.end_capture.is_set():
                out.writeframes(self.stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False))
        log.debug(f"Finished Recording {self.filename}")

    def pre_record(self):
        self.buffer = deque(maxlen=BUFFER_SIZE)
        while not self.start_capture.is_set():
            self.buffer.append(self.stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False))
        log.debug("Done Buffering")

    def compute_filename(self):
        i = 0
        candidate = os.path.join(config.RECORD_DIR, f'{datetime.now():%Y-%m-%d_%H-%M}.wav')
        while os.path.exists(candidate):
            i += 1
            candidate = os.path.join(config.RECORD_DIR, f'{datetime.now():%Y-%m-%d_%H-%M}-{i}.wav')

        self.filename = candidate
        log.debug(f"Computed filename: {self.filename}")

    @staticmethod
    def wave_out(filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(config.AUDIO_CHANNELS)
        wf.setsampwidth(get_sample_size(config.AUDIO_BIT_RATE))
        wf.setframerate(config.AUDIO_SAMPLE_RATE)
        return wf


class CaptureThread(Thread):

    pyaudio: pyaudio.PyAudio
    cycle: CaptureCycle
    ready: bool = False

    def run(self):
        log.info(f"Starting Recorder ({config.AUDIO_SAMPLE_RATE}/{config.AUDIO_BIT_RATE}, {config.AUDIO_CHANNELS} Ch)")
        self.pyaudio = pyaudio.PyAudio()
        self.check_directory_permission()
        self.ready = True

        try:
            while True:
                self.cycle = CaptureCycle(self.open_audio_stream())
                self.cycle.capture()
        finally:
            log.error("Thread done")

    def start_recording(self, keep_prerecording):
        cycle = self.cycle
        if cycle.started.is_set():
            log.warning("Could not start recording, cycle already started")
            return

        cycle.keep_prerecording = keep_prerecording
        cycle.start_capture.set()
        log.debug("Waiting for capture to start")
        cycle.started.wait()
        log.debug("start_recording done")

    def stop_recording(self):
        cycle = self.cycle
        if not cycle.started.is_set():
            log.warning("Could not stop recording, cycle not started")
            return

        cycle.end_capture.set()
        log.debug("Waiting for capture to complete")
        cycle.completed.wait()
        log.debug(f"Completed capture of {cycle.filename}")
        return cycle.filename

    @staticmethod
    def check_directory_permission():
        if not os.access(config.RECORD_DIR, os.W_OK):
            raise PermissionError(f"PermissionDenied: '{config.RECORD_DIR}' is not writable")

    def open_audio_stream(self):
        return self.pyaudio.open(input=True,
                                 format=config.AUDIO_BIT_RATE,
                                 channels=config.AUDIO_CHANNELS,
                                 rate=config.AUDIO_SAMPLE_RATE,
                                 input_device_index=self.find_device(),
                                 frames_per_buffer=config.AUDIO_CHUNK_SIZE)

    def find_device(self):
        devices = self.pyaudio.get_host_api_info_by_index(0)

        for index in range(0, devices.get('deviceCount')):
            device_info = self.pyaudio.get_device_info_by_host_api_device_index(0, index)
            if device_info.get('maxInputChannels') < config.AUDIO_CHANNELS:
                log.debug(f"Ignoring device '{device_info.get('name')}', to few input channels")
                continue

            log.info(f"Using device {index}: {device_info.get('name')}")
            return index

        raise NoDeviceFoundException()


class Status(str, Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"


class SessionRecorder:
    recorder: CaptureThread
    context: SessionContext
    processing: Lock

    def __init__(self):
        self.context = SessionContext(upload_path=config.DROPBOX_DEFAULT_DIR)
        self.processing = Lock()
        self.recorder = CaptureThread(daemon=True)

        self.recorder.start()

    def record(self, pre_capture=False):
        self.recorder.start_recording(pre_capture)
        self.update_session_context()

    def stop(self, canceled=False):
        filename = self.recorder.stop_recording()

        if canceled:
            log.debug("Capture canceled")
            return

        if filename:
            log.debug("Starting post processing thread")
            Thread(target=self.post_process, args=(filename, self.context)).start()
        else:
            log.warning("Stop recording didn't yield filename")

    def update_session_context(self):
        if not config.API_TOKEN:
            log.info("No API_TOKEN configured - using default profile")
            return

        result = requests.get(config.API_URL, headers=API_HEADERS)
        if result.status_code == 200:
            data = result.json()
            self.context = SessionContext(upload_path=data['path'], id=data['id'])
        else:
            self.context = SessionContext(upload_path=config.DROPBOX_DEFAULT_DIR)

    def post_process(self, source_file: str, context: SessionContext):
        log.info(f"File {source_file} scheduled for processing")
        with self.processing:
            log.info(f"Processing file {source_file}")
            processed_file = self.convert(source_file)
            log.info(f"Done processing, exported to {processed_file}")
            self.upload(processed_file, context.upload_path)
            self.notify(context)

        log.debug("Post processing finished")

    @staticmethod
    def notify(context: SessionContext):
        if config.API_TOKEN and context.id:
            log.debug(f"Notifying {config.API_URL}")
            requests.post(config.API_URL, headers=API_HEADERS, data={'id': context.id})

    @staticmethod
    def convert(source: str) -> str:
        raw = AudioSegment.from_file(source)
        log.info(f"File {source} loaded (length = {int(raw.duration_seconds)}s)")
        filename = os.path.basename(source)
        target = os.path.join(config.PROCESS_DIR, os.path.splitext(filename)[0] + ".mp3")
        log.info(f"Normalizing {source}")
        normalized = effects.normalize(raw)
        log.info(f"Exporting {target}")
        normalized.export(target, format='mp3')
        return target

    @staticmethod
    def upload(file, path):
        if not config.DROPBOX_TOKEN:
            log.info("No dropbox token configured - skipping upload ")
            return

        log.debug(f"Uploading {file} to {path}")
        filename = os.path.basename(file)

        with dropbox.Dropbox(config.DROPBOX_TOKEN) as db:
            with open(file, 'rb') as f:
                db.files_upload(f.read(), os.path.join(path, filename))
            log.info(f"Upload Completed ({file} to {path})")

    def get_status(self):
        if not self.recorder.ready:
            return Status.INITIALIZING

        if self.is_recording():
            return Status.RECORDING

        if self.processing.locked():
            return Status.PROCESSING

        return Status.READY

    def is_recording(self):
        return self.recorder.cycle.started.is_set()
        
    def is_alive(self):
        return self.recorder.is_alive()
