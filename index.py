import json
import sys
import time

from utils.progress import Progress
from utils.sythe import Sythe
from utils.context import Context

with open("./config.json", "r") as f:
    config = json.load(f)

ctx = Context(config["discord_webhook"])
api = Sythe(config["sythe_username"], config["sythe_password"])

ctx.send("✨ Script started, will start checking for bump in 10 seconds...")


def main():
    time.sleep(10)

    last_bump = api.bump_timestamp()
    approved_time = last_bump + api.wait_time
    if approved_time > int(time.time()):
        print(f"Next bump will start in {approved_time - int(time.time())} seconds")
        return None

    progress_bumper = Progress([
        "Logging in to Sythe.com",
        "Reading bump list",
        "Bumping threads"
    ])

    progress_bumper.show(ctx, 1)

    has_token = api.token()
    if not has_token:
        msg_oauth = ctx.send("📝 Not logged in... attempting to login")
        api.login()

        attempts = 0
        while True:
            if attempts >= config["login_attempts"]:
                msg_oauth.edit(f"🚪 Failed to login after {attempts} attempts, exiting...")
                sys.exit(0)

            api.oauth(msg_oauth)
            recheck_token = api.token()
            if recheck_token:
                msg_oauth.edit("✅ Valid oauth code submitted, logging in...")
                time.sleep(5)
                msg_oauth.delete()
                break
            else:
                attempts += 1
    else:
        # Already logged in
        progress_bumper.show(ctx, 2)
        time.sleep(2)

    threads = api.threads()
    bump_success = 0
    for i, thread_entry in enumerate(threads, start=1):
        thread = f"/threads/{thread_entry}/"
        progress_bumper.update_task(3, f"Bumping thread {i}/{len(threads)} *({thread})*")
        progress_bumper.show(ctx, 3)

        bump_log = api.bump(thread_entry, api.bump_text())
        if bool(bump_log):
            bump_success += 1
            time.sleep(config["bump_delay"])
        else:
            msg = ctx.send(f"Failed to bump {thread_entry}, skipping...\nLogs: {bump_log}")
            time.sleep(5)
            msg.delete()

    progress_bumper.update_task(3, f"Bumping threads {bump_success}/{len(threads)}")
    progress_bumper.show(ctx, -1)

    now = int(time.time())
    api.bump_timestamp(update=now)
    ctx.send(
        f"✅ Bump complete, **{bump_success}/{len(threads)}** threads successful.\n"
        f"⏰ Next bump will appear <t:{now + api.wait_time}:f>"
    )


try:
    while True:
        main()
except KeyboardInterrupt:
    print("Exiting...")
