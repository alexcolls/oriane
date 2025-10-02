import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("InstagramTests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("FastAPI application is starting...")

class CustomFormatter(logging.Formatter):
    '''
    Custom log formatter that includes milliseconds in the timestamp.
    '''
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.fromtimestamp(record.created).strftime(datefmt)
        else:
            t = datetime.fromtimestamp(record.created)
            s = t.strftime("%Y-%m-%d %H:%M:%S")
            s = f"{s}.{int(record.msecs):03d}"
        return s

def setup_logging(debug: bool, store_logs: bool, keep_history: bool, milliseconds: bool = True) -> None:
    '''
    Configures logging settings with options for file naming based on history preservation 
    and timestamp detail.
    
    - Args:
        debug (bool): If False, disables all logging output.
        store_logs (bool): If False, logs will not be written to files, only printed to console.
        keep_history (bool): Determines whether to keep previous log files or overwrite them.
                             True will create a new log file with a sequential number each time 
                             the program is executed, preventing overwriting of old log files.
                             False will always overwrite the single log file 'main.log'.
        milliseconds (bool): Determines whether to include milliseconds in the log timestamps.
                             True includes milliseconds, False omits them.
                             
    Creates logs in the 'logs' directory within the current working directory.
    This function must be called before any logging occurs in the application to ensure all logs are handled 
    and formatted correctly.
    '''
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory) 
    handlers = []
    if store_logs:
        if keep_history:
            existing_logs = [log for log in os.listdir(log_directory) if log.endswith(".log") and log.split('.')[0].isdigit()]
            existing_numbers = sorted([int(log.split('.')[0]) for log in existing_logs])
            next_log_number = existing_numbers[-1] + 1 if existing_numbers else 0
            file_name = f"{log_directory}/{next_log_number}.log"
            file_mode = 'a'
        else:
            file_name = f"{log_directory}/main.log"
            file_mode = 'w'
        file_handler = logging.FileHandler(file_name, mode=file_mode)
        handlers.append(file_handler)    
    handlers.append(logging.StreamHandler())
    date_format = "%Y-%m-%d %H:%M:%S" if not milliseconds else "%Y-%m-%d %H:%M:%S.%f"
    formatter = CustomFormatter("%(asctime)s - %(levelname)s - %(message)s", datefmt=date_format)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt=date_format,
        handlers=handlers
    )
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    if not debug:
        # Disable all logging output if debug is False.
        logging.disable(logging.CRITICAL)

def log(message: str, level: str = 'info') -> None:
    '''
    Logs a message at the specified level.
    - Args:
        message (str): The message to be logged.
        level (str): The severity level of the log message. Default is 'info'.
                     Other levels include 'debug', 'warning', 'error', and 'critical'.
    '''
    if level.lower() == 'debug':
        logging.debug(message)
    elif level.lower() == 'warning':
        logging.warning(message)
    elif level.lower() == 'error':
        logging.error(message)
    elif level.lower() == 'critical':
        logging.critical(message)
    else:
        logging.info(message)

def print_dict(dictionary: dict) -> None:
    '''
    Prints the contents of a dictionary to the console.
    - Args:
        dictionary (dict): The dictionary to be printed.
    '''
    for key, value in dictionary.items():
        print(f"{key}: {value}")
