# Website Measurement Crawler

This project automates browser-based website crawling to collect web request/response data, screenshots, and logs for measurement purposes. It supports multiple browsers (Firefox, Chrome, Brave, Edge) and works in headless or GUI modes.

## 📁 Project Structure

```text
├── cert_installation.py       # Certificate installation logic for SSL interception
├── config.py                  # Stores summary data used during crawling
├── crawl_logging.py           # Logging utility
├── csv_storage.py             # Initializes and stores web data to CSV
├── main.py                    # Main script to run the crawler
├── setup_webdriver.py         # WebDriver setup for multiple browsers
├── utils.py                   # Helpers for screenshots, URL parsing, etc.
├── crawling_csv/
│   └── tranco_list.csv        # CSV file with list of websites to crawl
├── drivers/
│   ├── linux/
│   └── windows/               # Place browser drivers here
├── measurements/              # Output directory created during each run
    └── YYYY-MM-DD_HH-MM-SS/
        ├── session.csv          # Stores captured web request data
        ├── summary.txt          # Run summary
        ├── logfile.log          # Runtime logs
        ├── browser_profile/     # Browser data profile (optional)
        └── website_screenshots/ # Screenshots for each website
```

## How to Run

### 1. Create and Activate Virtual Environment

```bash
# Create
python3 -m venv venv

# Activate
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Set Up Browser Drivers

Place the appropriate and compatible WebDriver executables in the `drivers/linux/` or `drivers/windows/` directory.

| Browser  | Driver            |
|----------|-------------------|
| Firefox  | `geckodriver`     |
| Chrome   | `chromedriver`    |
| Brave    | `chromedriver`    |
| Edge     | `msedgedriver`    |

---

### 4. Prepare Input CSV

Ensure `crawling_csv/tranco_list.csv` exists and contains:

```csv
1,example.com
2,wikipedia.org
3,github.com
```

---

### 5. Run the Crawler

```bash
# Example: Headless Firefox
python main.py --browser firefox --country india --headless

# Example: Chrome with GUI
python main.py --browser chrome --country usa
```

Valid `--browser` options: `firefox`, `chrome`, `brave`, `edge`  
`--country` specifies country (e.g., germany, india, usa, sweden)  
`--headless` makes the browser run invisibly

`--country` flag is present so that we can use it to differentiate results, in case the plan includes to use openvpn and do crawling in different country.

---

## 📊 Output Results

After each run, a folder is created in `measurements/`:

```text
├── session.csv          # Stores captured web request data
├── summary.txt          # Run summary
├── logfile.log          # Runtime logs
├── browser_profile/     # Browser data profile (optional)
└── website_screenshots/ # Screenshots for each website & in case of chrome also stores chrome profile on linux machines.
```
---

## 🔐 Certificates

Certificates are automatically:

- Installed to the system/user trust store using `cert_installation.py`
- Removed upon completion
- Required for HTTPS traffic inspection via Selenium Wire, else we observe `Not Secure` on the website
