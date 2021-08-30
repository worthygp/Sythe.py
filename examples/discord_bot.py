import asyncio
import time
import sythe
import json
import requests
import re

from discord.ext import commands


SETTINGS = {
    "prefix": "!",
    "discord_token": "token",
    "sythe_username": "username or email",
    "sythe_password": "password",
    "chrome_cookies_location": "../debug_bin",
    "chromedriver_location": "../debug_bin/chromedriver.exe",
    "chrome_binary_location": "../debug_bin/chrome.exe"
}

BUMP_TEXT = "bump"


class SytheCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_settings = {
            "threads": [],
            "last_bump": None
        }

        print("Logging in...")  # Just to confirm to user that it's working

    async def sythe_spawner(self, ctx):
        """ Spawn a Chrome instance to interact with Sythe.org
        It's spawned in a different task to not crash the bot
        """
        if not await self.can_bump(ctx):
            return

        await ctx.send("Spawning a Chrome instance")

        chrome = sythe.Sythe(
            SETTINGS["sythe_username"],
            SETTINGS["sythe_password"],
            cookies_location=SETTINGS["chrome_cookies_location"],
            chromedriver_location=SETTINGS["chromedriver_location"],
            binary_location=SETTINGS["chrome_binary_location"]
        )

        await ctx.send("Attempt to load previous Chrome cookies")
        await chrome.load_cookies()
        await ctx.send("Logging in to Sythe.com")

        try:
            await chrome.login()
            login_screen = True
        except Exception:
            login_screen = False

        def oauth_code(m):
            if (m.channel == ctx.channel and not m.author.bot):
                if (m.content.isdigit() and m.author.id == ctx.author.id):
                    return True
                return False

        if login_screen:
            while True:
                bypass_2auth = await chrome.check_2auth(enable_input=False)
                if bypass_2auth:
                    break

                await ctx.send("**[ ❌ ]** Login failed, please manually enter oauth code. *(60 secounds timeout)*")

                try:
                    get_code = await self.bot.wait_for("message", timeout=60.0, check=oauth_code)
                    code = get_code.content
                    await ctx.send(f"** [ ⌛ ] ** Attempting oauth code `[ {code} ]`")
                    await chrome.check_2auth(enable_input=True, manual_input=code)
                except asyncio.TimeoutError:
                    return await ctx.send("**[ ❌ ]** Waited too long for oauth, stopping...")

        # For some dumb reasons, Sythe.org needs double login to work.
        # Keeping this in here for now...
        try:
            await chrome.login()
        except Exception:
            pass

        bump_success = 0

        await ctx.send("Reading bump list")
        bump_list = self.get_settings()["threads"]
        await asyncio.sleep(2)

        if not bump_list:
            return await ctx.send("No threads to bump")

        for i, thread_entry in enumerate(bump_list, start=1):
            try:
                thread = f"/threads/{thread_entry}/"
                await ctx.send(f"Bumping thread {i}/{len(bump_list)}  *({thread})*")
                await chrome.local_get(thread)
                await chrome.type_something(BUMP_TEXT)
                bump_success += 1
            except Exception as e:
                await ctx.send(f"**[ ❌ ]** Failed to bump **{thread}**, skipping...\nDEBUG: {e}")

        chrome.save_cookies()
        self.update_settings(last_bump=int(time.time()))
        await ctx.send(
            f"✅ {ctx.author.mention} Bump complete, {bump_success}/{len(bump_list)} threads successful.\n"
            f"📝 **Sythe.py** version: {sythe.__version__}"
        )

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

    def append_thread(self, thread_id: int):
        """ Append thread from the thread JSON """
        data = self.get_settings()
        data["threads"].append(thread_id)
        self.write_settings(data)

    def remove_thread(self, thread_id: int):
        """ Remove thread from the thread JSON """
        data = self.get_settings()
        data["threads"] = [g for g in data["threads"] if g != thread_id]
        self.write_settings(data)

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

    async def can_bump(self, ctx):
        """ Checks if the user can bump """
        last_bump = self.get_settings()["last_bump"]
        if not last_bump:
            return True

        wait_time = 4 * 60 * 60  # 4 hours in seconds

        approved_time = last_bump + wait_time
        if approved_time > int(time.time()):
            await ctx.send(f"You can't bump anymore right now... You'll have to wait till <t:{approved_time}:f>")
            return False
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")

    @commands.command(aliases=["b"])
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    async def bump(self, ctx):
        """ Bumping """
        task = asyncio.ensure_future(self.sythe_spawner(ctx))
        await task

    @commands.command(aliases=["thread"])
    async def threads(self, ctx, thread_id: int = None):
        """ Add/Remove or show all threads the bot should bump """
        data = self.get_settings()["threads"]

        if not thread_id:
            if not data:
                return await ctx.send("No threads found...")

            return await ctx.send("\n".join([
                f"[{i}] <https://www.sythe.org/threads/{g}/>"
                for i, g in enumerate(data, start=1)
            ]))

        # Check if the thread exists
        thread_in_db = [g for g in data if g == thread_id]

        if thread_in_db:
            self.remove_thread(thread_id)
            return await ctx.send(f"**{thread_id}** removed from database, there are now **{len(data) - 1} threads** available.")

        thread_url = f"https://www.sythe.org/threads/{thread_id}"
        r = requests.get(thread_url).content
        r = str(r)

        if "This process is automatic. Your browser will" in r:
            return await ctx.send("The bot was detected by CloudFlare, can't continue...")
        if "You must log in or sign up to reply here" not in r:
            return await ctx.send(f"ThreadID **{thread_id}** is not a valid thread on **sythe.org**")

        get_title = re.search(r"<title>(.*?)<\/title>", r).group(1)

        self.append_thread(thread_id)

        await ctx.send(
            f"✅ ThreadID **{thread_id}** ({get_title}) added to list, "
            f"there are now **{len(data) + 1} threads** in the bump list."
        )


bot = commands.Bot(command_prefix=commands.when_mentioned_or(SETTINGS["prefix"]))
bot.add_cog(SytheCommands(bot))
bot.run(SETTINGS["discord_token"])
