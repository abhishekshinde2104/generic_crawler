from selenium.common.exceptions import TimeoutException

import os
import time
import json
import argparse
import logging
import platform
import traceback
from datetime import datetime


from csv_storage import initialize_csv, store_data_in_csv
from utils import capture_browser_data, wait_for_page_load, extract_domain, current_time, take_page_screenshot, take_element_screenshot
from crawl_logging import start_logging
from config import summary_data
from setup_webdriver import setup_webdriver, close_browser
from cert_installation import install_cert_windows, remove_cert_windows, install_cert_linux, remove_cert_linux

# TODO: Bannerclick
# from updated_bannerclick.bannerclick.bannerdetection import init as bannerclick_init, run_all_for_domain


current_os = platform.system().lower()

def setup_measurement_directory():
    """
    Create a new directory structure for storing measurement data.
    """
    run_id = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    os.makedirs("measurements", exist_ok=True)
    
    base_path = os.path.join("measurements", f"{run_id}")
    os.makedirs(base_path, exist_ok=True)


    session_csv_path = os.path.join(base_path, "session.csv")
    summary_txt_path = os.path.join(base_path, "summary.txt")
    logfile_path = os.path.join(base_path, "logfile.log")
    browser_profile_path = os.path.join(base_path, "browser_profile")

    return run_id, base_path, session_csv_path, summary_txt_path, logfile_path, browser_profile_path


def write_summary(summary_txt_path, summary_data):
    """
    Write measurement summary details to a text file.
    """
    excluded_keys = ['Measurement Start Time', 'Measurement End Time', 'Country', 'Browser', 'Headless mode', 'Hourly Checkpoints']
    with open(summary_txt_path, 'w') as f:
        f.write("Crawler Measurement Summary\n\n")
        f.write(f"Measurement Start Time: {summary_data['Measurement Start Time']}\n")
        f.write(f"Country: {summary_data['Country']}\n")
        f.write(f"Browser: {summary_data['Browser']}\n")
        f.write(f"Headless Mode: {summary_data['Headless mode']}\n")
        f.write(f"Measurement End Time: {summary_data['Measurement End Time']}\n\n")
        
        for key, value in summary_data.items():
            if key not in excluded_keys:
                f.write(f"{key}: {value}\n")
                
        f.write("\nHourly Checkpoints:\n")
        for checkpoint in summary_data["Hourly Checkpoints"]:
            f.write(f"- {checkpoint}\n")
            
            
def check_point(summary_txt_path, ytMaxResults):
    start_time = datetime.strptime(summary_data["Measurement Start Time"], '%Y-%m-%d %H:%M:%S')

    current_time = datetime.now()
    elapsed_time = current_time - start_time

    # Checkpoint every hour
    if elapsed_time.total_seconds() >= (len(summary_data["Hourly Checkpoints"]) + 1) * 3600:
        checkpoint = f"Hour {len(summary_data['Hourly Checkpoints']) + 1}: {summary_data['Number of websites visited']} out of {ytMaxResults} videos watched at {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        summary_data["Hourly Checkpoints"].append(checkpoint)
        write_summary(summary_txt_path, summary_data)
        
        
