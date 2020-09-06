"""Convenience methods for asynchronous HTTP requests."""


async def get(session, url, params=None):
  async with session.get(url, params=params) as response:
    return str(response.url), response.content_type, await response.text()


async def post(session, url, payload=None):
  async with session.post(url, data=payload) as response:
    return str(response.url), response.content_type, await response.text()
