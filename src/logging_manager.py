import time
import datetime

debug = False
timestamp = time.time()
date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

#
# Log Levels
#

def log_error(message):
    print("( " + date + " ):" + "\033[91m ERROR: \033[0m" + message)

def log_warn(message):
    print("( " + date + " ):" + "\033[93m WARNING: \033[0m" + message)

def log_trace(message, trace):
    print("( " + date + " ):" + "\033[94m TRACE: \033[0m" + message)
    print("\033[94m" + str(trace))

def log_info(message):
    print("( " + date + " ):" + "\033[92m INFO: \033[0m" + message)

def log_debug(message):
    if(debug):
        print("( " + date + " ):" + "\033[1m DEBUG: \033[0m" + message)