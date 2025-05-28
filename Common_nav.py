from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from EP import UiAutomationHelper
import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the directory containing EP.py to the system path
ep_dir = '/Users/pratik/Downloads/Assesment/Ui_Automation/'
if os.path.exists(os.path.join(ep_dir, 'EP.py')):
    sys.path.append(ep_dir)
else:
    logger.error(f"EP.py not found in {ep_dir}")
    exit(1)



driver_path = '/Users/pratik/Downloads/Assesment/Resource/chromedriver'

service = Service(executable_path=driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--verbose")
options.add_experimental_option("detach", True)

# Add arguments for bypassing face detection
options.add_argument("--use-fake-device-for-media-stream")  # Simulate a fake media device
options.add_argument("--use-fake-ui-for-media-stream")      # Bypass media permission dialogs
options.add_argument("--use-file-for-fake-video-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample.y4m")  # Fake video input
options.add_argument("--use-file-for-fake-audio-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample_audio.wav")  # Fake audio input

try:
    logger.info("Initializing Chrome WebDriver with camera and microphone permissions")
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.get("https://www.vmock.com/")
except Exception as e:
    logger.error(f"Error launching ChromeDriver: {e}")
    exit(1)

# Create helper instance
logger.info("Creating UiAutomationHelper instance")
helper = UiAutomationHelper(driver)

# Accept cookies if the button is present
try:
    logger.info("Checking for cookie acceptance popup")
    if driver.find_elements(By.XPATH, "//div[@class='modal-content']"):
        driver.find_element(By.XPATH, "//button[@class='btn btn-primary accept']").click()
        logger.info("Accepted cookies")
except Exception as e:
    logger.error(f"Cookie acceptance error: {e}")

# Navigate to login
try:
    logger.info("Attempting to navigate to login")
    if driver.find_elements(By.XPATH, "//div[@class='login-btn-container']"):
        driver.find_element(By.XPATH, "//a[@class='btn login-btn anim-btn btn-primary-web']").click()
        logger.info("Login button clicked")
except Exception as e:
    logger.error(f"Login navigation error: {e}")

# Login process
wait = WebDriverWait(driver, 10)
try:
    logger.info("Starting login process")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button']"))).click()
    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    email_field.send_keys("epitch-epitch_live21773@vmock.com")
    password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
    password_field.send_keys("1kI9vICw*9")
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    login_button.click()
    logger.info("Login successful")
except Exception as e:
    logger.error(f"Login error: {e}")

# Dashboard navigation
try:
    logger.info("Navigating to dashboard")
    dashboard_nav = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='collapse navbar-collapse']")))
    interview_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='interview dropdown']")))
    interview_link.click()
    logger.info("Interview dropdown clicked")
    
    # Start the interview
    logger.info("Attempting to start interview")
    helper.click_start_interview_button()

    # Close instructions popup with logging
    logger.info("Attempting to close instructions popup")
    helper.close_instructions_popup()

    # Start calibration
    logger.info("Starting calibration")
    helper.start_calicration()
    logger.info("Calibration started successfully")
    time.sleep(5)  # Wait for calibration to complete
    logger.info("Calibration completed, proceeding with interview")
    time.sleep(10)  # Wait for the interview to be ready
    logger.info("Waiting for interview to be ready")
    time.sleep(10)  # Additional wait time for the interview to be ready
    logger.info("Interview recording is ready, proceeding with the next steps")
    # Wait for the interview to be ready
    time.sleep(20)  # Wait for the interview to be ready
    # End interview
    logger.info("Ending interview")
    helper.end_interview()
    # waiting for process to complete
    helper.navigate_to_summary_page()
    logger.info("Navigated to summary page successfully")
    
except Exception as e:
    logger.error(f"Dashboard navigation error: {e}")

logger.info("Script execution completed")
time.sleep(5)