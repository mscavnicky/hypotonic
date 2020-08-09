import sys
import logging
import itertools
import importlib
import traceback

import asyncio
import aiohttp

logger = logging.getLogger('hypotonic')


class Hypotonic:
  def __init__(self, url=None):
    self.commands = []
    self.results = []
    self.errors = []

    if url:
      self.commands.append(('get', (url,), {}))

  async def worker(self, i, session, queue):
    logger.debug(f"Worker {i} starting.")

    module = importlib.import_module('hypotonic.command')
    while True:
      commands, context, data = await queue.get()

      try:
        command, args, kwargs = next(commands)
        logger.debug(("Start", i, command, args, kwargs))

        # Dynamically load the command function.
        func = getattr(module, command)
        async for result in func(session, context, data, *args, **kwargs):
          # Tee creates a shallow copy, advanced separately from original list.
          _, commands_copy = itertools.tee(commands)
          queue.put_nowait((commands_copy, *result))

        logger.debug(("Stop", i, command, args, kwargs))
      except StopIteration:
        self.results.append(data)
      except:
        self.errors.append(((command, args, kwargs, context), sys.exc_info()))
        logger.info(traceback.format_exc())
      finally:
        queue.task_done()

  async def run(self):
    session = aiohttp.ClientSession()
    queue = asyncio.Queue()

    tasks = []
    for i in range(4):
      loop = asyncio.get_event_loop()
      tasks.append(loop.create_task(self.worker(i, session, queue)))

    queue.put_nowait((iter(self.commands), None, {}))
    await queue.join()

    for task in tasks:
      task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    await session.close()

  def data(self):
    """Return all the scraped data as a list of dicts."""
    loop = asyncio.new_event_loop()
    try:
      loop.run_until_complete(self.run())
      return self.results, self.errors
    finally:
      loop.close()

  def __getattr__(self, attr):
    def apply(*args, **kwargs):
      self.commands.append((attr, args, kwargs))
      return self

    return apply
