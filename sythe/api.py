import asyncio
import pickle

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


class Sythe:
    def __init__(
            self, username: str, password: str, debug: bool = False,
            cookies_location: str = ".", binary_location: str = None,
            chromedriver_location: str = None, enable_headless: bool = True,
            page_load_timeout: int = 30):
        """
        Parameters
        -----------
        username: :class:`str`
            Sythe.org username
        password: :class:`str`
            Sythe.org password
        debug: :class:`bool`
            If True, will print debug messages
            Default: False
        cookies_location: :class:`str`
            Location of cookies file
            Example: ./assets
            Default: ./
        binary_location: :class:`str`
            Location of Chrome binary
            Default: PATH
        chromedriver_location: :class:`str`
            Location of ChromeDriver binary
            Default: PATH
        enable_headless: :class:`bool`
            If True, will run Chrome in headless mode
            Default: True
        page_load_timeout: :class:`int`
            Timeout for page loading (in seconds)
        """
        self.username = username
        self.password = password
        self.debug = debug

        self.domain = "https://www.sythe.org"
        self.options = webdriver.ChromeOptions()

        self.cookies_file = f"{cookies_location}/cookies.pkl"

        if binary_location:
            self.options.binary_location = binary_location

        if enable_headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--window-size=1250,800")
        self.options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(
            chromedriver_location or "chromedriver",
            chrome_options=self.options
        )

        self.driver.set_page_load_timeout(page_load_timeout)

    def print_debug(self, message: str):
        """ Prints debug messages when available

        Returns
        --------
        :class:`print`
            returns only if Sythe().debug is True
        """
        if self.debug:
            print(message)

    async def load_cookies(self):
        """ Load cookies """
        self.driver.delete_all_cookies()

        cookies = None
        try:
            cookies = pickle.load(open(self.cookies_file, "rb"))
            await self.get(self.domain)
            for cookie in cookies:
                self.print_debug(cookie)
                self.driver.add_cookie(cookie)
            self.driver.refresh()
        except Exception as e:
            self.print_debug(e)
            if cookies:
                self.save_cookies(cookies=cookies)

    def save_cookies(self, cookies=None):
        """ Saves current cookies from the session """
        pickle.dump(
            cookies or self.driver.get_cookies(),
            open(self.cookies_file, "wb")
        )

    async def local_get(self, url: str):
        """ Request Chrome to open a new place inside Sythe website

        Parameters
        -----------
        url: :class:`str`
            Sythe.org subfolder URL
            Example: /threads = https://sythe.org/threads

        Raises
        -------
        ValueError
            If the url string does not start with /.
        """
        if not url.startswith("/"):
            raise ValueError("URL string must start with a /")

        url = f"{self.domain}{url}"
        return await self.get(url)

    async def check_2auth(self, enable_input: bool = True, manual_input: int = None):
        """ Check if the website is prompting you with 2auth

        Returns
        --------
        :class:`bool`
            True if the website is prompting you with 2auth, otherwise False
        """
        try:
            url = self.driver.current_url
        except Exception:
            # Stupid timeout errors...
            # fix your website Sythe with inf. loading...
            # AAAAAAAAAAAAAAAA
            return False

        if "two-step" in str(url) and enable_input:
            if manual_input:
                get_code = str(manual_input)
            else:
                get_code = input("Please provide 2auth code\n> ")

            self.driver.find_element_by_id("ctrl_totp_code").send_keys(get_code)
            await asyncio.sleep(1)
            self.driver.find_element_by_id("ctrl_totp_code").submit()
            await asyncio.sleep(5)
            return False
        if "two-step" in str(url):
            return False
        return True

    async def debug_mode(self):
        """ A 'while True' loop that lets you run pure eval() code for debugging reasons
        Type 'exit' to leave the eval loop. """
        while True:
            eval_code = input("> ")
            if eval_code.lower() == "exit":
                print("Quitting debug mode...")
                break

            try:
                test = eval(eval_code)
                print(test)
            except Exception as e:
                print(e)

    async def get(self, url: str, retries: int = 5):
        """ Request Chrome to open a new website
        Parameters
        -----------
        url: :class:`str`
            Full URL of what you want to open in Chrome
        retries: :class:`int`
            Number of retries to try before giving up and raising OverflowError

        Raises
        -------
        OverflowError
            When too many attempts has been reached
        """
        self.print_debug(f"Fetching website: {url}")
        retry_attempts = 0

        while True:
            if retry_attempts >= retries:
                raise OverflowError(f"Too many retry attempts... ({retries})")

            try:
                open_this = self.driver.get(url)
                break
            except Exception as e:
                self.print_debug(e)
                retry_attempts += 1
                await asyncio.sleep(1)

        return open_this

    def load_file(self, filename: str):
        """ Load a txt file that should be read

        Parameters
        -----------
        filename: :class:`str`
            Path to the file you want to read

        Raises
        -------
        FileNotFoundError
            When the file does not exist

        Returns
        --------
        :class:`str`
            The textfile content
        """
        with open(filename, "r", encoding="utf-8") as f:
            data = f.read()
        return data

    async def type_something(self, text: str = None, filename: str = None, post: bool = True):
        """ Type something on a thread

        Parameters
        -----------
        text: :class:`str`
            Text to type
        filename: :class:`str`
            Path to a file that will be read (skips text paramter)
        post: :class:`bool`
            Whether to post or not (default: True)

        Raises
        -------
        IndexError
            When there are no text to post
        TypeError
            Whenever there are 0 textboxes found.
            Usually thrown when no access to write or not a thread
        """
        if filename:
            text = self.load_file(filename)
        if not text:
            raise IndexError("No text to type...")

        try:
            textbox = self.driver.find_element_by_class_name("redactor_BbCodeWysiwygEditor")
        except NoSuchElementException:
            raise TypeError("No textbox found...")

        try:
            self.driver.find_element_by_partial_link_text("Use Rich Text Editor")
        except Exception:
            # Something went wrong, we are probably not in BBCode mode
            self.driver.find_element_by_class_name("redactor_btn_switchmode").click()

        self.print_debug("Attempting to type something")
        self.driver.switch_to_frame(textbox)
        await asyncio.sleep(1)

        self.print_debug("Cleaning everything just in case of cache")
        iframe_body = self.driver.find_element_by_tag_name("body")
        iframe_body.send_keys(Keys.CONTROL + "A")
        iframe_body.send_keys(Keys.BACKSPACE)

        self.print_debug("Writing text...")
        await asyncio.sleep(1)
        iframe_body.send_keys(text)
        await asyncio.sleep(1)
        self.driver.switch_to_default_content()
        await asyncio.sleep(3)

        if post:
            self.driver.find_element_by_xpath("//input[@value='Post Reply']").click()

    async def login(self):
        """ Tell Chrome to login on Sythe.org """
        await self.get(self.domain)
        self.print_debug("Attempting to login")
        self.driver.find_element_by_partial_link_text("Log in or").click()
        await asyncio.sleep(4)
        self.driver.find_element_by_id("LoginControl").send_keys(self.username)
        await asyncio.sleep(1)
        self.driver.find_element_by_id("ctrl_password").send_keys(self.password)
        await asyncio.sleep(1)
        self.driver.find_element_by_id("ctrl_password").submit()
        await asyncio.sleep(1)
        self.print_debug("Done logging in")
