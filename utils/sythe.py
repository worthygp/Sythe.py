import requests
import re
import time
import os
import json


class APIResponse:
    def __init__(self, message: str, success: bool = True):
        self.message = message
        self.success = success

    def __str__(self):
        return self.message

    def __bool__(self):
        return self.success

    def __repr__(self):
        return self.__str__()


class Sythe:
    def __init__(self, username: str, password: str, html_debug: bool = False, settings_folder: str = "./settings"):
        self.username = username
        self.password = password
        self.xftoken = None
        self.html_debug = html_debug
        self.url = "https://www.sythe.org"
        self.session = requests.Session()

        self.wait_time = 4 * 60 * 60  # 4 hours in seconds
        self.settings_folder = settings_folder

    def threads(self):
        with open(f"{self.settings_folder}/threads.txt", "r") as f:
            return [
                g.replace("\n", "").replace("\r", "")
                for g in f.readlines()
            ]

    def bump_text(self):
        with open(f"{self.settings_folder}/bump.txt", "r") as f:
            return f.read()

    def bump_timestamp(self, update: int = None):
        """ Get or update the 'database' settings """
        try:
            with open(f"{self.settings_folder}/sythe.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return self.bump_timestamp_default()

        if update:
            with open(f"{self.settings_folder}/sythe.json", "w") as f:
                data["last_bump"] = update
                json.dump(data, f)
            return update
        return data["last_bump"]

    def bump_timestamp_default(self):
        with open(f"{self.settings_folder}/sythe.json", "w") as f:
            f.write(json.dumps({"last_bump": 0}))
        return 0

    def token(self, r=None):
        re_token = re.compile(r'name="_xfToken" value="(.*?)"')
        if not r:
            r = self.query("GET", "/")

        find_token = re_token.search(r.content.decode())
        return find_token.group(1) if find_token else None

    def load_cookies(self):
        try:
            with open(f"{self.settings_folder}/cookies.json", "r") as f:
                cookies = json.load(f)
        except FileNotFoundError:
            with open(f"{self.settings_folder}/cookies.json", "w") as f:
                json.dump({}, f, indent=2)
            cookies = {}
        return cookies

    def write_cookies(self, r):
        with open(f"{self.settings_folder}/cookies.json", "r") as f:
            cookies = json.load(f)

        for key, value in r.cookies.items():
            cookies[key] = value

        with open(f"{self.settings_folder}/cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        return cookies

    def query(self, method: str, query: str, *args, **kwargs):
        """ Do a query to the API

        NOTE: Must start with a / """

        if "headers" not in kwargs:
            kwargs["headers"] = {}

        if "User-Agent" not in kwargs["headers"]:
            kwargs["headers"]["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

        r = getattr(self.session, method.lower())(
            f"{self.url}{query}", cookies=self.load_cookies(),
            *args, **kwargs
        )

        if self.html_debug:
            if not os.path.exists("./debug"):
                os.mkdir("./debug")
            with open(f"./debug/{int(time.time())}_{query.replace('/', '_')}.html", "w", encoding="utf8") as f:
                f.write(r.content.decode())

        self.write_cookies(r)
        return r

    def login(self):
        r = self.query(
            "POST", "/login/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"login": self.username, "password": self.password}
        )

        return r

    def oauth(self, msg, code: int = None):
        if not code:
            msg.edit(
                "🍃 No code provided, created **oauth.txt** file. "
                "Enter code inside it, I will continue when the file is saved..."
            )

            with open("./oauth.txt", "w") as f:
                f.write("")

            code = ""
            while True:
                time.sleep(1)
                with open("./oauth.txt", "r") as f:
                    new_code = f.read().replace("\\n", "")

                if new_code != code:
                    code = new_code
                    os.remove("./oauth.txt")
                    msg.edit(f"❗ Attempting code: {code}")
                    break
        else:
            msg.edit(f"❗ Code provided: {code}")

        r = self.query(
            "POST", "/login/two-step",
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            data={
                "code": str(code),
                "trust": "1",
                "remember": "1",
                "provider": "totp_blackbox",
                "save": "Confirm",
                "_xfToken": "",
                "_xfConfirm": "1",
                "_xfRequestUri": "/login/two-step?redirect=https%3A%2F%2Fwww.sythe.org%2F&remember=1",
                "_xfNoRedirect": "1",
                "_xfResponseType": "json"
            }
        )

        return r

    def bump(self, thread_id: int, text: str):
        get_thread = r = self.query("GET", f"/threads/{thread_id}")
        if get_thread.status_code != 200:
            return APIResponse("[!] Unknown ThreadID", False)

        re_thread_url = re.compile(r"threads\/(.*?)\/")
        thread_name = re_thread_url.search(get_thread.url)
        if not thread_name:
            return APIResponse("[?] Not sure what happened...", False)
        thread_suburl = thread_name.group(1)

        token = self.token(r)
        if not token:
            return APIResponse("[!] Could not get token", False)

        r = self.query(
            "POST", f"/threads/{thread_suburl}/add-reply",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            data={
                "message_html": f"<p>{text}</p>",
                "_xfRequestUri": f"/threads/{thread_suburl}/",
                "_xfNoRedirect": "1",
                "_xfToken": token,
                "_xfResponseType": "json",
            }
        )

        return APIResponse(f"[+] Bumped {thread_id}", True)
