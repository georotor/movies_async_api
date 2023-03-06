import asyncio
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


class BackoffError(Exception):
    """Вызывается когда исчерпано количество попыток в backoff."""


def async_backoff(
        start_sleep_time=0.1,
        multiplier=2,
        max_sleep_time=10,
        max_retries=None,
        exceptions_tuple=None,
        logger=logger,
):
    """Декоратор для повторного выполнения функции в случае возникновения одной
    из указанных ошибок. Задержка будет увеличиваться с каждой неуспешной
    попыткой (sleep_time * multiplier) до тех пор пока не достигнет максимума в
    max_sleep_time. Либо пока не будет достигнуто максимальное количество
    попыток, указанное в max_retries (None - пробовать бесконечно). В
    переменной logger можно указать свой экземпляр logging.


    """
    exceptions_tuple = exceptions_tuple or (Exception,)

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            sleep_time = start_sleep_time
            tries = 0
            while max_retries != tries:
                tries += 1
                try:
                    return await func(*args, **kwargs)
                except exceptions_tuple as e:
                    logger.exception('Error was cached by backoff: %s', e)
                    if sleep_time != max_sleep_time:
                        sleep_time = min(
                            sleep_time * multiplier, max_sleep_time
                        )
                    logger.debug('Sleeping for %g sec', sleep_time)
                    await asyncio.sleep(sleep_time)
                    time.sleep(sleep_time)
            else:
                raise BackoffError('Too many retries!')
        return inner
    return wrapper
