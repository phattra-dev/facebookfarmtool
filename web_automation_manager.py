from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
from locators import FacebookLocators

class WebAutomationManager:
    """A class to handle all core web automation interactions with Facebook."""

    def __init__(self, driver, signals, account_uid, config_manager, db_manager=None):
        """
        Initialize the WebAutomationManager.

        Args:
            driver: The Selenium WebDriver instance.
            signals: The WorkerSignals instance for emitting logs and updates.
            account_uid: The UID of the account being processed.
            config_manager: The application's ConfigManager.
            db_manager: The AccountDBManager instance for updating account status (optional).
        """
        self.driver = driver
        self.signals = signals
        self.account_uid = account_uid
        self.config_manager = config_manager
        self.db_manager = db_manager

    def human_delay(self, min_sec=1, max_sec=3):
        """Introduce a random delay to mimic human behavior."""
        time.sleep(random.uniform(min_sec, max_sec))

    def wait_and_find_element(self, locator_tuple, timeout=10, condition=EC.presence_of_element_located):
        """
        Wait for an element to be present and return it.

        Args:
            locator_tuple: A tuple (By.<METHOD>, "selector").
            timeout: Maximum time to wait.
            condition: The expected condition (e.g., presence_of_element_located, element_to_be_clickable).

        Returns:
            The WebElement if found, None otherwise.
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                condition(locator_tuple)
            )
            return element
        except TimeoutException:
            self.signals.log.emit(f"Timeout waiting for element: {locator_tuple}")
            return None
        except Exception as e:
            self.signals.log.emit(f"Error finding element {locator_tuple}: {e}")
            return None

    def wait_and_find_elements(self, locator_tuple, timeout=10):
        """
        Wait for elements to be present and return a list.

        Args:
            locator_tuple: A tuple (By.<METHOD>, "selector").
            timeout: Maximum time to wait.

        Returns:
            A list of WebElements, empty if none found or timeout.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator_tuple)
            )
            return self.driver.find_elements(*locator_tuple)
        except TimeoutException:
            self.signals.log.emit(f"Timeout waiting for elements: {locator_tuple}")
            return []
        except Exception as e:
            self.signals.log.emit(f"Error finding elements {locator_tuple}: {e}")
            return []

    def is_logged_in(self):
        """Check if the user is logged in by looking for specific elements."""
        for locator in FacebookLocators.LOGGED_IN_INDICATORS:
            element = self.wait_and_find_element(locator, timeout=8)
            if element and element.is_displayed():
                return True
        return False

    def react_to_post(self, react_type='like'):
        """React to the current post with a specific emotion."""
        try:
            self.signals.log.emit(f"Attempting to react with {react_type} for UID: {self.account_uid}")

            # Find the main reaction button
            reaction_button = None
            for locator in FacebookLocators.REACTION_BUTTONS:
                reaction_button = self.wait_and_find_element(locator, timeout=5)
                if reaction_button and reaction_button.is_displayed():
                    break

            if not reaction_button:
                self.signals.interaction.emit(self.account_uid, "React", "Failed - Button not found")
                return False

            # Scroll to and hover over the button
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
            self.human_delay(1, 2)
            ActionChains(self.driver).move_to_element(reaction_button).perform()
            self.human_delay(1, 2)

            # Click to open reactions
            try:
                reaction_button.click()
            except WebDriverException:
                self.driver.execute_script("arguments[0].click();", reaction_button)
            self.human_delay(1, 2)

            # Find the specific reaction
            if react_type in FacebookLocators.REACTION_TYPES:
                for locator in FacebookLocators.REACTION_TYPES[react_type]:
                    reaction_element = self.wait_and_find_element(locator, timeout=5, condition=EC.element_to_be_clickable)
                    if reaction_element and reaction_element.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_element)
                        self.human_delay(0.5, 1)
                        try:
                            reaction_element.click()
                        except WebDriverException:
                            self.driver.execute_script("arguments[0].click();", reaction_element)
                        self.human_delay(1, 2)
                        self.signals.interaction.emit(self.account_uid, f"React ({react_type})", "Success")
                        # Increment task count
                        if self.db_manager:
                            self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                        return True

                # Fallback: Click the main button if specific reaction fails
                try:
                    reaction_button.click()
                    self.human_delay(1, 2)
                    self.signals.interaction.emit(self.account_uid, "React (Like)", "Success")
                    if self.db_manager:
                        self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                    return True
                except WebDriverException:
                    pass

            else:
                # Just click the main button for unknown types
                try:
                    reaction_button.click()
                    self.human_delay(1, 2)
                    self.signals.interaction.emit(self.account_uid, "React (Like)", "Success")
                    if self.db_manager:
                        self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                    return True
                except WebDriverException:
                    pass

            self.signals.interaction.emit(self.account_uid, f"React ({react_type})", "Failed - Could not click")
            return False

        except Exception as e:
            self.signals.interaction.emit(self.account_uid, "React", f"Error: {str(e)}")
            self.signals.log.emit(f"Error reacting to post: {e}")
            return False

    def like_post(self):
        """Like the current post."""
        try:
            # Check if already liked
            for locator in FacebookLocators.ALREADY_LIKED_INDICATORS:
                element = self.wait_and_find_element(locator, timeout=3)
                if element and element.is_displayed():
                    self.signals.interaction.emit(self.account_uid, "Like", "Already liked")
                    return True

            # Find and click the like button
            like_button = None
            for locator in FacebookLocators.LIKE_BUTTONS:
                like_button = self.wait_and_find_element(locator, timeout=5)
                if like_button and like_button.is_displayed():
                    break

            if like_button:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
                self.human_delay(1, 2)
                try:
                    like_button.click()
                except WebDriverException:
                    self.driver.execute_script("arguments[0].click();", like_button)
                self.human_delay(1, 2)
                self.signals.interaction.emit(self.account_uid, "Like", "Success")
                # Increment task count
                if self.db_manager:
                    self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                return True
            else:
                self.signals.interaction.emit(self.account_uid, "Like", "Failed - Button not found")
                return False

        except Exception as e:
            self.signals.interaction.emit(self.account_uid, "Like", f"Error: {str(e)}")
            self.signals.log.emit(f"Error liking post: {e}")
            return False

    def comment_on_post(self, comment_text):
        """Comment on the current post."""
        try:
            # Scroll down
            self.driver.execute_script("window.scrollBy(0, 500);")
            self.human_delay(2, 3)

            # Find the comment box
            comment_box = None
            for locator in FacebookLocators.COMMENT_BOXES:
                comment_box = self.wait_and_find_element(locator, timeout=10)
                if comment_box and comment_box.is_displayed():
                    break

            if not comment_box:
                self.signals.interaction.emit(self.account_uid, "Comment", "Failed - Comment box not found")
                return False

            # Interact with the comment box
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_box)
            self.human_delay(1, 2)
            comment_box.click()
            self.human_delay(1, 2)

            # Clear and type comment
            self.driver.execute_script("arguments[0].innerText = '';", comment_box)
            self.human_delay(0.5, 1)
            for char in comment_text:
                comment_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            self.human_delay(1, 2)

            # Find and click the post button
            post_button = None
            for locator in FacebookLocators.POST_BUTTONS:
                post_button = self.wait_and_find_element(locator, timeout=5, condition=EC.element_to_be_clickable)
                if post_button and post_button.is_displayed():
                    break

            if post_button:
                post_button.click()
            else:
                # Fallback: Press Enter
                comment_box.send_keys(Keys.ENTER)

            self.human_delay(2, 4)
            self.signals.interaction.emit(self.account_uid, "Comment", "Success")
            # Increment task count
            if self.db_manager:
                self.db_manager.update_account_status(self.account_uid, "Working", False, True)
            return True

        except Exception as e:
            self.signals.interaction.emit(self.account_uid, "Comment", f"Error: {str(e)}")
            self.signals.log.emit(f"Error commenting on post: {e}")
            return False

    def share_post(self):
        """Share the current post."""
        try:
            self.signals.log.emit(f"Attempting to share post for UID: {self.account_uid}")

            # Find the share button
            share_button = None
            for locator in FacebookLocators.SHARE_BUTTONS:
                elements = self.wait_and_find_elements(locator)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        share_button = element
                        break
                if share_button:
                    break

            if not share_button:
                self.signals.interaction.emit(self.account_uid, "Share", "Failed - Button not found")
                return False

            # Scroll to and click the share button
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
            self.human_delay(1, 2)
            try:
                share_button.click()
            except WebDriverException:
                self.driver.execute_script("arguments[0].click();", share_button)
            self.human_delay(2, 4)

            # Find the "Share Now" button
            share_now_button = None
            for locator in FacebookLocators.SHARE_NOW_BUTTONS:
                share_now_button = self.wait_and_find_element(locator, timeout=5, condition=EC.element_to_be_clickable)
                if share_now_button and share_now_button.is_displayed():
                    break

            if share_now_button:
                self.human_delay(1, 2)
                try:
                    share_now_button.click()
                except WebDriverException:
                    self.driver.execute_script("arguments[0].click();", share_now_button)
                self.human_delay(3, 5)
                self.signals.interaction.emit(self.account_uid, "Share", "Success")
                # Increment task count
                if self.db_manager:
                    self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                return True
            else:
                # Fallback: Try to find any share option in a menu
                menu_items = self.wait_and_find_elements((By.XPATH, "//div[@role='menuitem']"))
                for item in menu_items:
                    try:
                        if "Share" in item.text or "Post" in item.text:
                            item.click()
                            self.human_delay(3, 5)
                            self.signals.interaction.emit(self.account_uid, "Share", "Success")
                            if self.db_manager:
                                self.db_manager.update_account_status(self.account_uid, "Working", False, True)
                            return True
                    except Exception:
                        continue

            self.signals.interaction.emit(self.account_uid, "Share", "Failed - Share Now option not found")
            return False

        except Exception as e:
            self.signals.interaction.emit(self.account_uid, "Share", f"Error: {str(e)}")
            self.signals.log.emit(f"Error sharing post: {e}")
            return False

    def check_for_captcha(self):
        """Check if a CAPTCHA or security challenge is present."""
        for locator in FacebookLocators.CAPTCHA_INDICATORS:
            elements = self.wait_and_find_elements(locator, timeout=3)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    self.signals.log.emit(f"⚠️  CAPTCHA or Security Check detected for UID: {self.account_uid}.")
                    return True
        return False