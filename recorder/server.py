from signal import pause

from gpiozero import LED, Button
from flask import Flask

from recorder.recorder import SessionRecorder


#app = Flask(__name__)
recorder = SessionRecorder()


# @app.route("/")
# def index():
#     pass


triggered = False


def main():
    def action(long=False):
        print(f"button pressed (long={long})")
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
            print("Short")
            action()
        else:
            print("Long")
            action(long=True)
        triggered = False

    status_led = LED(17)
    button = Button(2, hold_time=2.5)
    status_led.on()
    button.when_held = button_held
    button.when_released = button_released

    pause()
    # app.run()


if __name__ == '__main__':
    main()