def main(browser, country, headless):
    """
    Main function which starts the browser - visits youtube videos - perform measurements - closes browser
    """
    global current_os
    # 1. Setup measurement directory
    run_id, base_path, session_csv_path, summary_txt_path, logfile_path, browser_profile_path = setup_measurement_directory() 
    
    # Initialize summary data
    summary_data["Measurement Start Time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary_data["Measurement End Time"] = None
    summary_data["Number of websites visited"] = 0
    summary_data["Country"] = country
    summary_data["Browser"] = browser
    summary_data["Headless mode"] = "Enabled" if headless else "Disabled"
    summary_data["Hourly Checkpoints"] = []
    
    # 2. Setup logging before further processing
    start_logging(logfile_path)
    
    
    # TODO: Video list to go through
    # Get the combined videos for 3 days:
    tranco_csv_path = os.path.join("crawling_csv", "tranco_list.csv")
    domain_dict = {}

    with open(tranco_csv_path, "r") as file:
        for line in file:
            key, value = line.strip().split(",")
            domain_dict[int(key)] = value
        
    
    # Installing MiTM Certificates
    if "windows" in current_os:
        install_cert_windows()
    else:
        install_cert_linux(system_wide=os.geteuid() == 0, user_nss=True)
    
    
    try: 
        logging.info("Script started with the following command-line arguments:")
        logging.info(f"Country: {country}")
        logging.info(f"Browser: {browser}")
        logging.info(f"Headless mode: {'Enabled' if headless else 'Disabled'}")
        
        # HAD TODO: As requests and responses from seleniumwire were getting captured automatically, I had to suppress them
        # Suppress Selenium Wire logging by setting logging level to ERROR
        logging.getLogger('seleniumwire').setLevel(logging.ERROR)

        # Or redirect selenium-wire logs to null (disable completely)
        # logging.getLogger('seleniumwire').propagate = False
            
        # 1. Initialize csv
        initialize_csv(session_csv_path)
        logging.info(f"Length of Website list is: \t {len(domain_dict)}")
        
        for i in range(0, len(domain_dict)):
            website_id = list(domain_dict.keys())[i]
            website_url = list(domain_dict.values())[i]
            
            # In case of stateless mode, this could be used to store browser profiles as well for some browsers like chrome
            website_screenshot_path = os.path.join(base_path, "website_screenshots", website_url)
            os.makedirs(website_screenshot_path, exist_ok=True)
            
            
            website_url = "https://"+website_url
            

            time.sleep(2)
            try:
                # 3. Setup browser instance
                driver = setup_webdriver(browser, headless=headless, stateful=False, browser_profile_path=website_screenshot_path)
                logging.info(f"Video #{i+1} of {len(domain_dict)}")
                logging.info(f"Visiting website URL:\t {website_url}")
                
                # Sleeping 5 seconds
                time.sleep(5)
                
                
                # Visiting Website
                try: 
                    summary_data["Number of websites visited"] += 1  # Increment website count
                    driver.get(website_url)
                # TODO: Check if handles the HTTPConnectionPool error
                except Exception as e:
                    if "Read timed out" in str(e) or "HTTPConnectionPool" in str(e):
                        logging.error(f"HTTPConnectionPool error detected: {e}")
                        time.sleep(10)
                    driver.get(website_url)  # Retry once
                except TimeoutException:
                    logging.error(f"Timeout occurred, for website with url : {website_url} retrying in 10 seconds...")
                    time.sleep(10)
                    driver.get(website_url)  # Retry once
                           
                           
                wait_for_page_load(driver, timeout=30)
                
                # Take screenshot of the youtube page
                take_page_screenshot(driver, f"{website_screenshot_path}/{website_url}.png")
                
                # Scroll
                driver.execute_script("window.scrollBy(0, 300);")
                
                # TODO: checking hourly checkpoint function
                check_point(summary_txt_path, len(domain_dict))
                # TODO: Wait before capturing web requests:
                time.sleep(30)
                logging.info(f"Storing web requests for website: \t {website_url} ")
                store_data_in_csv(timestamp=current_time(), website_id=website_id, website_url=website_url, driver=driver, output_csv_path=session_csv_path)
                
                time.sleep(10)    
                # 16. close the browser
                close_browser(driver, browser)
                
                logging.info(f"... Website #{i+1} of {len(domain_dict)} DONE ...\n\n\n")
                
                # Sleep after closing browser
                time.sleep(30)
            except Exception as e:
                logging.error(f"[ERROR] Exception while setting up WebDriver or browsing:\n{e}")
                if "Read timed out" in str(e) or "HTTPConnectionPool" in str(e):
                    logging.error(f"HTTPConnectionPool error detected: {e}")
                # TODO: This was cause of Zombie processes, deleting those    
                try:
                    if 'driver' in locals():
                        close_browser(driver, browser)
                except Exception as err:
                    logging.warning(f"Failure while Browser cleanup: {err}")
                traceback.print_exc()
                time.sleep(30)
                continue
                    
    
    except KeyboardInterrupt:
        logging.warning("Keyboard Interrupt detected. Closing the browser.")    
    
    except Exception as e:
        if "Read timed out" in str(e) or "HTTPConnectionPool" in str(e):
            logging.error(f"HTTPConnectionPool error detected: {e}")
        else:
            logging.error(f"An unexpected error occurred: {e}")
    
    finally:
        summary_data["Measurement End Time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Remove MiTM Certificate
        if "windows" in current_os:
            remove_cert_windows()
        else:
            remove_cert_linux(system_wide=os.geteuid() == 0, user_nss=True)
        
        
        # Write the Summary details to summary.txt
        write_summary(summary_txt_path, summary_data)
        
        logging.info("Summary written successfully. Exiting program.")
        
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Crawler to crawl websites")
    parser.add_argument("--browser", choices=["firefox", "chrome", "brave", "edge"], default="firefox", help="Browser to use: Firefox/Chrome/Edge/Brave (default: Firefox).")
    parser.add_argument("--country", type=str, required=True, help="Country for which trending videos are to be fetched")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode. (default: headful)")
    args = parser.parse_args()
    

    country = args.country
    browser = args.browser
    headless = args.headless
    
    main(browser=browser, country=country, headless=headless)
    
    
    # Close logging
    logging.info("Session completed.")
    logging.info(f"Closing logging session. {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    logging.shutdown()
    
    # main()