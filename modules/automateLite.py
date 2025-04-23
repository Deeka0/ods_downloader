
try:
    from base import clear, win32_hider, win32_analyser, downloader, shell_arg
except ImportError:
    from .base import clear, win32_hider, win32_analyser, downloader, shell_arg

import shlex, pickle
from time import sleep
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from platform import processor
from sys import exit, platform, version_info
from subprocess import Popen, run, PIPE, DEVNULL

try:
    from requests import Session
    import undetected_chromedriver as uc
    from psutil import NoSuchProcess, AccessDenied, ZombieProcess, process_iter

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (ElementNotVisibleException, 
                                            StaleElementReferenceException, 
                                            NoSuchElementException, 
                                            SessionNotCreatedException, 
                                            WebDriverException)
except (ImportError, ModuleNotFoundError):
    print("\nModules are not installed!")
    exit("Run 'pip install requirements.txt' in the terminal to fix errors.")


if platform not in ("darwin", "linux", "win32"):
    exit("OS configurations not available yet.")


# Core paths
runtime_path: Path = Path(__file__).parent
parent_runtime_path: Path = runtime_path.parent
desktop_path: Path = Path("~/Desktop").expanduser()

# Hidden runtime files
runtime_folder: Path = parent_runtime_path.joinpath(".runtime")
chromecache_path: Path = runtime_folder.joinpath("chromecache")

# User files
user_folder: Path = parent_runtime_path.joinpath("user")
log_file: Path = user_folder.joinpath(".log")


# UTILITY FUNCTIONS

def log_error(stacktrace: str) -> None:
    """
    Logs a stacktrace to the '.log' file.
    - stacktrace: Error stacktrace.
    """
    today: datetime = datetime.today()
    with open(log_file, "a") as file:
        file.write(f"STACKTRACE {today.date()} at {today.time()}:\n{stacktrace}\n")


def scroll_into_view(driver, element) -> None:
    "Scrolls a web element into view."
    driver.execute_script('arguments[0].scrollIntoView({behaviour: "smooth"});', element)


def load_cookies(session = None, driver = None, cookie_file_path: str | Path = "") -> None:
    """
    Loads saved browser cookies from a file.
    - Defaults to "runtime_folder/cookies.pkl" if no cookie_file_path is passed.
    """
    if session and driver or not session and not driver:
        raise Exception('Specify arguments for either "session" or "driver".')

    if session:
        cookie_file_name = "requests_cookies.pkl"
    elif driver:
        cookie_file_name = "webdriver_cookies.pkl"

    cookie_file_path = cookie_file_path if cookie_file_path else runtime_folder.joinpath(cookie_file_name)
    try:
        # {'name': cookie["name"], 'value': cookie["value"], 'domain': cookie["domain"], 'secure': cookie["secure"], 'httpOnly': cookie["httpOnly"], 'path': cookie["path"], 'sameSite': cookie["sameSite"], 'expiry': cookie["expiry"]}
        with open(cookie_file_path, "rb") as cookie_file:
            cookies = pickle.load(cookie_file)

        if session:
            for cookie in cookies:
                session.cookies.update({cookie["name"] : cookie["value"]})

        elif driver:
            for cookie in cookies:
                driver.add_cookie(cookie)

    except FileNotFoundError:
        raise Exception("Invalid path for specified file.")


def save_cookies(session = None, driver = None, cookie_file_path: str | Path = "") -> None:
    """
    Saves browser cookies to a file.
    - Defaults to "runtime_folder/cookies.pkl" if no cookie_file_path is passed.
    - cookies: Browser cookies as Python dicts:
        - Dump using requests: session.cookies.get_dict() -> dict[str, str]
        - Dump using selenium: driver.get_cookies() -> list[dict]
    """
    if session and driver or not session and not driver:
        raise Exception('Specify arguments for either "session" or "driver".')

    if session:
        cookie_file_name = "requests_cookies.pkl"
        cookies = session.cookies.get_dict()
    elif driver:
        cookie_file_name = "webdriver_cookies.pkl"
        cookies = driver.get_cookies()

    cookie_file_path = cookie_file_path if cookie_file_path else runtime_folder.joinpath(cookie_file_name)
    try:
        with open(cookie_file_path, "wb") as cookie_file:
            pickle.dump(cookies, cookie_file)

    except FileNotFoundError:
        raise Exception("Invalid path for specified file.")


