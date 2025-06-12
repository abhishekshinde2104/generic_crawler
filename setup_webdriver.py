import tempfile
from seleniumwire import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
#import seleniumwire.undetected_chromedriver as uc

import logging
import platform
import os
import subprocess
import psutil
import shutil


current_os = platform.system().lower()
created_stateful_profile_path = None

def get_driver_path(driver_name):
    global current_os
    driver_path = os.path.join("drivers", "windows") if "windows" in current_os else os.path.join("drivers", "linux")
    if "windows" in current_os:
        executable = os.path.join(driver_path,f"{driver_name}.exe")
    else:
        executable = os.path.join(driver_path, driver_name)
    return executable

def setup_webdriver(browser, headless=True, stateful=False, browser_profile_path=None):
    """
    Set up the WebDriver based on the selected browser and headless mode.
    """
    global current_os
    
    # Local driver variable
    driver = None
    
    logging.info(f"Setting up WebDriver for browser: {browser}")
    
    
    if browser == "firefox":
        seleniumwire_options = {
            'ignore_http_methods': [],
            'request_timeout': 240,
            'disable_encoding':True,
        }
        options = FirefoxOptions()
        
        if stateful and browser_profile_path:
            pass
            # os.makedirs(browser_profile_path, exist_ok=True)
            # TODO: Firefox Profile creation is a manual task
            # TODO: This path to Firefox profile need to be changed based on where it is created,
        
        if headless:
            options.add_argument("--headless") 
            
        executable = get_driver_path("geckodriver")
        logging.info(f"Using Geckodriver driver at path: {executable}")
        if "linux" in current_os:
            options.binary_location = "/usr/bin/firefox"
        
        try:
            service = FirefoxService(executable_path=executable)
            driver = webdriver.Firefox(service=service, options=options, seleniumwire_options=seleniumwire_options)
            driver.maximize_window()
            logging.info("Firefox WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Firefox WebDriver: {e}")
            raise
         
    elif browser == "chrome":
        global created_stateful_profile_path
        seleniumwire_options = {
            'ignore_http_methods': [],
            'request_timeout': 240,
            'disable_encoding':True,
        }
        options = ChromeOptions()
        options.add_argument("--no-sandbox")     # Required when running as root
        options.add_argument("--disable-gpu")
        # options.add_argument("--disable-dev-shm-usage")
        
        
        # This if works on linux, does not work on windows if chrome already in use
        if not stateful and browser_profile_path: # Stateless with Browser Profile Path given
            profile_dir = os.path.join(browser_profile_path, "profile_directory") # This makes new profile under each new video
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile_dir}")
        elif stateful and browser_profile_path:
            if not created_stateful_profile_path:
                created_stateful_profile_path = os.path.join(browser_profile_path, "chrome_stateful_profile")
                if os.path.exists(created_stateful_profile_path):
                    shutil.rmtree(created_stateful_profile_path, ignore_errors=True)
                os.makedirs(created_stateful_profile_path, exist_ok=True)
                logging.info(f"Created clean Chrome profile at: {created_stateful_profile_path}")
            options.add_argument(f"--user-data-dir={created_stateful_profile_path}")
            logging.info(f"Using Chrome profile at: {created_stateful_profile_path}")
            

        
        if headless:
            options.add_argument("--headless=new")
            
        executable = get_driver_path("chromedriver")
        logging.info(f"Using Chrome driver at path: {executable}")
        
        # if "linux" in current_os:
        #     options.binary_location = "/usr/bin/google-chrome"
            
        try: 
            service = ChromeService(executable_path=executable)
            driver = webdriver.Chrome(options=options, service=service, seleniumwire_options=seleniumwire_options)
            driver.maximize_window()
            logging.info("Chrome WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Chrome WebDriver: {e}")
            raise
        
    elif browser == 'edge':
        seleniumwire_options = {
            'ignore_http_methods': [],
            "request_timeout": 240,
            'disable_encoding':True,
            "http2": False,  # Force HTTP/1.1
            # "connection_timeout": 30,  # Increase connection timeout
        }
        options = EdgeOptions()
        # options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--enable-unsafe-swiftshader')
        # options.add_argument("--disable-software-rasterizer")
        
        # Network stability flags
        options.add_argument("--disable-http2")  # Explicit HTTP/2 disable
        options.add_argument("--disable-quic")   # Disable alternative protocol
        
        executable = get_driver_path("msedgedriver")
        logging.info(f"Using Edge driver at path: {executable}")
        
        if headless:
            options.add_argument("--headless=new")
        
        if "linux" in current_os:
            options.binary_location = "/usr/bin/microsoft-edge"
        
        try:
            service = EdgeService(executable)
            driver = webdriver.Edge(options=options, service=service, seleniumwire_options=seleniumwire_options)
            driver.maximize_window()
            logging.info("Edge WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Edge WebDriver: {e}")
        
    elif browser == 'brave':
        seleniumwire_options = {
            'ignore_http_methods': [],
            'request_timeout': 240,
            'disable_encoding':True,
        }
        options = ChromeOptions()
        # options.add_argument("--no-sandbox") # When running as root
        options.add_argument("--disable-gpu")
        # options.add_argument("--disable-software-rasterizer")
        # options.add_argument("--disable-dev-shm-usage")
        
        if headless:
            options.add_argument("--headless=new")
        
        executable = get_driver_path("chromedriver")
        logging.info(f"Brave Using Chrome driver at path: {executable}")
        if "linux" in current_os:
            options.binary_location = "/usr/bin/brave-browser"
        elif "windows" in current_os:
            options.binary_location = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
         
        try:
            service = ChromeService(executable_path=executable)
            driver = webdriver.Chrome(options=options, service=service, seleniumwire_options=seleniumwire_options)
            driver.maximize_window()
            logging.info("Brave WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Brave WebDriver: {e}")
    
    else:
        raise ValueError(f"Unsupported browser: {browser}")
    
    return driver



