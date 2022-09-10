import os
import sys
import logging

try:
    import sonos_settings
except ImportError:
    sys.exit(1)

_LOGGER = logging.getLogger(__name__)


def setup_logging():
    """Set up logging facilities for the script."""
    log_level = getattr(sonos_settings, "log_level", logging.INFO)
    log_file = getattr(sonos_settings, "log_file", None)
    if log_file:
        log_path = os.path.expanduser(log_file)
    else:
        log_path = None

    fmt = "%(asctime)s %(levelname)7s - %(message)s"
    logging.basicConfig(format=fmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    if log_path is None:
        return

    _LOGGER.info("Writing to log file: %s", log_path)
    logfile_handler = logging.FileHandler(log_path, mode="a")

    logfile_handler.setLevel(log_level)
    logfile_handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger("")
    logger.addHandler(logfile_handler)