def force_click(driver, element) -> None:
    "Clicks a web element using JavaScript injection."
    driver.execute_script("arguments[0].click();", element)


def get_browser_version() -> bool | str:
    """
    Fetches version of currently installed Google Chrome browser.
    """
    # Get browser version
    match platform:

        # For Windows
        case "win32":

            # Powershell
            # Older versions install to the 32-bit directory
            # (Get-Item 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe').VersionInfo.ProductVersion

            # Newer versions use the 64-bit directory
            # (Get-Item 'C:\Program Files\Google\Chrome\Application\chrome.exe').VersionInfo.ProductVersion

            # To using it in cmd.exe or via any subprocess calls (python, go os/exec, etc.) you can do,
            # powershell -command "&{(Get-Item 'Path\To\chrome.exe').VersionInfo.ProductVersion}"

            browser_path = Path("C:\\").joinpath("Program Files").joinpath("Google").joinpath("Chrome").joinpath("Application").joinpath("chrome.exe")
            version_command = f"(Get-Item '{browser_path}').VersionInfo.ProductVersion"
            version_command = win32_analyser(command=version_command)

        # For macOS
        case "darwin":

            # Full browser path
            # version_command = "/Applications/'Google Chrome.app'/Contents/MacOS/'Google Chrome' --version"

            browser_path = Path("/Applications").joinpath("Google Chrome.app").joinpath("Contents").joinpath("MacOS").joinpath("Google Chrome")
            version_command = f"'{browser_path}' --version"

        # For Linux
        case "linux":
            version_command = "google-chrome --version"
    
    try:
        with Popen(args=shlex.split(version_command), stdout=PIPE, stderr=DEVNULL, shell=shell_arg) as curler:
            output = curler.stdout.read().strip().decode()
            browser_version = output.split(" ")[-1].split(".")[0]
            
    except:
        return False
    finally:
        curler.terminate()
        curler.wait()

    return browser_version


def fetch_chromedriver() -> bool | str:
    """
    Downloads the latest chromedriver binary from Google servers.
    """
    browser_version = get_browser_version()
    if not browser_version:
        return False
    
    with Session() as driver_session:

        response = driver_session.get(url="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json")
        if response.status_code != 200:
            return False
        
        found: bool = False
        all_versions: list[str] = response.json()["versions"]
        for version in all_versions:
            if version["version"].split(".")[0] == browser_version:
                response_data: list[str] = version["downloads"]["chromedriver"]
                found = True
                break

        if not found:
            return False

    # For platform specific chromedriver download
    match platform:
        case "darwin":
            selected_platform = "mac-arm64" if processor() == "arm" else "mac-x64"
        case "linux" | "linux2":
            selected_platform = "linux64"
        case "win32":
            selected_platform = "win32"
        case "win64":
            selected_platform = "win64"

    # Download binary for selected platform
    for data in response_data:
        if data["platform"] == selected_platform:
            download_url: str = data["url"]

            print("Fetching new driver, please wait ...")
            is_downloaded = downloader(destination_path=runtime_folder, download_url=download_url)
            if not is_downloaded:
                return False
            
            return download_url.split("/")[-1]
            
    return False


