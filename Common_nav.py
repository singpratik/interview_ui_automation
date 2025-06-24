from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from EP import UiAutomationHelper
from APICallMonitor import APICallMonitor
from HTMLReportGenerator import HTMLReportGenerator
from EmailSender import send_email_report
import sys
import os
import time
import logging
import stat

# Define ANSI color codes for simplicity
class LogColors:
    INFO = "\033[92m"  # Green
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"  # Red
    HEADER = "\033[94m"  # Blue
    API = "\033[33m"    # Orange
    RESET = "\033[0m"   # Reset to default

# Custom formatter to add colors and structure
class CustomFormatter(logging.Formatter):
    def format(self, record):
        color = LogColors.RESET
        if record.levelno == logging.INFO:
            color = LogColors.INFO
        elif record.levelno == logging.WARNING:
            color = LogColors.WARNING
        elif record.levelno == logging.ERROR:
            color = LogColors.ERROR
        elif record.levelno == logging.CRITICAL:
            color = LogColors.HEADER
        elif record.levelno == 25:  # Custom log level for API logs
            color = LogColors.API
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return f"{color}[{timestamp}] {record.levelname}: {record.msg}{LogColors.RESET}"

# Set up the logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Define a custom log level for API logs
logging.addLevelName(25, "API")

def log_api(message):
    logger.log(25, message)

# Helper function for section headers
def log_section_header(header):
    logger.critical("\n" + "=" * 60)
    logger.critical(f"{header}")
    logger.critical("=" * 60 + "\n")

# Example log messages
logger.info("Starting script execution...")

# Add the directory containing EP.py to the system path
ep_dir = '/Users/pratik/Downloads/Assesment/Ui_Automation/'
if os.path.exists(os.path.join(ep_dir, 'EP.py')):
    sys.path.append(ep_dir)
else:
    logger.error(f"EP.py not found in {ep_dir}")
    exit(1)

def initialize_webdriver():
    """
    Initializes the Chrome WebDriver with the required options and returns the driver instance.
    """
    try:
        log_section_header("Initializing Chrome WebDriver")
        logger.info("Setting up Chrome WebDriver with camera and microphone permissions...")
        
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_setting_values.notifications": 1
        }
        
        options = webdriver.ChromeOptions()
        options.add_argument("--verbose")
        options.add_experimental_option("detach", True)
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--use-fake-device-for-media-stream")
        options.add_argument("--use-fake-ui-for-media-stream")
        options.add_argument("--use-file-for-fake-video-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample.y4m")
        options.add_argument("--use-file-for-fake-audio-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample_audio.wav")
        
        # Enable performance logging
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        driver_path = '/Users/pratik/Downloads/Assesment/Resource/chromedriver'
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        logger.info("ChromeDriver launched successfully.")
        
        return driver
    except Exception as e:
        logger.error(f"Error initializing Chrome WebDriver: {e}")
        exit(1)

driver = initialize_webdriver()

# Initialize API monitor
api_monitor = APICallMonitor(driver)
api_monitor.start_monitoring()

