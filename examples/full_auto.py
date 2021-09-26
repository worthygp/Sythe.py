# --- DISCLAIMER ---
# This script does in fact automate the entire bump process.
# However, if I remember correctly, you have to donate enough to be allowed to use automation.
# Only use this if you are 100% sure that you're allowed to do so.
# I will not take responsibility for you being banned.

import asyncio
import time
import sythe
import json
import requests


SETTINGS = {
    "discord_webhook": "discord webhook url",
    "sythe_username": "username or email",
    "sythe_password": "password",
    "chrome_cookies_location": "../debug_bin",
    "chromedriver_location": "../debug_bin/chromedriver.exe",
    "chrome_binary_location": "../debug_bin/chrome.exe"
}

THREADS = [
    1337, 69, 420
]

BUMP_TEXT = "bump"


class SytheManager:
    def __init__(self):
        self.wait_time = 4 * 60 * 60  # 4 hours in seconds
        self.max_oauth_retries = 3
        self.default_settings = {
            "last_bump": None
        }

    def discord_webook(self, message: str, status: str = "default"):
        """ Send a message to the Discord webhook """
        status_colours = {
            "success": "2ecc71",
            "unsure": "f1c40f",
            "error": "e74c3c"
        }

        colour = status_colours.get(status, "ecf0f1")

        r = requests.post(
            SETTINGS["discord_webhook"],
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "embeds": [{
                    "description": message,
                    "color": int(colour, 16)
                }]
            })
        )

        return r

    async def sythe_spawner(self):
        """ Spawn a Chrome instance to interact with Sythe.org
        It's spawned in a different task to not crash the bot
        """
        if not await self.can_bump():
            return

        self.discord_webook(
            "Bump started, spawning a Chrome instance",
            status="unsure"
        )

        chrome = sythe.Sythe(
            SETTINGS["sythe_username"],
            SETTINGS["sythe_password"],
            cookies_location=SETTINGS["chrome_cookies_location"],
            chromedriver_location=SETTINGS["chromedriver_location"],
            binary_location=SETTINGS["chrome_binary_location"]
        )

        self.discord_webook("Attempt to load previous Chrome cookies", status="unsure")
        await chrome.load_cookies()
        self.discord_webook("Logging in to Sythe.com", status="unsure")

        try:
            await chrome.login()
            login_screen = True
        except Exception:
            login_screen = False

        if login_screen:
            retry = 0
            while True:
                bypass_2auth = await chrome.check_2auth(enable_input=False)
                if bypass_2auth:
                    break

                self.write_oauth()

                self.discord_webook(
                    "Login failed, created an oauth.txt file"
                    "Paste your code in there, I will check every 20 seconds."
                    f"\n\nAttempt: {retry}",
                    status="error"
                )

                await asyncio.sleep(20)
                oauth_code = self.read_oauth()
                if not oauth_code:
                    continue

                self.discord_webook("Attempting oauth code provided...", status="unsure")
                await chrome.check_2auth(enable_input=True, manual_input=oauth_code)
                retry += 1

                if retry > self.max_oauth_retries:
                    return self.discord_webook(
                        f"Max oauth retries reached ({retry}/{self.max_oauth_retries}), stopping...",
                        status="error"
                    )

        # For some dumb reasons, Sythe.org needs double login to work.
        # Keeping this in here for now...
        try:
            await chrome.login()
        except Exception:
            pass

        bump_success = 0

        self.discord_webook("Reading bump list...", status="unsure")
        bump_list = THREADS
        await asyncio.sleep(2)

        if not bump_list:
            return self.discord_webook(
                "No threads to bump...", status="error"
            )

        for i, thread_entry in enumerate(bump_list, start=1):
            try:
                thread = f"/threads/{thread_entry}/"
                self.discord_webook(
                    f"Bumping thread {i}/{len(bump_list)}  ({thread})",
                    status="unsure"
                )
                await chrome.local_get(thread)
                await chrome.type_something(BUMP_TEXT)
                bump_success += 1
            except Exception as e:
                self.discord_webook(
                    f"Failed to bump {thread}, skipping...\nDEBUG: {e}",
                    status="error"
                )

        chrome.save_cookies()
        last_bump_timestamp = int(time.time())
        self.update_settings(last_bump=last_bump_timestamp)

        self.discord_webook(
            f"Bump complete, **{bump_success}/{len(bump_list)}** threads successful.\n"
            f"Next bump will appear <t:{last_bump_timestamp + self.wait_time}:f>"
            f"Sythe.py version: {sythe.__version__}",
            status="success"
        )

    def read_oauth(self):
        try:
            with open("./oauth.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            return self.write_oauth()

    def write_oauth(self):
        with open("./oauth.txt", "w") as f:
            f.write("")
        return ""

    def write_settings(self, data: dict):
        """ Write dict values to the 'database' """
        with open("./sythe.json", "w") as f:
            f.write(json.dumps(data))

    def get_settings(self):
        """ Get the 'database' settings """
        try:
            with open("./sythe.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.write_settings(self.default_settings)
            return self.default_settings

    def update_settings(self, **kwargs):
        """ Update setting(s) in config.json """
        data = self.get_settings()
        for key, value in kwargs.items():
            data[key] = value
        self.write_settings(data)

    def delete_settings(self, *args):
        """ Delete setting(s) in config.json """
        data = self.get_settings()
        for g in args:
            try:
                del data[g]
            except KeyError:
                pass
        self.write_settings(data)

    async def can_bump(self):
        """ Checks if the user can bump """
        last_bump = self.get_settings()["last_bump"]
        if not last_bump:
            return True

        approved_time = last_bump + self.wait_time
        if approved_time > int(time.time()):
            # await ctx.send(f"You can't bump anymore right now...
            # You'll have to wait till <t:{approved_time}:f>")
            return False
        return True

    async def bump(self):
        """ Bumping """
        task = asyncio.ensure_future(self.sythe_spawner())
        await task


async def main():
    bumper = SytheManager()
    bumper.discord_webook(
        "Successfully turned on the Sythe.py bumper script\n"
        "I will start checking for bumps in about 15 seconds..."
    )
    while True:
        await asyncio.sleep(15)
        await bumper.bump()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