def process_binary(fetched_file: str, binary_executable_path: Path | str) -> bool:
    """
    Processes the newly downloaded chromedriver binary for usage.
    """
    zipped_binary = runtime_folder.joinpath(fetched_file)
    extracted_binary_folder = runtime_folder.joinpath(fetched_file.replace('.zip', ''))
    extracted_binary = extracted_binary_folder.joinpath('chromedriver.exe' if platform == 'win32' else 'chromedriver')

    try:
        print("Processing binary ...")
        # Delete the existing binary
        if binary_executable_path.is_file():
            binary_executable_path.unlink()
            sleep(1)

        # Unzip the zipped binary
        if zipped_binary.is_file():
            with ZipFile(file=zipped_binary, mode="r") as file:
                file.extractall(path=runtime_folder)
            sleep(1)

        # Move the extracted binary to the core_data_folder
        if extracted_binary.is_file():
            extracted_binary.replace(target=binary_executable_path)
            sleep(1)

        # Delete the extracted binary folder
        if extracted_binary_folder.is_dir():
            remove_command = f"rm -r {extracted_binary_folder}"
            if platform == "win32": remove_command = win32_analyser(command=remove_command)
            
            run(args=shlex.split(remove_command), stderr=DEVNULL)
            sleep(1)

        # Delete the zipped binary
        if zipped_binary.is_file():
            zipped_binary.unlink()
            sleep(1)

        # Fix permissions for extracted binary on macOS and Linux
        if platform != "win32" and binary_executable_path.is_file():
            # fix_command = f"chmod 755 {binary_executable_path}"
            fix_command = f"chmod +x {binary_executable_path}"

            run(args=shlex.split(fix_command), stderr=DEVNULL)
            sleep(1)

        return True
    except:
        return False


def compose_launch_command(headless: bool, data_directory: str, port: int | None = None) -> str:
    """
    Composes a command to launch browsers on different OS
    """
    match platform:

        # For Windows
        case "win32":
            browser_launch_path = Path('C:\\').joinpath('Program Files').joinpath('Google').joinpath('Chrome').joinpath('Application').joinpath('chrome.exe')
            browser_launch_path = f"'{browser_launch_path}'"

        # For macOS
        case "darwin":
            browser_launch_path = Path("/Applications").joinpath("Google Chrome.app").joinpath("Contents").joinpath("MacOS").joinpath("Google Chrome")
            browser_launch_path = f"'{browser_launch_path}'"


        # For Linux
        case "linux":
            browser_launch_path = "google-chrome"
    
    final_command = f"{browser_launch_path} {f'--remote-debugging-port={port}' if port else ''} --user-data-dir='{data_directory}' {'--headless=new' if headless else ''} --no-first-run --start-maximized"
    return final_command


def wait_for_chrome() -> None:
    """
    Waits for Google Chrome to launch efficiently.
    """
    checked_processes: int = 0
    while checked_processes < 7:

        # Possible race condition due to permissions error on macOS.
        # Explained at: https://github.com/giampaolo/psutil/issues/2189
        
        # # First fix method
        # for process in process_iter(attrs=["name"]):
        #     if "chrome" in process.info["name"].lower(): checked_processes += 1

        # Second fix method
        for process in process_iter():
            try:
                if "chrome" in process.name().lower(): checked_processes += 1
            except (NoSuchProcess, AccessDenied, ZombieProcess):
                continue

        sleep(2)

    sleep(3)


def initialize_chrome_session(port: int, headless: bool = True) -> bool | Popen:
    """
    Starts up Google Chrome from a dedicated profile directory.
    If an active directory is unavailable, it is created.
    - headless: Flag indicates if browser would be seen or not.
    """
    is_new = False

    # Check for persistent chrome folder
    if not chromecache_path.is_dir():
        is_new = True
        print("Crafting new profile. Please wait ...")
    else:
        print("Spooling up ...")

    launch_command = compose_launch_command(headless=headless, port=port, data_directory=chromecache_path)
    try:
        new_chrome = Popen(args=shlex.split(launch_command), stderr=DEVNULL)
        wait_for_chrome()

        if is_new:
            print("Done crafting profile.")

        return new_chrome
    except:
        print("An error occured!")
        new_chrome.terminate()
        new_chrome.wait()
        return False
    finally:
        sleep(1)


