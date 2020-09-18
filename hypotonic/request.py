"""
Convenience methods for asynchronous HTTP requests.

For performance reasons, we are utilizing aiohttp with keepalive connections [1].
Long-running connections get closed eventually, and aiohttp session throws
an exception to signal those. Exponential backoff is employed to resolve those.

References:
[1] https://github.com/aio-libs/aiohttp/issues/850#issuecomment-210883478
"""

import backoff
import aiohttp


@backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, max_tries=3)
async def get(session, url, params=None):
  async with session.get(url, params=params) as response:
    return response.url, response.content_type, await response.text()


@backoff.on_exception(backoff.expo, aiohttp.ClientConnectionError, max_tries=3)
async def post(session, url, payload=None):
  async with session.post(url, data=payload) as response:
    return response.url, response.content_type, await response.text()
