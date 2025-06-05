from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Remove the deprecated DesiredCapabilities import
from EP import UiAutomationHelper
import sys
import os
import time
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create separate logger for API calls
api_logger = logging.getLogger('api_calls')
api_handler = logging.FileHandler('api_calls.log')
api_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

class APICallMonitor:
    def __init__(self, driver):
        self.driver = driver
        self.api_calls = []
    
    def start_monitoring(self):
        """Enable performance logging to capture network events"""
        # Enable performance logging
        self.driver.execute_cdp_cmd('Network.enable', {})
        logger.info("Network monitoring enabled")
    
    def get_network_logs(self):
        """Retrieve and parse network logs for API calls"""
        try:
            logs = self.driver.get_log('performance')
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    request_id = message['message']['params']['requestId']
                    
                    # Filter for API calls (typically JSON responses or specific endpoints)
                    if self.is_api_call(response):
                        api_call_info = {
                            'timestamp': datetime.now().isoformat(),
                            'url': response['url'],
                            'method': response.get('requestHeaders', {}).get('method', 'GET'),
                            'status': response['status'],
                            'statusText': response['statusText'],
                            'mimeType': response['mimeType'],
                            'headers': response.get('headers', {}),
                            'requestId': request_id
                        }
                        
                        # Try to get response body
                        try:
                            response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                            api_call_info['responseBody'] = response_body.get('body', '')
                        except Exception as e:
                            api_call_info['responseBody'] = f"Could not retrieve body: {str(e)}"
                        
                        self.api_calls.append(api_call_info)
                        self.log_api_call(api_call_info)
        
        except Exception as e:
            logger.error(f"Error retrieving network logs: {e}")
    
    def is_api_call(self, response):
        """Determine if the response is likely an API call"""
        url = response['url'].lower()
        mime_type = response.get('mimeType', '').lower()
        
        # Common patterns for API calls
        api_patterns = [
            'api/',
            '/api',
            'json',
            'ajax',
            'rest/',
            '/rest',
            'graphql',
            'xhr'
        ]
        
        # Check URL patterns
        url_is_api = any(pattern in url for pattern in api_patterns)
        
        # Check MIME type
        mime_is_api = 'json' in mime_type or 'xml' in mime_type
        
        # Exclude static resources
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf']
        is_static = any(url.endswith(ext) for ext in static_extensions)
        
        return (url_is_api or mime_is_api) and not is_static
    
    def log_api_call(self, api_info):
        """Log API call information"""
        log_message = f"""
API Call Detected:
  URL: {api_info['url']}
  Method: {api_info['method']}
  Status: {api_info['status']} {api_info['statusText']}
  Content-Type: {api_info['mimeType']}
  Timestamp: {api_info['timestamp']}
  Response Body: {api_info['responseBody'][:200]}{'...' if len(str(api_info['responseBody'])) > 200 else ''}
  ---
"""
        api_logger.info(log_message)
        logger.info(f"API call logged: {api_info['method']} {api_info['url']} - Status: {api_info['status']}")
    
    def save_api_calls_to_file(self, filename='api_calls.json'):
        """Save all captured API calls to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.api_calls, f, indent=2)
            logger.info(f"API calls saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving API calls to file: {e}")
    
    def print_summary(self):
        """Print a summary of captured API calls"""
        print(f"\n=== API Calls Summary ===")
        print(f"Total API calls captured: {len(self.api_calls)}")
        
        if self.api_calls:
            print("\nAPI Endpoints:")
            for call in self.api_calls:
                print(f"  {call['method']} {call['url']} - {call['status']}")

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

# Enable performance logging for network monitoring (modern approach)
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

# Add arguments for bypassing face detection
options.add_argument("--use-fake-device-for-media-stream")
options.add_argument("--use-fake-ui-for-media-stream")
options.add_argument("--use-file-for-fake-video-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample.y4m")
options.add_argument("--use-file-for-fake-audio-capture=/Users/pratik/Downloads/Assesment/Ui_Automation/Resources/sample_audio.wav")

try:
    logger.info("Initializing Chrome WebDriver with camera, microphone permissions, and network monitoring")
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    }
    options.add_experimental_option("prefs", prefs)
    
    # Initialize driver with performance logging capabilities
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    
    # Initialize API monitor
    api_monitor = APICallMonitor(driver)
    api_monitor.start_monitoring()
    
    driver.get("https://www.vmock.com/")
    
    # Start periodic API monitoring
    api_monitor.get_network_logs()
    
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
        api_monitor.get_network_logs()  # Check for API calls after cookie acceptance
except Exception as e:
    logger.error(f"Cookie acceptance error: {e}")

# Navigate to login
try:
    logger.info("Attempting to navigate to login")
    if driver.find_elements(By.XPATH, "//div[@class='login-btn-container']"):
        driver.find_element(By.XPATH, "//a[@class='btn login-btn anim-btn btn-primary-web']").click()
        logger.info("Login button clicked")
        api_monitor.get_network_logs()  # Check for API calls after login navigation
except Exception as e:
    logger.error(f"Login navigation error: {e}")

# Login process
wait = WebDriverWait(driver, 10)
try:
    logger.info("Starting login process")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button']"))).click()
    api_monitor.get_network_logs()  # Check for API calls
    
    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    email_field.send_keys("epitch-epitch_live21773@vmock.com")
    
    password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
    password_field.send_keys("1kI9vICw*9")
    
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    login_button.click()
    logger.info("Login successful")
    
    # Wait a moment for login API calls to complete
    time.sleep(3)
    api_monitor.get_network_logs()  # Check for login API calls
    
except Exception as e:
    logger.error(f"Login error: {e}")

# Dashboard navigation
try:
    logger.info("Navigating to dashboard")
    dashboard_nav = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='collapse navbar-collapse']")))
    interview_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='interview dropdown']")))
    interview_link.click()
    logger.info("Interview dropdown clicked")
    api_monitor.get_network_logs()  # Check for dashboard API calls
    
    # Start the interview
    logger.info("Attempting to start interview")
    helper.click_start_interview_button()
    api_monitor.get_network_logs()  # Check for interview start API calls

    # Close instructions popup with logging
    logger.info("Attempting to close instructions popup")
    helper.close_instructions_popup()
    api_monitor.get_network_logs()

    # Start calibration
    logger.info("Starting calibration")
    helper.start_calicration()
    logger.info("Calibration started successfully")
    time.sleep(5)
    api_monitor.get_network_logs()  # Check for calibration API calls
    
    logger.info("Calibration completed, proceeding with interview")
    time.sleep(10)
    api_monitor.get_network_logs()
    
    logger.info("Waiting for interview to be ready")
    time.sleep(10)
    api_monitor.get_network_logs()
    
    logger.info("Interview recording is ready, proceeding with the next steps")
    time.sleep(20)
    api_monitor.get_network_logs()
    
    # End interview
    logger.info("Ending interview")
    helper.end_interview()
    api_monitor.get_network_logs()  # Check for interview end API calls
    
    # Navigate to summary
    helper.navigate_to_summary_page()
    logger.info("Navigated to summary page successfully")
    api_monitor.get_network_logs()  # Check for summary page API calls
    
except Exception as e:
    logger.error(f"Dashboard navigation error: {e}")

# Final API monitoring and cleanup
logger.info("Final API call monitoring...")
time.sleep(2)
api_monitor.get_network_logs()

# Save API calls and print summary
api_monitor.save_api_calls_to_file()
api_monitor.print_summary()

logger.info("Script execution completed")
time.sleep(5)
