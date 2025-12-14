import logging
from functools import partial

import structlog

from v2g.core.config import settings


def add_logger_name(_, __, event_dict, fallback):
    record = event_dict.get('_record')
    if record is None:
        event_dict['logger'] = fallback
    else:
        event_dict['logger'] = record.name
    return event_dict


def configure_logging(logger_name):
    preprocessors = [
        structlog.contextvars.merge_contextvars,
        partial(add_logger_name, fallback=logger_name),
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='iso', utc=True),
    ]

    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
        preprocessors.append(structlog.processors.format_exc_info)
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log_level),
        processors=preprocessors + [renderer],
        logger_factory=structlog.PrintLoggerFactory(),
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=preprocessors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(settings.log_level)
