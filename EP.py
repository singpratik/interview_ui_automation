from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

class UiAutomationHelper:
    def __init__(self, driver):
        self.driver = driver
        # Configure logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def click_start_interview_button(self):
        try:
            self.logger.info("Attempting to click start interview button")
            start_interview_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='button']"))
            )
            start_interview_button.click()
            self.logger.info("Successfully clicked start interview button")
        except Exception as e:
            self.logger.error(f"Error clicking start interview button: {e}")

    def close_instructions_popup(self):
        try:
            self.logger.info("Checking for instructions popup")
            instructions_popup = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='modal-body']"))
            )
            if instructions_popup:
                self.logger.info("Instructions popup found - attempting to close")
                close_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='extend-close-btn']"))
                )
                close_button.click()
                self.logger.info("Successfully closed instructions popup")
            else:
                self.logger.info("No instructions popup found")
        except Exception as e:
            self.logger.error(f"Error closing instructions popup: {e}")

    def start_calicration(self):
        try:
            self.logger.info("Starting calibration process")
            # Wait for the calibration button to be clickable
            calibration_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='calibration-mech']"))
            )
            calibration_button.click()
            self.logger.info("Calibration started successfully")
        except Exception as e:
            self.logger.error(f"Error starting calibration: {e}")

    def end_interview(self):
        try:
            self.logger.info("Ending interview process")
            end_interview_button = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//button[@class='interview-questions-view-header-action']"))
                
            )
            # self.logger.info("Finding button for ending interview process")
            if end_interview_button:
                self.logger.info("Finding button for ending interview process")
                click_end_interview_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='interview-questions-view-header-action']"))
                )
                click_end_interview_button.click()
            else:
                self.logger.info("Interview ended successfully")
        except Exception as e:
            self.logger.error(f"Error ending interview: {e}")

    def navigate_to_summary_page(self):
        try:
            self.logger.info("Navigating to summary page")
            Detail_feedback_button = WebDriverWait(self.driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='blackTextApp']"))
            )
            Detail_feedback_button.click()
            self.logger.info("Successfully navigated to Detail_feedback page")
        except Exception as e:
            self.logger.error(f"Error navigating to Detail_feedback page: {e}")        