class AutomateLite:

    def __init__(self, 
                 debug: bool = False, 
                 headless: bool = True, 
                 undetected: bool = False, 
                 slave: bool = False, 
                 port: int = 9000, 
                 browser_version: int = 108, 
                 load_images: bool = True, 
                 binary_executable_path: Path | str = None, 
                 ) -> None:
        
        # Guide
        """
        Defaults:
        - debug: Uses embedded driver binary if set to True.
        - headless: Sets headless property.
        - undetected: Runs headless Chrome browser with undetected-chromedriver. Compatible with only Python 3.11.*.
        - slave: Toggles slave mode (takes over already open browser window if set to True).
        - port: Port used by Chrome browser to connect to in slave mode.
        - browser_version: Rounded up Chrome browser version.
        - load_images: Sets image load property.
        - binary_executable_path: Path to chromedriver executable.
        """
        
        # Default constructor flags
        self.binary_executable_path = binary_executable_path
        self.debug = debug
        self.headless = headless
        self.undetected = undetected
        self.slave = slave
        self.port = port
        self.browser_version = browser_version
        self.load_images = load_images

        # Check for chromedriver and/or undetected_chromedriver
        if self.debug and not self.binary_executable_path.is_file():
            print("Error! chromedriver was not found.")
            raise KeyError

        if self.slave and not self.port:
            print("Error! You must declare an open port.")
            raise SystemExit

        # Custom flag management
        if self.undetected:

            # Checks for Python version (3.8.* - 3.11.*)
            if version_info.major != 3 or version_info.minor not in (8, 9, 10, 11):
                print("Error! Invalid Python version. Undetected mode is only compatible with Python 3.8 - 3.11")
                raise SystemExit
            
            self.webdriver = uc
        else:
            self.webdriver = webdriver

        if self.slave: self.headless = True

        self.Options = Options
        self.Service = Service


    def core(self):
        """
        Prepares core session configurations.
        """
        options = self.Options()
        options.add_argument("--start-maximized") # Maximize browser window to fix view ports

        # Headless mode argument
        if self.headless: options.add_argument("--headless=new")

        # Manages image loads
        if not self.load_images: options.add_argument("--blink-settings=imagesEnabled=false")

        # Slave mode management
        if self.slave: options.add_argument(f"--remote-debugging-port={self.port}")

        service = self.Service(executable_path=self.binary_executable_path) if self.debug else self.Service()
        # service = self.Service(executable_path=undetected_binary_executable_path) if self.debug else self.Service()

        # ===== DISABLE WebRTC features =====
        options.add_argument("--enforce-webrtc-ip-permission-check")
        options.add_argument("--webrtc-ip-handling-policy=disable_non_proxied_udp")
        options.add_argument("--force-webrtc-ip-handling-policy")
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--use-fake-device-for-media-stream')
        options.add_argument("--disable-media-session-api")

        # ===== CHROMIUM BASED ANONYMITY FEATURES =====
        if self.undetected:
            options.add_argument('--disable-gpu')
        else:
            options.add_argument("--disable-blink-features=AutomationControlled") # Adding argument to disable the AutomationControlled flag
            options.add_experimental_option("excludeSwitches", ["enable-automation"]) # Exclude the collection of enable-automation switches
            options.add_experimental_option("useAutomationExtension", False) # Turn-off userAutomationExtension

        return options, service


    def session(self):
        """
        Fires up the session.
        """
        try:
            clear()
            print("Spawning session ...")
            options, service = self.core()

            BrowserClass = self.webdriver.Chrome

            try:
                if self.webdriver.__name__ == "selenium.webdriver":
                    driver = BrowserClass(options=options, service=service)
                elif self.webdriver.__name__ == "undetected_chromedriver":
                    # driver = BrowserClass(options=options, driver_executable_path=str(self.binary_executable_path) if platform == "win32" else self.binary_executable_path, port=self.port, version_main=self.browser_version) if self.debug else BrowserClass(options=options, port=self.port, version_main=self.browser_version)

                    if self.debug:
                        driver = BrowserClass(options=options, driver_executable_path=str(self.binary_executable_path) if platform == "win32" else self.binary_executable_path, port=self.port, version_main=self.browser_version)
                    else:
                        driver = BrowserClass(options=options, port=self.port, version_main=self.browser_version)
            
            except SessionNotCreatedException:
                print("Error! chromedriver is outdated.")
                raise KeyError

            wait = WebDriverWait(driver=driver, timeout=30)
            action = ActionChains(driver=driver)

            # ===== GENERAL ANONYMITY FEATURES =====
            if not self.slave:
                # Changing the property of the navigator value for webdriver to undefined
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Fix headless UAs
            user_agent = driver.execute_script('return navigator.userAgent;')
            for i in ("Headless", "headless"):
                if i in user_agent:
                    user_agent = user_agent.replace(i, "")

                    # Spoof User-Agent on the fly for chromium based browsers
                    driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
                    # driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {"userAgent": user_agent})
                    break

            return driver, wait, action
        except KeyboardInterrupt:
            print("\nInterrupted by user.")


