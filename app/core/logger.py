from loguru import logger

# Can be used to delete the provided config by default
# logger.remove(0)

# Can be added more, like rotation and compression
logger.add(
    "logs/app.log",
    level="DEBUG",
    encoding="utf-8",
    enqueue=True,  # For async
    backtrace=True,  # For detailed errors
    diagnose=True,  # For detailed errors
)
