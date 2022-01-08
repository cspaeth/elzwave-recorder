import logging
from gpiozero import Button, RGBLED
from .recorder import SessionRecorder, Status
from time import sleep


log = logging.getLogger("recorder")

STATES = {
    Status.INITIALIZING: lambda led: setattr(led, 'value', (1, 1, 0)),
    Status.PROCESSING: lambda led: led.blink(off_time=1.3, on_time=0.2, on_color=(1, 1, 0), off_color=(0, 1, 0)),
    Status.RECORDING: lambda led: led.blink(off_time=0.5, on_time=0.5, on_color=(1, 0, 0)),
    Status.READY: lambda led: setattr(led, 'value', (0, 1, 0))
}


class StatusHandler:
    led: RGBLED
    recorder: SessionRecorder
    status: Status = None

    def __init__(self, target):
        self.led = RGBLED(17, 18, 4, active_high=False)
        self.recorder = target
        self.update_status()

    def update_status(self):
        new_status = recorder.get_status()
        if new_status != self.status:
            log.debug(f"Changing state to: {new_status}")
            STATES[new_status](self.led)
            self.status = new_status


class ButtonHandler:
    triggered: bool = False

    def button_held(self):
        self.triggered = True
        self.action(long=True)

    def button_released(self):
        if not self.triggered:
            self.action()
        
        self.triggered = False
        
    def __init__(self, action):
        self.button = Button(2, hold_time=1.5)
        self.button.when_held = self.button_held
        self.button.when_released = self.button_released
        self.action = action


if __name__ == '__main__':
    log.info("Starting up Elzwave session recorder")

    def toggle_record(long=False):
        log.debug(f"toggle_record(long={long})")
        if not recorder.is_recording():
            recorder.record(pre_capture=long)
        else:
            recorder.stop(canceled=long)

        status.update_status()

    recorder = SessionRecorder()
    button = ButtonHandler(toggle_record)
    status = StatusHandler(recorder)

    while recorder.is_alive():
        sleep(1)
        status.update_status()