def close_browser_chrome_n_brave(driver, browser):
    """
    Closes the Chrome or Brave browser and aggressively kills any orphaned subprocesses
    spawned by this script session.
    """

    try:
        driver.quit()
        logging.info("WebDriver closed successfully.")
    except Exception as e:
        logging.warning(f"Error while quitting WebDriver: {e}")

    keywords = {
        "chrome": ["chrome", "chromedriver"],
        "brave": ["brave", "chromedriver"]
    }

    current_uid = os.getuid()
    session_keywords = keywords[browser]

    def is_target_process(proc):
        try:
            # Match name/cmdline and ensure it's run by the current user
            name = proc.name().lower()
            cmd = " ".join(proc.cmdline()).lower()
            return any(k in name or k in cmd for k in session_keywords) and proc.uids().real == current_uid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline", "uids"]):
            if is_target_process(proc):
                logging.info(f"Killing {browser}-related root process: PID {proc.pid} CMD: {' '.join(proc.cmdline())}")
                try:
                    for child in proc.children(recursive=True):
                        try:
                            logging.info(f"  └─ Killing child process: PID {child.pid} CMD: {' '.join(child.cmdline())}")
                            child.kill()
                        except Exception as ce:
                            logging.warning(f"Failed to kill child process {child.pid}: {ce}")
                    proc.kill()
                except Exception as e:
                    logging.warning(f"Failed to kill process {proc.pid}: {e}")
        logging.info(f"All {browser} processes terminated for current session.")
    except Exception as e:
        logging.warning(f"Brave/Chrome process cleanup failed: {e}")
        
        

def close_browser(driver, browser):
    global current_os
    
    # if browser in ["chrome", "brave"]:
    #    close_browser_chrome_n_brave(driver, browser)
    
    
    try:
        driver.quit()
        logging.info("WebDriver closed successfully.")
    except Exception as e:
        logging.warning(f"Error while quitting WebDriver: {e}")
    
    # TODO: this works for firefox and edge perfectly
    # Kill browser-specific lingering processes
    try:
        if current_os == "linux":
            if browser == "firefox":
                subprocess.run(["pkill", "-f", "firefox-esr"], check=False)
                subprocess.run(["pkill", "-f", "geckodriver"], check=False)
            # elif browser == "brave":
                # subprocess.run(["pkill", "-f", "brave"], check=False)
                #subprocess.run(["pkill", "-f", "chromedriver"], check=False)
            # elif browser in ["chrome", "duckduckgo"]:
            #     subprocess.run(["pkill", "-f", "chrome"], check=False)
            #     subprocess.run(["pkill", "-f", "chromedriver"], check=False)
            elif browser == "edge":
                subprocess.run(["pkill", "-f", "microsoft-edge"], check=False)
                subprocess.run(["pkill", "-f", "msedgedriver"], check=False)
        elif current_os == "windows":
            # Fallback to psutil for Windows
            browser_name_map = {
                "firefox": ["firefox.exe", "geckodriver.exe"],
                "chrome": ["chrome.exe", "chromedriver.exe"],
                "brave": ["brave.exe", "chromedriver.exe"],
                "edge": ["msedge.exe", "msedgedriver.exe"]
            }
            for proc in psutil.process_iter(["pid", "name"]):
                for bname in browser_name_map.get(browser, []):
                    if bname.lower() in proc.info["name"].lower():
                        proc.kill()
        logging.info(f"Cleaned up lingering browser processes for: {browser}")
    except Exception as e:
        logging.warning(f"Failed to kill browser processes: {e}")