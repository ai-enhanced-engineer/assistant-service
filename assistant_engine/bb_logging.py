import logging

LEVEL = "INFO"
FORMATTER = logging.Formatter(fmt="%(asctime)s: %(levelname)s: %(name)s: %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")


class OpenAIFilter(logging.Filter):
    def filter(self, record):
        # print(f"Filtering record: {record.msg}")
        return not record.getMessage().startswith("HTTP Request:")


def configure_root_logger():
    logger = logging.getLogger()
    handler = logger.handlers[0]
    handler.setFormatter(FORMATTER)
    handler.addFilter(OpenAIFilter())
    handler.setLevel(LEVEL)


def get_logger(name):
    return logging.getLogger(name)


configure_root_logger()
