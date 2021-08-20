import sythe
import asyncio


class Bumper:
    def __init__(self):
        self.chrome = sythe.Sythe(
            "sythe_username", "sythe_password",
            cookies_location="../debug_bin",
            chromedriver_location="../debug_bin/chromedriver.exe",
            binary_location="../debug_bin/chrome.exe",
        )

    async def sign_in(self):
        """ Sign in to sythe.org """
        await self.chrome.load_cookies()

        try:
            await self.chrome.login()
            login_screen = True
        except Exception:
            # Logged in already, continue
            login_screen = False

        if login_screen:
            while True:
                bypass_2auth = await self.chrome.check_2auth(enable_input=False)
                if bypass_2auth:
                    break

                # We need that juicy oauth code now...
                await self.chrome.check_2auth()

        return None


async def main():
    """ Run bumper class with async support """
    chrome = Bumper()

    # Attempt to sign in first
    await chrome.sign_in()

    # Add code to bump whatever you desire
    # When done, save cookies

    # You could also use a time.sleep() here to wait for next bump timer
    # or something, idk, do whatever lmao
    chrome.save_cookies()
    return True


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
