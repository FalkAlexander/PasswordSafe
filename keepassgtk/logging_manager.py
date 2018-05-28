import time
import datetime


class LoggingManager:
    debug = NotImplemented
    timestamp = NotImplemented
    date = NotImplemented

    #
    # Log Levels
    #

    def __init__(self, debug_mode):
        self.debug = debug_mode
        self.timestamp = time.time()
        self.date = datetime.datetime.fromtimestamp(self.timestamp).strftime(
            '%Y-%m-%d %H:%M:%S')

    def log_error(self, message):
        print("( " + self.date + " ):" + "\033[91m ERROR: \033[0m" + message)

    def log_warn(self, message):
        print("( " + self.date + " ):" + "\033[93m WARNING: \033[0m" + message)

    def log_trace(self, message, trace):
        print("( " + self.date + " ):" + "\033[94m TRACE: \033[0m" + message)
        print("\033[94m" + str(trace))

    def log_info(self, message):
        print("( " + self.date + " ):" + "\033[92m INFO: \033[0m" + message)

    def log_debug(self, message):
        if(self.debug):
            print("( " + self.date + " ):" + "\033[1m DEBUG: \033[0m" + message)