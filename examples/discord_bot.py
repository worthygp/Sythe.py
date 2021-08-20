import sythe
import asyncio

from discord.ext import commands


class Bumper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = [
            1337, 69420
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Successfully logged in as {self.bot.user}")

    async def sythe_spawner(self, ctx):
        """ Run the sythe spawner in background """
        chrome = sythe.Sythe(
            "sythe_username", "sythe_password",
            cookies_location="../debug_bin",
            chromedriver_location="../debug_bin/chromedriver.exe",
            binary_location="../debug_bin/chrome.exe",
        )

        # Load cookies to avoid oauth multiple times
        await chrome.load_cookies()

        try:
            await chrome.login()
            login_screen = True
        except Exception:
            # Logged in already, continue
            login_screen = False

        if login_screen:
            def oauth_code(m):
                if (m.channel == ctx.channel and not m.author.bot):
                    if (m.content.isdigit() and m.author.id == ctx.author.id):
                        return True
                    return False

            while True:
                bypass_2auth = await chrome.check_2auth(enable_input=False)
                if bypass_2auth:
                    break

                await ctx.send("Failed oauth, please enter the oauth code to account")
                try:
                    get_code = await self.bot.wait_for("message", timeout=60.0, check=oauth_code)
                    code = get_code.content
                    await ctx.send(content="Attempting oauth code...")
                    await chrome.check_2auth(enable_input=True, manual_input=code)
                except asyncio.TimeoutError:
                    return await ctx.send(content="Timeout error, no oauth provided, stopping...")

        # Add your code here where you bump threads
        # When done, remember to save cookies
        chrome.save_cookies()
        return None

    @commands.command(aliases=["b"])
    async def bump(self, ctx):
        """ Bump on sythe.org """
        # Run the sythe spawner in background
        # If not, the bot will crash and reboot because
        # the chrome extension isn't async in theory...
        task = asyncio.ensure_future(self.sythe_spawner(ctx))
        await task


bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"))
bot.add_cog(Bumper(bot))
bot.run('token')
