import asyncio

from sythe import Sythe


async def testing():
    chrome = Sythe(
        "username", "password", debug=True,
        chromedriver_location="../debug_bin/chromedriver.exe",
        binary_location="../debug_bin/chrome.exe",
    )

    await chrome.type_something()
    return "done"


loop = asyncio.get_event_loop()
loop.run_until_complete(testing())
