import logging
import sys

COLOR_RESET = '\033[0m'
COLOR_CYAN = '\033[36m'
COLOR_GREEN = '\033[32m'
COLOR_YELLOW = '\033[33m'
COLOR_MAGENTA = '\033[35m'
COLOR_BLUE = '\033[34m'
COLOR_RED = '\033[31m'
COLOR_BOLD = '\033[1m'


class CustomFormatter(logging.Formatter):
    """Custom logging formatter that adds timestamps, component tags, and colors for terminal output."""

    def format(self, record):
        level_colors = {
            logging.DEBUG: '\033[90mDEBUG  \033[0m',
            logging.INFO: f'{COLOR_GREEN}INFO   {COLOR_RESET}',
            logging.WARNING: f'{COLOR_YELLOW}WARNING{COLOR_RESET}',
            logging.ERROR: f'{COLOR_RED}ERROR  {COLOR_RESET}',
            logging.CRITICAL: f'{COLOR_RED}{COLOR_BOLD}CRITICAL{COLOR_RESET}',
        }

        tag = level_colors.get(record.levelno, f'{record.levelname:<7}')
        name_colored = f'{COLOR_CYAN}{record.name:<18}{COLOR_RESET}'
        log_fmt = f'{COLOR_BOLD}%(asctime)s{COLOR_RESET} | {tag} | {name_colored} | %(message)s'

        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


def setup_logging(level=logging.INFO):
    """Configures root and application loggers to print structured colored logs to terminal stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    for logger_name in ('uvicorn', 'uvicorn.access', 'uvicorn.error', 'fastapi'):
        l = logging.getLogger(logger_name)
        l.handlers = [handler]
        l.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger instance for application components."""
    return logging.getLogger(name)
