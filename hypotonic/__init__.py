import logging
import importlib

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
      command, args, kwargs = commands.pop()

      try:
        logger.debug(("Start", i, command, args, kwargs))

        # Dynamically load the command function.
        func = getattr(module, command)
        async for context, data in func(session, context, data, *args, **kwargs):
          if not commands:
            self.results.append(data)
          else:
            logger.debug(("Queue", i, commands, context, data))
            queue.put_nowait((commands.copy(), context, data))

        logger.debug(("Stop", i, command, args, kwargs))
      except Exception as error:
        self.errors.append(((command, args, kwargs), context, error))
        logger.debug(('Error', i, command, args, kwargs, error))
      finally:
        queue.task_done()

  async def run(self):
    session = aiohttp.ClientSession(raise_for_status=True)
    queue = asyncio.Queue()

    tasks = []
    for i in range(4):
      loop = asyncio.get_event_loop()
      tasks.append(loop.create_task(self.worker(i, session, queue)))

    queue.put_nowait((list(reversed(self.commands)), None, {}))
    await queue.join()

    for task in tasks:
      task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await session.close()

    return self.results, self.errors

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
