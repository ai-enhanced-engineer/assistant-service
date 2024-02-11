import logging


def configure_logger(level="INFO", logger=None):
    """
    Configures a simple console logger with the givel level.
    A usecase is to change the formatting of the default handler of the root logger
    """
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logger or logging.getLogger()  # either the given logger or the root logger
    logger.setLevel(level)
    # If the logger has handlers, we configure the first one. Otherwise we add a handler and configure it
    if logger.handlers:
        console = logger.handlers[0]  # we assume the first handler is the one we want to configure
    else:
        console = logging.StreamHandler()
        logger.addHandler(console)
    console.setFormatter(formatter)
    console.setLevel(level)