def generate_puppies(
        port: int, 
        binary_executable_path: Path | str, 
        debug_mode: bool = True, 
        load_images: bool = True, 
        retrying: bool = False
        ):
    """
    Generates an active instance of webdriver, WebDriverWait and ActionChains.
    """
    # Defaults to debug mode
    try:
        driver, wait, action = AutomateLite(
            debug=debug_mode, 
            undetected=True, 
            slave=True, port=port, 
            load_images=load_images, 
            browser_version=int(get_browser_version()), 
            binary_executable_path=binary_executable_path
            ).session()
        
        return driver, wait, action
    
    except KeyError:

        if debug_mode:
            
            if retrying:
                # Launch in release mode
                print("Debug mode error! Falling back to Release mode ...")
                sleep(3)
                print("Fetching release driver, please wait ...")
                return generate_puppies(port=port, binary_executable_path=binary_executable_path, debug_mode=False, load_images=load_images, retrying=retrying)

            is_fetched = fetch_chromedriver()
            if not is_fetched:
                print("Couldn't fetch binary!")
                raise SystemExit

            is_processed = process_binary(fetched_file=is_fetched, binary_executable_path=binary_executable_path)
            if not is_processed:
                print("Couldn't process binary!")
                raise SystemExit
            
            # Retry launching in debug mode with latest driver
            return generate_puppies(port=port, binary_executable_path=binary_executable_path, debug_mode=debug_mode, load_images=load_images, retrying=True)

        # A higher level error due to failure of release mode
        print("Critical Error! Please contact your administrator.")
        raise SystemExit

    except (SystemExit, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\nInterrupted by user!")
        
        raise SystemExit

    except:
        print("Critical error!")
        raise SystemExit


# Check for runtime folder
if not runtime_folder.is_dir():
    runtime_folder.mkdir(parents=True, exist_ok=True)
    if platform == "win32": win32_hider(path=runtime_folder) # Hide folder

# Check for user folder
if not user_folder.is_dir():
    user_folder.mkdir(parents=True, exist_ok=True)

# Check for log file
if not log_file.is_file():
    log_file.touch()
    if platform == "win32": win32_hider(path=log_file) # Hide file





# TO-DO
# 



# DONE
# binary_executable_path in AutomateLite
# runtime_folder in fetch_chromedriver
# runtime_folder, binary_executable_path in process_binary
# chromecache_path, port in initialize_chrome_session
# port, runtime_folder, binary_executable_path in generate_puppies
# FIX DEFAULT port=args.port in generate_puppies, initialize_chrome_session
# Fixed checks for chrome updates and added driver update feature
# Fixed intermittent runtime breaks
# 

