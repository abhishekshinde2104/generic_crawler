import shutil
import subprocess
import os
import logging

def get_seleniumwire_cert_path():
    return "mitm-ca.crt"

def install_cert_windows():
    cert_path = get_seleniumwire_cert_path()
    
    if not os.path.exists(cert_path):
        logging.error(f"Certificate not found at: {cert_path}")
        return

    try:
        result = subprocess.run([
            "certutil",
            "-addstore",
            "-f",  # Force overwrite
            "ROOT",  # Trust store
            cert_path
        ], capture_output=True, text=True, check=True)

        logging.info("Certificate installed successfully:")
        logging.info(result.stdout)

    except subprocess.CalledProcessError as e:
        logging.error("Failed to install certificate.")
        logging.error(e)

def remove_cert_windows():
    subprocess.run([
        "certutil",
        "-delstore",
        "ROOT",
        "mitmproxy"
    ])
    logging.info("Certificate removed from the trust store.")
    

def is_nss_db_usable(nss_db):
    try:
        subprocess.run(
            ["certutil", "-L", "-d", f"sql:{nss_db}"],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    
    
def initialize_nss_db(nss_db):
    try:
        subprocess.run(["certutil", "-N", "-d", f"sql:{nss_db}"], input=b"\n", check=True)
        logging.info("NSS DB initialized with blank password.")
    except subprocess.CalledProcessError as e:
        logging.error("Failed to initialize NSS DB.")
        logging.error(e)
    
    
def install_cert_linux(system_wide=True, user_nss=True):
    cert_path = get_seleniumwire_cert_path()

    if not os.path.exists(cert_path):
        logging.error(f"Certificate not found at: {cert_path}")
        return

    if system_wide:
        # System-wide CA trust
        dst_path = f"/usr/local/share/ca-certificates/seleniumwire.crt"
        try:
            logging.info("Installing cert system-wide...\n")
            subprocess.run(["sudo", "cp", cert_path, dst_path], check=True)
            subprocess.run(["sudo", "update-ca-certificates"], check=True)
            logging.info("System CA trust updated.\n")
        except subprocess.CalledProcessError as e:
            logging.error("System-wide installation failed.\n")
            logging.error(e)

    if user_nss:
        try:
            nss_db = os.path.expanduser("~/.pki/nssdb")
            os.makedirs(nss_db, exist_ok=True)

            if not is_nss_db_usable(nss_db):
                logging.warning("⚠️ NSS DB unusable or missing. Re-initializing...")
                shutil.rmtree(nss_db, ignore_errors=True)
                os.makedirs(nss_db, exist_ok=True)
                initialize_nss_db(nss_db)

            logging.info("Installing cert in user NSS DB...")
            subprocess.run([
                "certutil", "-A", "-d", f"sql:{nss_db}",
                "-n", "Selenium Wire CA", "-t", "C,,", "-i", cert_path
            ], check=True)
            logging.info("NSS trust installed.")
        except subprocess.CalledProcessError as e:
            logging.error("NSS installation failed.")
            logging.error(e)


def remove_cert_linux(system_wide=True, user_nss=True):
    if system_wide:
        try:
            logging.info("Removing system-wide cert...")
            subprocess.run(["sudo", "rm", "/usr/local/share/ca-certificates/seleniumwire.crt"], check=True)
            subprocess.run(["sudo", "update-ca-certificates", "--fresh"], check=True)
            logging.info("Removed from system trust.")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to remove system cert.")
            logging.error(e)

    if user_nss:
        try:
            logging.info("Removing cert from user NSS DB...")
            nss_db = os.path.expanduser("~/.pki/nssdb")
            subprocess.run([
                "certutil", "-D", "-d", f"sql:{nss_db}", "-n", "Selenium Wire CA"
            ], check=True)
            logging.info("Removed from user NSS store.")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to remove cert from NSS.")
            logging.error(e)
    