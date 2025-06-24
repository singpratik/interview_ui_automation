from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logging_config import logger
import logging
import time

logger = logging.getLogger(__name__)

class UiAutomationHelper:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 20  # Default timeout value, configurable
        # Configure logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def click_start_interview_button(self):
        try:
            self.logger.info("Attempting to click start interview button")
            # Try the first XPath
            start_interview_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='interview-questions-view-header-action']"))
            )
            start_interview_button.click()
            self.logger.info("Successfully clicked start interview button")
        except Exception as e:
            self.logger.warning(f"First XPath failed: {e}. Trying alternative XPath.")
            try:
                # Try the alternative XPath
                start_interview_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/div/div/div[5]/div/div[1]/div/div/div/div[2]/div/div/div[2]/div[1]/button"))
                )
                start_interview_button.click()
                self.logger.info("Successfully clicked start interview button using alternative XPath")
            except Exception as e:
                self.logger.error(f"Error clicking start interview button: {e}")

    def close_instructions_popup(self):
        try:
            self.logger.info("Checking for instructions popup")
            instructions_popup = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='modal-content']"))
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
            Find_feedback_button = WebDriverWait(self.driver, 120).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='blackTextApp']"))
            )
            if Find_feedback_button:
                self.logger.info("Feedback button found, clicking to navigate to summary page")
                click_detail_feedback_button = WebDriverWait(self.driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@class='blackTextApp']"))
                )
                click_detail_feedback_button.click()
                self.logger.info("Successfully clicked on detailed feedback page")
            else:
                self.logger.info("Successfully navigated to Detail_feedback page")
        except Exception as e:
            self.logger.error(f"Error navigating to Detail_feedback page: {e}") 

    def explore_non_verbal_feedback(self):
        """
        ul = WebDriverWait(self.driver, self.timeout).until(

        This method waits for the visibility of a <ul> element containing submodule items,
        iterates through each <li> item, scrolls into view, clicks on it, and waits for 2 seconds
        between clicks. It logs errors if any item cannot be clicked.

        Expected Behavior:
        - The method interacts with all <li> elements under the <ul> with the CSS class 'submodule-list'.

        Parameters:
        - None

        Returns:
        - None
        """
            # Wait until the <ul> element is visible
        ul = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//ul[contains(@class, 'system-feedback-nav js-sf-top-nav nav nav-justified')]"))
        )

        # Find all <li> items under the <ul>
        li_items = ul.find_elements(By.XPATH, ".//li[contains(@class, 'submodule-item')]")

        for item in li_items:
            try:
                # Scroll to the item if needed
                self.driver.execute_script("arguments[0].scrollIntoView(true);", item)
                item.click()
                WebDriverWait(self.driver, 10).until(
                    EC.staleness_of(item)
                )  # Wait until the clicked item is no longer attached to the DOM
                # Optionally wait for something to load or verify after click
            except Exception as e:
                self.logger.error(f"Could not click on item: {e}")

    def explore_Delivery_of_speech(self):
            """
            This method explores the 'Delivery of Speech' section by clicking on each item in the list.
            It waits for the list to be visible, iterates through each item, scrolls into view, clicks on it,
            and waits for 2 seconds between clicks. It logs errors if any item cannot be clicked.

            Expected Behavior:
            - The method interacts with all items under the 'Delivery of Speech' section.

            Parameters:
            - None

            Returns:
            - None
            """
            # Wait until the <ul> nav is visible
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "li.active.js-tour-active-icon[role='tablist'][aria-label='navlist']")
                )
            )
            # Wait until the div with the specified class is visible
            sidebar_container = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.sidebar-submodule-sidebar-container.inactive"))
            )

            # Find the <ul> element inside the div
            ul_element = sidebar_container.find_element(By.CSS_SELECTOR, "ul.submodule-list.js-tour-sidenav")

            # Find all <li> items under the <ul>
            li_items = ul_element.find_elements(By.CSS_SELECTOR, "li.submodule-item")

            # Iterate through each <li> item and click on it
            for item in li_items:
                try:
                    # Scroll to the item if needed
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    item.click()
                    WebDriverWait(self.driver, 10).until(
                        EC.staleness_of(item)
                    )  # Wait until the clicked item is no longer attached to the DOM
                    # Optionally wait for something to load or verify after click
                except Exception as e:
                    self.logger.error(f"Could not click on item: {e}")

            
