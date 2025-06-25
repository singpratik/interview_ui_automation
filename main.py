import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import logger, verify_media_files
from Api_monitor import APICallMonitor
from email_sender import EmailSender
from html_generator import generate_html_report
from EP import UiAutomationHelper

# Email configuration
MAILTRAP_CONFIG = {
    'smtp_server': 'sandbox.smtp.mailtrap.io',
    'smtp_port': 587,
    'username': 'singhpratik0017@gmail.com',
    'password': 'Welcome!@#098123',
    'api_token': 'a10d2e6f59db078dead77ee9f26e69b7'
}

def create_driver_with_media_permissions(video_file_path: str, audio_file_path: str) -> webdriver.Chrome:
    """Launch Chrome with fake webcam/mic streams - Enhanced for Y4M support"""
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    # Verify video file exists and get absolute path
    if not os.path.exists(video_file_path):
        raise FileNotFoundError(f"Video file not found: {video_file_path}")
    
    abs_video_path = os.path.abspath(video_file_path)
    logger.info(f"Using video file: {abs_video_path}")
    
    chrome_options = webdriver.ChromeOptions()
    
    # Core fake media stream arguments - CRITICAL ORDER
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--use-fake-device-for-media-stream")
    chrome_options.add_argument(f"--use-file-for-fake-video-capture={abs_video_path}")
    
    # Additional media stream options for Y4M support
    chrome_options.add_argument("--enable-usermedia-screen-capturing")
    chrome_options.add_argument("--allow-http-screen-capture")
    chrome_options.add_argument("--auto-select-desktop-capture-source=Entire screen")
    
    # Audio file argument if exists
    if audio_file_path and os.path.exists(audio_file_path):
        abs_audio_path = os.path.abspath(audio_file_path)
        chrome_options.add_argument(f"--use-file-for-fake-audio-capture={abs_audio_path}")
        logger.info(f"Using audio file: {abs_audio_path}")
    else:
        logger.warning("No audio file - using fake audio capture")
        chrome_options.add_argument("--use-file-for-fake-audio-capture=")
    
    # Security and file access permissions
    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    
    # Media policy arguments
    chrome_options.add_argument("--allow-file-access")
    chrome_options.add_argument("--allow-cross-origin-auth-prompt")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    
    # Browser behavior options
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1440,900")
    chrome_options.add_argument("--start-maximized")
    
    # Disable automation indicators
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Logging for debugging
    chrome_options.set_capability('goog:loggingPrefs', {
        'performance': 'ALL',
        'browser': 'ALL'
    })

    # Enhanced media permissions
    prefs = {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.notifications": 1,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.media_stream_camera": 1,
        "profile.managed_default_content_settings.media_stream_mic": 1,
        "profile.content_settings.pattern_pairs": {
            "https://*,*": {
                "media-stream": {
                    "video": 1,
                    "audio": 1
                }
            }
        },
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        driver_path = ChromeDriverManager().install()
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        
        # Extended wait for media initialization
        time.sleep(5)
        
        # Set user agent to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize ChromeDriver: {e}")
        raise

def force_media_stream_initialization(driver):
    """Force initialize media streams on the page"""
    try:
        # Wait for page to be ready
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Execute JavaScript to force media stream access
        script = """
        (async function() {
            try {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: true,
                        audio: true
                    });
                    console.log('Media stream acquired successfully');
                    
                    // Find video elements and assign stream
                    const videoElements = document.querySelectorAll('video');
                    videoElements.forEach(video => {
                        if (!video.srcObject) {
                            video.srcObject = stream;
                            video.play();
                        }
                    });
                    
                    return 'success';
                } else {
                    console.log('getUserMedia not available');
                    return 'no-support';
                }
            } catch (error) {
                console.log('Media stream error:', error);
                return 'error: ' + error.message;
            }
        })();
        """
        
        result = driver.execute_script(script)
        logger.info(f"Media stream initialization result: {result}")
        time.sleep(2)
        
    except Exception as e:
        logger.warning(f"Failed to force media stream initialization: {e}")

def wait_for_video_stream(driver, timeout=15):
    """Wait for video stream to be available with enhanced checking"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check if video element exists and has video stream
            video_elements = driver.find_elements(By.TAG_NAME, "video")
            if video_elements:
                for video in video_elements:
                    # Check multiple attributes for video source
                    has_src = video.get_attribute("src")
                    has_srcObject = driver.execute_script("return arguments[0].srcObject !== null", video)
                    video_width = video.get_attribute("videoWidth")
                    
                    if has_src or has_srcObject or (video_width and int(video_width or 0) > 0):
                        logger.info("Video stream detected and active")
                        return True
                        
            # Also check for canvas elements that might be used for video
            canvas_elements = driver.find_elements(By.TAG_NAME, "canvas")
            if canvas_elements:
                logger.info(f"Found {len(canvas_elements)} canvas element(s)")
                
            time.sleep(1)
        except Exception as e:
            logger.debug(f"Checking video stream: {e}")
            time.sleep(1)
    
    logger.warning("Video stream not detected within timeout")
    return False

def main():
    driver = None
    try:
        # Initialize driver
        video_path = "/Users/pratiksingh/Desktop/Interview_automation/EP_smoke_automation/Resources/sample_video.y4m"
        audio_path = "/Users/pratiksingh/Desktop/Interview_automation/EP_smoke_automation/Resources/sample_audio.wav"
        
        # Verify media files exist
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        valid, verified_audio_path = verify_media_files(video_path, audio_path)
        if not valid:
            raise FileNotFoundError("Required media files not found")
        
        # Use the verified audio path or fallback to empty string
        audio_path_to_use = str(verified_audio_path) if verified_audio_path else ""
        
        driver = create_driver_with_media_permissions(video_path, audio_path_to_use)
        
        # Initialize components
        api_monitor = APICallMonitor(driver)
        api_monitor.start_monitoring()
        helper = UiAutomationHelper(driver)
        
        # Navigate to website
        driver.get("https://www.vmock.com/")
        time.sleep(5)  # Allow page to load completely
        
        # Cookie acceptance
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'accept')]"))
            )
            cookie_button.click()
            logger.info("Accepted cookies")
            api_monitor.get_network_logs()
        except Exception as e:
            logger.warning(f"Cookie acceptance not required or failed: {e}")
        
        # Login process
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'login-btn')]"))
            )
            login_button.click()
            
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='button']"))
            ).click()
            
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            email_field.send_keys("epitch-epitch_live21773@vmock.com")
            
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
            )
            password_field.send_keys("1kI9vICw*9")
            
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            time.sleep(5)
            api_monitor.get_network_logs()
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise
        
        # Interview process
        try:
            interview_link = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='interview dropdown']"))
            )
            interview_link.click()
            
            helper.click_start_interview_button()
            helper.close_instructions_popup()
            
            # Wait for calibration page to load completely
            time.sleep(5)
            
            # Force media stream initialization before calibration
            force_media_stream_initialization(driver)
            
            # Check if video stream is working
            video_ready = wait_for_video_stream(driver)
            if not video_ready:
                logger.warning("Video stream not detected, but continuing with calibration")
            
            # Start calibration with extended wait
            helper.start_calicration()
            time.sleep(20)  # Extended wait for calibration to complete
            
            helper.end_interview()
            helper.navigate_to_summary_page()
            api_monitor.get_network_logs()
        except Exception as e:
            logger.error(f"Interview process error: {e}")
            raise
        
        # Generate reports
        api_monitor.save_api_calls_to_file()
        generate_html_report(api_monitor.api_calls)
        api_monitor.print_summary()
        
        # Send email
        email_sender = EmailSender(MAILTRAP_CONFIG)
        if all(os.path.exists(f) for f in ['api_calls_report.html', 'api_calls.json']):
            email_sender.send_html_report(
                html_file_path='api_calls_report.html',
                json_file_path='api_calls.json'
            )
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
    # finally:
    #     if driver:
    #         driver.quit()

if __name__ == "__main__":
    main()