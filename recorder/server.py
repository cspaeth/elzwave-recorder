import logging
from logging.handlers import SysLogHandler

from signal import pause

from gpiozero import LED, Button

from recorder import config
from recorder.recorder import SessionRecorder

handlers=[logging.StreamHandler()]
if config.LOG_TARGET:
    handlers.append(SysLogHandler(address=config.LOG_TARGET))


logging.basicConfig(level=logging.INFO,
                    format="%(name)s:%(asctime)s %(thread)s [%(levelname)s] %(message)s",
                    handlers=handlers)

log = logging.getLogger("recorder")
recorder = SessionRecorder()
triggered = False


def main():
    def action(long=False):
        log.info(f"button pressed (long={long})")
        if not recorder.is_recording():
            recorder.record(pre_capture=long)
            status_led.blink(off_time=0.5, on_time=0.5)
        else:
            recorder.stop(canceld=long)
            status_led.on()

    def button_held():
        global triggered
        status_led.blink(off_time=0.1, on_time=0.1, n=4)
        triggered = True

    def button_released():
        global triggered

        if not triggered:
            log.info("Button pressed (short)")
            action()
        else:
            log.info("Button pressed (short)")
            action(long=True)
        triggered = False

    status_led = LED(17)
    button = Button(2, hold_time=2)
    status_led.on()
    button.when_held = button_held
    button.when_released = button_released

    pause()


if __name__ == '__main__':
    main()
