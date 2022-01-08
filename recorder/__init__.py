import logging

import sys
import threading

__version__ = "0.1"

handlers = [logging.StreamHandler(stream=sys.stdout)]
logging.basicConfig(level=logging.DEBUG,
                    format="[%(levelname)s] %(name)s %(thread)s %(message)s",
                    handlers=handlers)

logging.getLogger("pydub").setLevel(logging.INFO)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger().error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def handle_thread_exception(args):
    logging.getLogger().error("Uncaught exception in Thread",
                              exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


sys.excepthook = handle_exception
threading.excepthook = handle_thread_exception