# Main test execution wrapped in try/finally
try:
    # Navigate to the website
    driver.get("https://www.vmock.com/")
    logger.info("Navigated to https://www.vmock.com/")
    time.sleep(2)
    logger.info("Fetching initial network logs...")
    api_monitor.get_network_logs()

    # Create helper instance
    logger.info("Creating UiAutomationHelper instance...")
    helper = UiAutomationHelper(driver)

    # Accept cookies if the button is present
    try:
        log_section_header("Cookie Acceptance")
        logger.info("Checking for cookie acceptance popup...")
        if driver.find_elements(By.XPATH, "//div[@class='modal-content']"):
            driver.find_element(By.XPATH, "//button[@class='btn btn-primary accept']").click()
            logger.info("Cookies accepted.")
            time.sleep(1)  # Wait for the popup to close
            logger.info("Fetching network logs after accepting cookies...")
            api_monitor.get_network_logs()
    except Exception as e:
        logger.error(f"Cookie acceptance error: {e}")

    # Navigate to login
    try:
        log_section_header("Login Navigation")
        logger.info("Attempting to navigate to login page...")
        if driver.find_elements(By.XPATH, "//div[@class='login-btn-container']"):
            driver.find_element(By.XPATH, "//a[@class='btn login-btn anim-btn btn-primary-web']").click()
            logger.info("Login button clicked.")
            logger.info("Fetching network logs after navigating to login...")
            api_monitor.get_network_logs()
    except Exception as e:
        logger.error(f"Login navigation error: {e}")

    # Login process
    wait = WebDriverWait(driver, 10)
    try:
        log_section_header("Login Process")
        logger.info("Starting login process...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button']"))).click()
        
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        email_field.send_keys("disney-biz_l1_live42138@vmock.com")
        
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
        password_field.send_keys("@G986xVLdq")
        
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()
        logger.info("Login successful.")
        logger.info("Fetching network logs after login...")
        api_monitor.get_network_logs()
        
    except Exception as e:
        logger.error(f"Login error: {e}")

    # Dashboard navigation
    try:
        log_section_header("Dashboard Navigation")
        logger.info("Navigating to dashboard...")
        dashboard_nav = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='collapse navbar-collapse']")))
        interview_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='interview dropdown']")))
        interview_link.click()
        logger.info("Interview dropdown clicked.")
        logger.info("Fetching network logs after navigating to dashboard...")
        api_monitor.get_network_logs()
        
        # Start the interview
        log_section_header("Interview Process")
        logger.info("Attempting to start interview...")
        helper.click_start_interview_button()
        logger.info("Fetching network logs after starting interview...")
        api_monitor.get_network_logs()

        # Close instructions popup with logging
        logger.info("Attempting to close instructions popup...")
        helper.close_instructions_popup()
        logger.info("Fetching network logs after closing instructions popup...")
        api_monitor.get_network_logs()

        # Start calibration
        logger.info("Starting calibration...")
        helper.start_calicration()
        logger.info("Calibration started successfully.")
        time.sleep(5)
        logger.info("Fetching network logs after calibration...")
        api_monitor.get_network_logs()
        
        logger.info("Calibration completed, proceeding with interview...")
        time.sleep(10)
        
        logger.info("Waiting for interview to be ready...")
        time.sleep(10)
        
        logger.info("Interview recording is ready, proceeding with the next steps...")
        time.sleep(20)
        
        # End interview
        log_section_header("Ending Interview")
        logger.info("Ending interview...")
        helper.end_interview()
        logger.info("Fetching network logs after ending interview...")
        api_monitor.get_network_logs()
        logger.info("Interview ended successfully.")
        
        # Navigate to summary
        helper.navigate_to_summary_page()
        logger.info("Navigated to summary page successfully.")
        logger.info("Fetching network logs after navigating to summary page...")
        api_monitor.get_network_logs()
    except Exception as e:
        logger.error(f"Error in interview execution: {e}")

except Exception as main_error:
    logger.error(f"Critical error in main execution: {main_error}")

finally:
    # FINAL REPORT GENERATION BLOCK - ALWAYS RUNS
    log_section_header("Final Network Log Collection")
    logger.info("Collecting final network logs...")
    time.sleep(2)  # Give time for any pending requests
    api_monitor.get_network_logs()
    api_monitor.print_summary()

    # Directory permissions check
    log_section_header("Directory Permissions Check")
    report_dir = os.getcwd()
    test_file = os.path.join(report_dir, 'permission_test.txt')
    
    try:
        # Check permissions
        dir_stat = os.stat(report_dir)
        permissions = stat.S_IMODE(dir_stat.st_mode)
        logger.info(f"Directory: {report_dir}")
        logger.info(f"Permissions: {oct(permissions)}")
        
        # Test write access
        with open(test_file, 'w') as f:
            f.write('Permission test successful')
        os.remove(test_file)
        logger.info("✅ Write permission verified successfully")
    except Exception as e:
        logger.error(f"❌ Permission error: {e}")
        logger.critical(f"FIX REQUIRED: Run 'chmod u+rwx \"{report_dir}\"' to grant permissions")

    # Report generation
    log_section_header("Report Generation")
    report_path = os.path.join(report_dir, 'api_calls_report.html')
    
    try:
        # Save API calls first
        api_json_path = os.path.join(report_dir, 'api_calls.json')
        if api_monitor.save_api_calls_to_file(api_json_path):
            logger.info(f"Saved {len(api_monitor.api_calls)} API calls to {api_json_path}")
        
        # Generate HTML report
        html_generator = HTMLReportGenerator()
        if html_generator.generate_report(api_monitor.api_calls, report_path):
            logger.info(f"✅ HTML report generated: file://{os.path.abspath(report_path)}")
        else:
            logger.error("❌ HTML report generation failed")
    except Exception as e:
        logger.error(f"Report generation error: {e}")

    # Email report
    try:
        log_section_header("Email Report")
        logger.info("Sending email report...")
        send_email_report()
        logger.info("✅ Email report sent successfully.")
    except Exception as e:
        logger.error(f"Error sending email report: {e}")

    # Final statistics
    stats = api_monitor.get_stats()
    logger.info(f"Final API call statistics: {stats}")
    logger.info("Script execution completed")
