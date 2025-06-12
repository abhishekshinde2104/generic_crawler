from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs
import logging
from requests.exceptions import ReadTimeout



# Define ID patterns for detection
id_patterns = {
    'gclid': r'[?&](gclid)=([a-zA-Z0-9_-]+)',
    'fbclid': r'[?&](fbclid)=([a-zA-Z0-9_-]+)',
    'msclkid': r'[?&](msclkid)=([a-zA-Z0-9_-]+)',
    'user_id': r'[?&](uid|user_id|userid|user)=([a-zA-Z0-9_-]+)',
    'tracking_id': r'[?&](tracking_id|id|token|tracking|trk|track|trk_id)=([a-zA-Z0-9_-]+)',
    'cid': r'[?&](cid)=([a-zA-Z0-9_-]+)',
    'uid': r'[?&](uid)=([a-zA-Z0-9_-]+)',
    'id' : r"[?&]([\w-]*id[\w-]*)=([\w.-]+)",
}

def current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def take_page_screenshot(driver, filename):
    driver.save_screenshot(filename)
    logging.info(f"Full page screenshot saved to {filename}\n")


def take_element_screenshot(driver, element, filename):
    element.screenshot(filename)
    logging.info(f"Element screenshot saved to {filename}\n")


def extract_domain(url):
    """Extract the domain from a URL."""
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc
    except Exception as e:
        logging.error(f"Failed to parse URL {url}: {e}")
        return None

# Function to extract all matching IDs from a URL based on the provided patterns
def extract_ids_from_url(url, id_patterns):
    ids_found = {}
    for id_name, pattern in id_patterns.items():
        matches = re.findall(pattern, url)
        if matches:
            ids_found[id_name] = [match[1] for match in matches]  # Capture the ID values
    return ids_found


def wait_for_page_load(driver, timeout=10):
    """
    Wait until the page is fully loaded.
    """
    logging.info("Waiting for page to load...")
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        logging.info(f"Page is fully loaded in.")
    except Exception as e:
        logging.error(f"Error: Page load timeout after {timeout} seconds. {e}")


def extract_websocket_messages(ws_messages):
    """Extract details from WebSocket messages."""
    ws_data = []
    for msg in ws_messages:
        ws_data.append({
            'timestamp': msg.date.isoformat() if msg.date else datetime.now().isoformat(),
            'content': msg.content.decode('utf-8', errors='ignore') if isinstance(msg.content, bytes) else msg.content,
            'from_client': msg.from_client  # True if sent by client, False if from server
        })
    return ws_data


def extract_request_data(req):
    
    return {
        'timestamp': req.date.isoformat() if req.date else datetime.now().isoformat(),
        'url': req.url,
        'method': req.method,
        'status_code': req.response.status_code if req.response else None,
        'request_headers': dict(req.headers),
        'response_headers': dict(req.response.headers) if req.response else None,
        'location_header': req.response.headers.get('Location') if req.response and 'Location' in req.response.headers else None,
        # 'is_redirect': req.response and req.response.status_code in (301, 302, 303, 307, 308),
        # 'extracted_ids': extract_ids_from_url(req.url, id_patterns),
        # 'query_params': parse_qs(urlparse(req.url).query),
        'response_body': req.response.body.decode('utf-8', errors='ignore') if req.response and req.response.body else None,
        # 'websocket_messages': extract_websocket_messages(req.ws_messages) if req.ws_messages else None,
    }


def capture_browser_data(driver):
    logging.info("Capturing web requests...")
    # Cookies
    # cookies = driver.get_cookies()
    # js_cookies = driver.execute_script("return document.cookie")
        
    # Local Storage
    # local_storage = driver.execute_script("return {...window.localStorage};")
    # session_storage = driver.execute_script("return {...window.sessionStorage};")

    
    # Web Requests
    requests = driver.requests
    
    # web_requests = [extract_request_data(req) for req in requests]
    web_requests = []
    for req in requests:
        try:
            data = extract_request_data(req)
            web_requests.append(data)
        except ReadTimeout:
            logging.warning(f"Request timed out for {req.url if req.url else 'unknown url'}. Retrying extraction...")
            try:
                data = extract_request_data(req)
                web_requests.append(data)
            except Exception as e:
                logging.error(f"Failed extraction on retry for {req.url if req.url else 'unknown url'}: {e}")
                continue
        except Exception as e:
            logging.error(f"Error processing request {req.url if req.url else 'unknown url'}: {e}")
            continue    
    
    # TODO: TRY IF THIS REDUCES REDUNDANT REQUESTS BEING CAPTURED IN DIFFERENT PHASES
    # driver.requests.clear()
    logging.info(f"Length of web requests: {len(web_requests)}")
    
    return {
        # 'cookies': cookies,
        # 'js_cookies': js_cookies,
        # 'local_storage': local_storage,
        # 'session_storage': session_storage,
        'web_requests': web_requests,
    }