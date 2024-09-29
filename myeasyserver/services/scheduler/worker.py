#  Copyright (c) 2024.  stef.
#
#      ______                 _____
#     / ____/___ ________  __/ ___/___  ______   _____  _____
#    / __/ / __ `/ ___/ / / /\__ \/ _ \/ ___/ | / / _ \/ ___/
#   / /___/ /_/ (__  ) /_/ /___/ /  __/ /   | |/ /  __/ /
#  /_____/\__,_/____/\__, //____/\___/_/    |___/\___/_/
#                   /____/
#
#  Apache License
#  ================
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Code Adapted/Copied From fastapi_utils
# https://github.com/dmontagu/fastapi-utils/blob/master/fastapi_utils/tasks.py

import asyncio
import functools
import logging
import sys
import typing
from collections.abc import Callable, Coroutine
from functools import wraps
from traceback import format_exception
from typing import Any, Union

import anyio

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec
P = ParamSpec("P")
T = typing.TypeVar("T")

NoArgsNoReturnFuncT = Callable[[], None]
NoArgsNoReturnAsyncFuncT = Callable[[], Coroutine[Any, Any, None]]
ExcArgNoReturnFuncT = Callable[[Exception], None]
ExcArgNoReturnAsyncFuncT = Callable[[Exception], Coroutine[Any, Any, None]]
NoArgsNoReturnAnyFuncT = Union[NoArgsNoReturnFuncT, NoArgsNoReturnAsyncFuncT]
ExcArgNoReturnAnyFuncT = Union[ExcArgNoReturnFuncT, ExcArgNoReturnAsyncFuncT]
NoArgsNoReturnDecorator = Callable[[NoArgsNoReturnAnyFuncT], NoArgsNoReturnAsyncFuncT]

async def _handle_func(func, *args, **kwargs) -> None:
    if asyncio.iscoroutinefunction(func):
        await func(*args, **kwargs)
    else:
        await run_in_threadpool(func, *args, **kwargs)

async def _handle_exc(exc: Exception, on_exception, *args, **kwargs) -> None:
    if on_exception:
        if asyncio.iscoroutinefunction(on_exception):
            await on_exception(exc, *args, **kwargs)
        else:
            await run_in_threadpool(on_exception, exc, *args, **kwargs)

# got from starlette.concurrency
async def run_in_threadpool(
    func: typing.Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    if kwargs:  # pragma: no cover
        # run_sync doesn't accept 'kwargs', so bind them in here
        func = functools.partial(func, **kwargs)
    return await anyio.to_thread.run_sync(func, *args)


async def threaded_loop( func, *args,
    seconds: float,
    wait_first: float | bool = False,
    logger: logging.Logger | None = None,
    raise_exceptions: bool = False,
    max_repetitions: int | None = None,
    on_complete: NoArgsNoReturnAnyFuncT | None = None,
    on_exception: ExcArgNoReturnAnyFuncT | None = None,
    ** kwargs,

) -> None:
    """
    This function call in a separated thread func which is periodically re-executed after its first call.
    Func should return nothing. If necessary, this can be accomplished
    by using `functools.partial` or otherwise wrapping the target function prior.

    Parameters
    ----------
    func: Callable or Coroutine
       The function to call
    args:
        Positional arguments to pass to the decorated function
    kwargs:
        Keyword arguments to pass to the decorated function
    seconds: float
        The number of seconds to wait between repeated calls
    wait_first: float | bool (default False)
        If True, the function will wait for a single period of seconds before the first call
        If a Float value is given, the function will wait that many seconds before the first call
    logger: Optional[logging.Logger] (default None)
        The logger to use to log any exceptions raised by calls to the decorated function.
        If not provided, exceptions will not be logged by this function (though they may be handled by the event loop).
    raise_exceptions: bool (default False)
        If True, errors raised by the decorated function will be raised to the event loop's exception handler.
        Note that if an error is raised, the repeated execution will stop.
        Otherwise, exceptions are just logged and the execution continues to repeat.
        See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_exception_handler for more info.
    max_repetitions: Optional[int] (default None)
        The maximum number of times to call the repeated function. If `None`, the function is repeated forever.
    on_complete: Optional[Callable[[], None]] (default None)
        A function to call after the final repetition of the decorated function.
    on_exception: Optional[Callable[[Exception], None]] (default None)
        A function to call when an exception is raised by the decorated function.
    """

    async def loop()-> None:
        if wait_first:
            if isinstance(wait_first, bool):
                timeout = seconds
            else:
                timeout = wait_first
            await asyncio.sleep(timeout)
        repetitions = 0
        while max_repetitions is None or repetitions < max_repetitions:
            try:
                await _handle_func(func, *args, **kwargs)
            except Exception as exc:
                if logger is not None:
                    formatted_exception = "".join(format_exception(type(exc), exc, exc.__traceback__))
                    logger.error(formatted_exception)
                if raise_exceptions:
                    raise exc
                await _handle_exc(exc, on_exception, *args, **kwargs)

            repetitions += 1
            await asyncio.sleep(seconds)

        if on_complete:
            await _handle_func(on_complete, *args, **kwargs)

    asyncio.ensure_future(loop())


def worker_every(
    *args,
    seconds: float,
    wait_first: float | bool = False,
    logger: logging.Logger | None = None,
    raise_exceptions: bool = False,
    max_repetitions: int | None = None,
    on_complete: NoArgsNoReturnAnyFuncT | None = None,
    on_exception: ExcArgNoReturnAnyFuncT | None = None,
    **kwargs,
) -> NoArgsNoReturnDecorator:
    """
    This function returns a decorator that modifies a function so it is periodically re-executed after its first call.
    The function it decorates should accept no arguments and return nothing. If necessary, this can be accomplished
    by using `functools.partial` or otherwise wrapping the target function prior to decoration.

    Parameters
    ----------
    seconds: float
        The number of seconds to wait between repeated calls
    wait_first: float | bool (default False)
        If True, the function will wait for a single period of seconds before the first call
        If a Float value is given, the function will wait that many seconds before the first call
    logger: Optional[logging.Logger] (default None)
        The logger to use to log any exceptions raised by calls to the decorated function.
        If not provided, exceptions will not be logged by this function (though they may be handled by the event loop).
    raise_exceptions: bool (default False)
        If True, errors raised by the decorated function will be raised to the event loop's exception handler.
        Note that if an error is raised, the repeated execution will stop.
        Otherwise, exceptions are just logged and the execution continues to repeat.
        See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_exception_handler for more info.
    max_repetitions: Optional[int] (default None)
        The maximum number of times to call the repeated function. If `None`, the function is repeated forever.
    on_complete: Optional[Callable[[], None]] (default None)
        A function to call after the final repetition of the decorated function.
    on_exception: Optional[Callable[[Exception], None]] (default None)
        A function to call when an exception is raised by the decorated function.
    """

    def decorator(func: NoArgsNoReturnAsyncFuncT | NoArgsNoReturnFuncT) -> NoArgsNoReturnAsyncFuncT:
        """
        Converts the decorated function into a repeated, periodically-called version of itself.
        """
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func) # keep the original function name and docstring
        async def wrapped() -> None:
            threaded_loop(func, *args, seconds, wait_first, logger, raise_exceptions, max_repetitions, on_complete, on_exception, **kwargs)

        return wrapped

    return decorator
