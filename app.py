import sys
import time
import random
import os
import json
import pyperclip
import psutil
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer, QDate, QItemSelectionModel, QUrl, QThreadPool, QRunnable, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMenu, QMessageBox, QProgressBar, QLabel, QHeaderView, QLineEdit,
    QGroupBox, QSplitter, QFrame, QCheckBox, QSizePolicy,
    QDialog, QDialogButtonBox, QInputDialog, QTabWidget, QComboBox, QFormLayout,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QFileDialog
)
from PyQt6.QtGui import QFont, QColor, QIcon, QPalette, QBrush, QDesktopServices
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from screeninfo import get_monitors  # For cross-platform screen resolution detection

# --- ADDED: Import the new Database Manager ---
from db_manager import AccountDBManager
# --- END ADDED ---

# --- ADDED: Configuration Manager (Unchanged) ---
class ConfigManager:
    """Handles loading and saving application settings."""
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "delay_min": 5,
            "delay_max": 15,
            "use_proxy": False,
            "headless": False,
            "save_profiles": True,
            "session_persistence": True,
            "auto_relogin_on_failure": True,
            # --- NEW: Session Management Settings ---
            "reuse_sessions": True,
            "session_storage": "profile",  # or "cookies"
            "session_path": "chrome_profiles",  # or "cookies"
            # --- NEW: Grid Layout Settings ---
            "grid_layout": True,
            "grid_spacing": 10,
            "default_window_size": [800, 600],
            # --- NEW: Concurrency Settings ---
            "max_concurrent_browsers": 3  # Maximum number of parallel browsers
        }
        # Initialize self.config BEFORE calling load_config
        self.config = self.default_config.copy()  # <-- THIS IS THE CRITICAL FIX
        self.config = self.load_config()  # Now safe to call
    def load_config(self):
        """Load config from file or return defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Ensure all keys from default are present
                    for key, value in self.default_config.items():
                        if key not in loaded:
                            loaded[key] = value
                    return loaded
            else:
                self.save_config()
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    def save_config(self):
        """Save current config to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    def get(self, key, default=None):
        """Get a config value."""
        return self.config.get(key, default)
    def set(self, key, value):
        """Set a config value and save."""
        self.config[key] = value
        self.save_config()
# --- END ADDED ---

class SystemMonitorWidget(QWidget):
    """Widget to display real-time CPU and RAM usage with a professional design."""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_monitoring()
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(25)
        # CPU Display
        cpu_frame = QFrame()
        cpu_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cpu_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 12px;
                border: 1px solid #404040;
            }
        """)
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_layout.setContentsMargins(15, 12, 15, 12)
        cpu_layout.setSpacing(5)
        cpu_title = QLabel("CPU USAGE")
        cpu_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        cpu_title.setStyleSheet("color: #AAAAAA; letter-spacing: 0.5px;")
        cpu_layout.addWidget(cpu_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.cpu_value = QLabel("--%")
        self.cpu_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.cpu_value.setStyleSheet("color: #FFB07C;")
        cpu_layout.addWidget(self.cpu_value, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cpu_frame)
        # RAM Display
        ram_frame = QFrame()
        ram_frame.setFrameShape(QFrame.Shape.StyledPanel)
        ram_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 12px;
                border: 1px solid #404040;
            }
        """)
        ram_layout = QVBoxLayout(ram_frame)
        ram_layout.setContentsMargins(15, 12, 15, 12)
        ram_layout.setSpacing(5)
        ram_title = QLabel("RAM USAGE")
        ram_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        ram_title.setStyleSheet("color: #AAAAAA; letter-spacing: 0.5px;")
        ram_layout.addWidget(ram_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.ram_value = QLabel("--%")
        self.ram_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.ram_value.setStyleSheet("color: #7CB9E8;")
        ram_layout.addWidget(self.ram_value, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ram_frame)
        # Accounts Info
        accounts_frame = QFrame()
        accounts_frame.setFrameShape(QFrame.Shape.StyledPanel)
        accounts_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 12px;
                border: 1px solid #404040;
            }
        """)
        accounts_layout = QVBoxLayout(accounts_frame)
        accounts_layout.setContentsMargins(15, 12, 15, 12)
        accounts_layout.setSpacing(5)
        accounts_title = QLabel("TOTAL ACCOUNTS")
        accounts_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        accounts_title.setStyleSheet("color: #AAAAAA; letter-spacing: 0.5px;")
        accounts_layout.addWidget(accounts_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.accounts_value = QLabel("0")
        self.accounts_value.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.accounts_value.setStyleSheet("color: #A9DFBF;")
        accounts_layout.addWidget(self.accounts_value, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(accounts_frame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(100)
    def start_monitoring(self):
        """Start a timer to update system stats every 2 seconds."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)
        self.update_stats()
    def update_stats(self):
        """Fetch and display current CPU and RAM usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            ram_percent = psutil.virtual_memory().percent
            self.cpu_value.setText(f"{cpu_percent:.1f}%")
            self.ram_value.setText(f"{ram_percent:.1f}%")
            if cpu_percent > 80:
                self.cpu_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
            else:
                self.cpu_value.setStyleSheet("color: #FFB07C;")
            if ram_percent > 80:
                self.ram_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
            else:
                self.ram_value.setStyleSheet("color: #7CB9E8;")
        except Exception as e:
            print(f"Error updating system stats: {e}")
    def stop_monitoring(self):
        """Stop the monitoring timer."""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
    def update_accounts_count(self, count):
        """Update the accounts count display"""
        self.accounts_value.setText(str(count))

# --- MODIFIED: Removed the old AccountManager class. It is replaced by AccountDBManager. ---

# --- NEW: Worker Signals Class (Unchanged) ---
class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = pyqtSignal(int, str)  # row_index, status
    log = pyqtSignal(str)
    interaction = pyqtSignal(str, str, str)  # uid, action, status
    account_status = pyqtSignal(str, str, bool, bool)  # uid, status, increment_login_count, increment_task_count
    task_completed = pyqtSignal(str)  # uid - for task count increment
    progress = pyqtSignal(int)  # completed count
# --- END NEW ---

# --- MODIFIED: Individual Account Worker ---
class AccountWorker(QRunnable):
    """Worker thread for handling individual account login and actions."""
    def __init__(self, account_data, row_index, use_proxies, post_url, comment_text, actions, random_comments, react_type, db_manager, target_group_url, schedule_actions, config_manager, proxy=None, window_position=None):
        super().__init__()
        
        # Get UID for logging
        if isinstance(account_data, dict):
            uid_for_debug = account_data.get('uid', 'Unknown')
        elif isinstance(account_data, (list, tuple)) and len(account_data) > 0:
            uid_for_debug = account_data[0]
        else:
            uid_for_debug = 'Unknown'
        
        print(f"🔧 DEBUG: AccountWorker.__init__ for UID: {uid_for_debug}")
        print(f"🔧 DEBUG: Received parameters:")
        print(f"   - post_url: {post_url}")
        print(f"   - actions: {actions}")
        print(f"   - react_type: {react_type}")
        print(f"   - comment_text: {'Yes' if comment_text else 'No'}")
        print(f"   - random_comments: {'Yes' if random_comments else 'No'}")
        
        self.account_data = account_data
        self.row_index = row_index
        self.use_proxies = use_proxies
        self.post_url = post_url
        self.comment_text = comment_text
        self.actions = actions if actions else []
        self.random_comments = random_comments if random_comments else []
        self.react_type = react_type
        
        print(f"🔧 DEBUG: After assignment:")
        print(f"   - self.post_url: {self.post_url}")
        print(f"   - self.actions: {self.actions}")
        print(f"   - self.react_type: {self.react_type}")
        
        # --- MODIFIED: Use db_manager instead of account_manager ---
        self.db_manager = db_manager
        # --- END MODIFIED ---
        self.target_group_url = target_group_url
        self.schedule_actions = schedule_actions if schedule_actions else []
        self.config_manager = config_manager
        self.proxy = proxy
        self.window_position = window_position
        self.signals = WorkerSignals()
        self.driver = None
        self.running = True

    def run(self):
        """Process the account in this thread."""
        try:
            # Handle different account formats
            if isinstance(self.account_data, dict):
                uid = self.account_data['uid']
                password = self.account_data['password']
                token = self.account_data['token']
                cookie_str = self.account_data['cookie']
            else:
                uid, password, token, cookie_str = self.account_data

            success = False
            login_success = False  # Track if login was successful

            try:
                # --- ENHANCED: Session Management with Configurable Storage ---
                reuse_sessions = self.config_manager.get("reuse_sessions", True)
                session_storage = self.config_manager.get("session_storage", "profile")
                if reuse_sessions and self.has_valid_session(uid):
                    if session_storage == "profile":
                        success, self.driver = self.login_with_profile_session(uid)
                    else:  # cookies
                        success, self.driver = self.login_with_cookie_session(uid)
                    if success:
                        status = "Success (Session)"
                        self.signals.log.emit(f"✓ Reusing existing session for UID: {uid}")
                        login_success = True  # Session reuse counts as successful login
                    else:
                        # Session expired or invalid, try other login methods
                        self.signals.log.emit(f"⚠️ Session expired for UID: {uid}, trying normal login")
                        if token and cookie_str:
                            success, self.driver = self.login_with_token_cookie_stealth(uid, token, cookie_str)
                            status = "Success (Token)" if success else "Failed (Token)"
                            login_success = success
                        elif uid and password:
                            success, self.driver = self.login_with_uid_pass_stealth(uid, password)
                            status = "Success (Pass)" if success else "Failed (Pass)"
                            login_success = success
                        else:
                            status = "Skipped - Incomplete info"
                            self.driver = None
                else:
                    # No session available, try token/cookie first, then password
                    if token and cookie_str:
                        success, self.driver = self.login_with_token_cookie_stealth(uid, token, cookie_str)
                        status = "Success (Token)" if success else "Failed (Token)"
                        login_success = success
                    elif uid and password:
                        success, self.driver = self.login_with_uid_pass_stealth(uid, password)
                        status = "Success (Pass)" if success else "Failed (Pass)"
                        login_success = success
                    else:
                        status = "Skipped - Incomplete info"
                        self.driver = None
                # --- END ENHANCED ---

                # Update account status in database
                # --- MODIFIED: Emit signal to update DB ---
                if self.db_manager:
                    self.signals.account_status.emit(uid, "Working" if login_success else "Failed", login_success, False)
                # --- END MODIFIED ---

                # If login successful, perform actions based on context
                if login_success and self.driver:
                    self.signals.log.emit(f"✅ LOGIN SUCCESS for UID: {uid}")
                    self.signals.log.emit(f"🔍 DEBUG: post_url={self.post_url}")
                    self.signals.log.emit(f"🔍 DEBUG: actions={self.actions}")
                    self.signals.log.emit(f"🔍 DEBUG: schedule_actions={self.schedule_actions}")
                    
                    # Save session for future use
                    if reuse_sessions:
                        if session_storage == "cookies":
                            cookies = self.driver.get_cookies()
                            self.save_account_session(uid, cookies)
                            self.signals.log.emit(f"Session saved for UID: {uid}")

                    if self.post_url:
                        self.signals.log.emit(f"🎯 CALLING perform_post_actions for UID: {uid}")
                        self.perform_post_actions(self.driver, uid)
                    elif self.schedule_actions:
                        self.signals.log.emit(f"📅 CALLING perform_scheduled_actions for UID: {uid}")
                        self.perform_scheduled_actions(self.driver, uid)
                    elif hasattr(self, 'automation_actions') and self.automation_actions:
                        self.signals.log.emit(f"🤖 CALLING perform_automation_actions for UID: {uid}")
                        self.perform_automation_actions(self.driver, uid)
                    else:
                        self.signals.log.emit(f"⚠️ NO ACTIONS TO PERFORM for UID: {uid}")

                self.signals.finished.emit(self.row_index, status)

                # Random delay between accounts to appear more human
                min_delay = self.config_manager.get("delay_min", 5)
                max_delay = self.config_manager.get("delay_max", 15)
                time.sleep(random.uniform(min_delay, max_delay))

                # --- AUTO-CLOSE BROWSER ---
                if self.driver:
                    try:
                        self.driver.quit()
                        self.signals.log.emit(f"Browser auto-closed for UID: {uid}")
                    except Exception as e:
                        self.signals.log.emit(f"Error closing browser for UID {uid}: {e}")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.signals.finished.emit(self.row_index, error_msg)
                if self.db_manager:
                    self.signals.account_status.emit(uid, "Error", False, False)
                # Ensure browser closes even on error
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass

        except Exception as e:
            self.signals.log.emit(f"Critical error in worker: {str(e)}")
            self.signals.finished.emit(self.row_index, f"Critical Error: {str(e)}")
        finally:
            self.signals.progress.emit(1)  # Signal that this worker has completed

    # --- Helper Methods for Session Management (adapted for SQLite) ---
    def has_valid_session(self, uid):
        """Check if account has a valid session file (placeholder, logic remains the same)"""
        # This logic is filesystem-based and doesn't change with the DB.
        # You might want to store a `has_valid_session` flag in the DB in the future.
        session_storage = self.config_manager.get("session_storage", "profile")
        session_path = self.config_manager.get("session_path", "chrome_profiles")
        if session_storage == "cookies":
            session_file_path = os.path.join(os.getcwd(), session_path, f"session_{uid}.json")
            return os.path.exists(session_file_path)
        elif session_storage == "profile":
            profile_path = os.path.join(os.getcwd(), session_path, f"profile_{uid}")
            return os.path.exists(profile_path)
        return False

    def save_account_session(self, uid, cookies):
        """Save cookies to session file (placeholder, logic remains the same)"""
        # This is filesystem-based. The DB doesn't store the cookies, just metadata.
        session_storage = self.config_manager.get("session_storage", "profile")
        session_path = self.config_manager.get("session_path", "chrome_profiles")
        if session_storage == "cookies":
            session_dir = os.path.join(os.getcwd(), session_path)
            os.makedirs(session_dir, exist_ok=True)
            session_file_path = os.path.join(session_dir, f"session_{uid}.json")
            try:
                with open(session_file_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                print(f"Saved session for UID: {uid}")
            except Exception as e:
                print(f"Error saving session for UID {uid}: {e}")

    # --- Login Methods (mostly unchanged, but adapted for worker) ---
    def login_with_profile_session(self, uid):
        """Login using saved Chrome profile"""
        profile_dir = os.path.join(os.getcwd(), "chrome_profiles", f"profile_{uid}")
        os.makedirs(profile_dir, exist_ok=True)
        options = uc.ChromeOptions()
        options.user_data_dir = profile_dir
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Add proxy if available
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        # Headless mode
        if self.config_manager.get("headless", False):
            options.add_argument("--headless")
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            self.driver = driver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.signals.log.emit(f"Attempting profile session login for UID: {uid}")
            driver.get("https://www.facebook.com")
            # Apply grid layout positioning
            if self.window_position:
                x, y, width, height = self.window_position
                try:
                    driver.set_window_size(width, height)
                    driver.set_window_position(x, y)
                    self.signals.log.emit(f"Positioned window at ({x}, {y}) with size {width}x{height}")
                except Exception as e:
                    self.signals.log.emit(f"Error setting window position/size: {e}")
            self.human_delay(3, 5)
            # Check if login was successful
            if self.is_logged_in(driver):
                self.signals.log.emit(f"✓ Successfully logged in via profile session for UID: {uid}")
                return True, driver
            else:
                self.signals.log.emit(f"✗ Profile session login failed for UID: {uid}")
                return False, driver
        except Exception as e:
            self.signals.log.emit(f"Profile session login error for {uid}: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False, None

    def login_with_cookie_session(self, uid):
        """Login using saved cookies"""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Add proxy if available
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        # Headless mode
        if self.config_manager.get("headless", False):
            options.add_argument("--headless")
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            self.driver = driver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.signals.log.emit(f"Attempting cookie session login for UID: {uid}")
            driver.get("https://www.facebook.com")
            # Apply grid layout positioning
            if self.window_position:
                x, y, width, height = self.window_position
                try:
                    driver.set_window_size(width, height)
                    driver.set_window_position(x, y)
                    self.signals.log.emit(f"Positioned window at ({x}, {y}) with size {width}x{height}")
                except Exception as e:
                    self.signals.log.emit(f"Error setting window position/size: {e}")
            self.human_delay(2, 4)
            # Load saved cookies
            cookies = self.load_account_session(uid)
            if cookies:
                for cookie in cookies:
                    try:
                        # Ensure cookie has required fields
                        if 'name' in cookie and 'value' in cookie:
                            cookie_dict = {
                                'name': cookie['name'],
                                'value': cookie['value'],
                                'domain': cookie.get('domain', '.facebook.com'),
                                'path': cookie.get('path', '/'),
                                'secure': cookie.get('secure', True),
                                'httpOnly': cookie.get('httpOnly', False),
                                'sameSite': cookie.get('sameSite', 'None')
                            }
                            driver.add_cookie(cookie_dict)
                    except Exception as e:
                        self.signals.log.emit(f"Error adding cookie for UID {uid}: {e}")
                        continue
                # Refresh to apply cookies
                driver.refresh()
                self.human_delay(3, 5)
                # Check if login was successful
                if self.is_logged_in(driver):
                    self.signals.log.emit(f"✓ Successfully logged in via cookie session for UID: {uid}")
                    return True, driver
                else:
                    self.signals.log.emit(f"✗ Cookie session login failed for UID: {uid}")
                    return False, driver
            else:
                self.signals.log.emit(f"No session found for UID: {uid}")
                return False, driver
        except Exception as e:
            self.signals.log.emit(f"Cookie session login error for {uid}: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False, None

    def is_logged_in(self, driver):
        """Check if user is logged in by looking for specific elements"""
        logged_in_selectors = [
            "//div[@aria-label='Account']",
            "//span[contains(text(), 'Home')]",
            "//a[@aria-label='Messenger']",
            "//div[@id='userNav']",
            "//span[contains(text(), 'Groups')]",
            "//div[@role='navigation']//a[@href='/']",
            "//div[@aria-label='Create post']",
            "//div[@aria-label='What's on your mind?']",
            "//div[@aria-label='Create a post']",
            "//span[contains(text(), 'News Feed')]",
            "//div[@role='banner']//a[@href='/']"
        ]
        for selector in logged_in_selectors:
            try:
                element = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if element.is_displayed():
                    return True
            except:
                continue
        return False

    def perform_post_actions(self, driver, uid):
        """Perform actions on the post (like, comment, etc.)"""
        try:
            self.signals.log.emit(f"🎯 STARTING perform_post_actions for UID: {uid}")
            self.signals.log.emit(f"🔍 DEBUG: post_url={self.post_url}")
            self.signals.log.emit(f"🔍 DEBUG: actions={self.actions}")
            self.signals.log.emit(f"🔍 DEBUG: react_type={self.react_type}")
            self.signals.log.emit(f"🔍 DEBUG: comment_text={self.comment_text}")
            self.signals.log.emit(f"🔍 DEBUG: random_comments={'Yes' if self.random_comments else 'No'}")
            
            self.signals.log.emit(f"🌐 Navigating to post URL: {self.post_url}")
            driver.get(self.post_url)
            self.signals.log.emit(f"✅ Navigation complete, waiting for page load...")
            self.human_delay(3, 5)
            # Wait for post to load
            post_selectors = [
                "//div[contains(@role, 'article') or contains(@data-pagelet, 'Feed')]",
                "//div[@data-pagelet='FeedUnit']",
                "//div[@role='feed']//div[@role='article']",
                "//div[contains(@class, 'story_body_container')]",
                "//div[contains(@class, 'userContentWrapper')]"
            ]
            post_element = None
            for selector in post_selectors:
                try:
                    post_element = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if post_element.is_displayed():
                        break
                except:
                    continue
            if not post_element:
                self.signals.log.emit(f"❌ ERROR: Could not find post element for UID: {uid}")
                self.signals.log.emit(f"🔍 DEBUG: Current URL: {driver.current_url}")
                self.signals.log.emit(f"🔍 DEBUG: Page title: {driver.title}")
                return

            self.signals.log.emit(f"✅ Post element found! Starting actions...")
            self.signals.log.emit(f"🎯 Actions to perform: {self.actions}")
            
            # Perform actions based on selection
            if 'react' in self.actions and self.react_type:
                self.signals.log.emit(f"🔄 Executing REACT action with type: {self.react_type}")
                self.react_to_post(driver, uid, self.react_type)
            if 'like' in self.actions:
                self.signals.log.emit(f"🔄 Executing LIKE action")
                self.like_post(driver, uid)
            if 'comment' in self.actions:
                self.signals.log.emit(f"🔄 Executing COMMENT action")
                comment_text = self.get_comment_text()
                self.signals.log.emit(f"📝 Comment text: {comment_text[:50] if comment_text else 'EMPTY'}")
                if comment_text:
                    self.comment_on_post(driver, uid, comment_text)
                else:
                    self.signals.log.emit(f"⚠️ No comment text available - skipping comment action")
            if 'share' in self.actions:
                self.signals.log.emit(f"🔄 Executing SHARE action")
                self.share_post(driver, uid)
            
            self.signals.log.emit(f"✅ All actions completed for UID: {uid}")
        except Exception as e:
            self.signals.log.emit(f"Error performing actions for {uid}: {e}")

    def share_post(self, driver, uid):
        """Share the post to timeline or friends"""
        try:
            self.signals.log.emit(f"Attempting to share post for UID: {uid}")
            # Find share button - try multiple selectors
            share_selectors = [
                "//div[@aria-label='Send this to friends or post it on your Timeline.']",
                "//div[@aria-label='Share']",
                "//div[contains(@aria-label, 'Share')]//span[text()='Share']",
                "//div[contains(@class, 'share_button')]//div[@role='button']",
                "//div[@data-testid='UFI2ShareLink']",
                "//div[contains(@class, 'reaction')]/following::div[contains(@aria-label, 'Share')][1]",
                "//div[@role='button' and contains(@aria-label, 'Send this to friends')]",
                "//span[text()='Share']/ancestor::div[@role='button']"
            ]
            share_button = None
            for selector in share_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            share_button = element
                            break
                    if share_button:
                        break
                except:
                    continue
            if not share_button:
                self.signals.interaction.emit(uid, "Share", "Failed - Button not found")
                self.signals.log.emit(f"✗ Share button not found for UID: {uid}")
                return

            # Scroll to button and click
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
            self.human_delay(1, 2)
            try:
                share_button.click()
            except:
                # Try JavaScript click if normal click fails
                driver.execute_script("arguments[0].click();", share_button)
            self.human_delay(2, 4)

            # Now find the "Share Now" or "Post to Timeline" option
            share_now_selectors = [
                "//span[text()='Share Now' or text()='Share to News Feed']",
                "//div[@aria-label='Share Now' or @aria-label='Share to News Feed']",
                "//span[contains(text(), 'Share Now')]",
                "//div[contains(@aria-label, 'Share Now')]",
                "//div[@role='menuitem']//span[text()='Share Now']",
                "//div[@role='menuitem']//div[@aria-label='Share Now']"
            ]
            share_now_button = None
            for selector in share_now_selectors:
                try:
                    share_now_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if share_now_button.is_displayed():
                        break
                except:
                    continue

            if share_now_button:
                self.human_delay(1, 2)
                try:
                    share_now_button.click()
                except:
                    driver.execute_script("arguments[0].click();", share_now_button)
                self.human_delay(3, 5)
                self.signals.interaction.emit(uid, "Share", "Success")
                # --- ADDED: Increment task count ---
                self.signals.task_completed.emit(uid)
                # --- END ADDED ---
                self.signals.log.emit(f"✓ Shared post for UID: {uid}")
            else:
                # Try to find any share option
                menu_items = driver.find_elements(By.XPATH, "//div[@role='menuitem']")
                for item in menu_items:
                    try:
                        if "Share" in item.text or "Post" in item.text:
                            item.click()
                            self.human_delay(3, 5)
                            self.signals.interaction.emit(uid, "Share", "Success")
                            # --- ADDED: Increment task count ---
                            self.signals.task_completed.emit(uid)
                            # --- END ADDED ---
                            self.signals.log.emit(f"✓ Shared post for UID: {uid}")
                            return
                    except:
                        continue
                self.signals.interaction.emit(uid, "Share", "Failed - Share Now option not found")
                self.signals.log.emit(f"✗ Share Now option not found for UID: {uid}")
        except Exception as e:
            self.signals.interaction.emit(uid, "Share", f"Error: {str(e)}")
            self.signals.log.emit(f"Error sharing post for {uid}: {e}")

    def perform_scheduled_actions(self, driver, uid):
        """Perform scheduled actions with more detailed implementation."""
        for action in self.schedule_actions:
            if not self.running:
                break
            try:
                if action == "View Feed":
                    self.signals.log.emit(f"Simulating 'View Feed' for UID: {uid}")
                    driver.get("https://www.facebook.com/")
                    self.human_delay(5, 10)
                    # Scroll down multiple times with random pauses
                    scroll_count = random.randint(5, 10)
                    for _ in range(scroll_count):
                        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.7);")
                        pause_duration = random.uniform(2, 5)
                        time.sleep(pause_duration)
                        # Occasionally, try to click on a random post or story to simulate engagement
                        if random.random() < 0.3: # 30% chance
                            try:
                                # Find a random post
                                posts = driver.find_elements(By.XPATH, "//div[@role='article']")
                                if posts:
                                    random_post = random.choice(posts)
                                    # Try to find a clickable element within the post (e.g., author name, timestamp)
                                    clickable_elements = random_post.find_elements(By.XPATH, ".//a | .//span[@role='link']")
                                    if clickable_elements:
                                        target = random.choice(clickable_elements)
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                                        self.human_delay(1, 2)
                                        target.click()
                                        self.human_delay(3, 5) # Wait on the clicked page
                                        driver.back() # Go back to feed
                                        self.human_delay(2, 3)
                            except Exception as e:
                                self.signals.log.emit(f"Minor error during feed interaction: {e}")
                                continue
                    # --- ADDED: Increment task count ---
                    self.signals.task_completed.emit(uid)
                    # --- END ADDED ---
                elif action == "React to Friends' Posts":
                    self.signals.log.emit(f"Simulating 'React to Friends' Posts' for UID: {uid}")
                    driver.get("https://www.facebook.com/")
                    self.human_delay(5, 10)
                    # Define possible reactions
                    possible_reactions = ['like', 'love', 'care', 'haha', 'wow', 'sad', 'angry']
                    # Find posts in the feed
                    # Using a more specific selector for the main feed container
                    feed_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='feed']"))
                    )
                    # Find articles within the feed
                    posts = feed_container.find_elements(By.XPATH, ".//div[@role='article']")
                    reacted_count = 0
                    for post in posts[:5]: # Limit to first 5 to avoid being too aggressive
                        if not self.running:
                            break
                        if reacted_count >= 3: # Limit total reactions per session
                            break
                        try:
                            # Look for the reaction button within this post
                            # This is a common structure, but Facebook changes it often
                            reaction_button = post.find_element(By.XPATH, ".//div[@aria-label='Like' or @aria-label='Thích'] | .//div[@aria-label='Like this post' or @aria-label='Thích bài viết này']")
                            # Scroll to the button
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
                            self.human_delay(1, 2)
                            # Hover to reveal reaction options
                            ActionChains(driver).move_to_element(reaction_button).perform()
                            self.human_delay(1, 2)
                            # Click to open the reaction tray
                            reaction_button.click()
                            self.human_delay(1, 2)
                            # Choose a random reaction
                            chosen_reaction = random.choice(possible_reactions)
                            # Define selectors for different reactions
                            reaction_selectors = {
                                'like': "//div[@aria-label='Like' or @aria-label='Thích']",
                                'love': "//div[@aria-label='Love' or @aria-label='Yêu thích']",
                                'care': "//div[@aria-label='Care' or @aria-label='Thương thương']",
                                'haha': "//div[@aria-label='Haha' or @aria-label='Haha']",
                                'wow': "//div[@aria-label='Wow' or @aria-label='Wow']",
                                'sad': "//div[@aria-label='Sad' or @aria-label='Buồn']",
                                'angry': "//div[@aria-label='Angry' or @aria-label='Phẫn nộ']"
                            }
                            if chosen_reaction in reaction_selectors:
                                try:
                                    # Wait for the specific reaction to be clickable
                                    specific_reaction = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, reaction_selectors[chosen_reaction]))
                                    )
                                    specific_reaction.click()
                                    reacted_count += 1
                                    self.signals.log.emit(f"Reacted with '{chosen_reaction}' to a post.")
                                    self.human_delay(2, 4)
                                except TimeoutException:
                                    # If specific reaction not found, just like it
                                    self.signals.log.emit(f"Specific reaction '{chosen_reaction}' not found, defaulting to 'Like'.")
                                    # The tray might still be open, clicking the main button again might close it or like it.
                                    # We'll just move on.
                                    pass
                            else:
                                self.signals.log.emit(f"Unknown reaction type: {chosen_reaction}")
                        except NoSuchElementException:
                            self.signals.log.emit(f"No reaction button found for a post. Skipping.")
                            continue
                        except Exception as e:
                            self.signals.log.emit(f"Error reacting to a post: {e}")
                            continue
                    # --- ADDED: Increment task count ---
                    if reacted_count > 0:
                        self.signals.task_completed.emit(uid)
                    # --- END ADDED ---
                elif action == "Invite Friends to Group" and self.target_group_url:
                    self.signals.log.emit(f"Simulating 'Invite Friends to Group' for UID: {uid}")
                    driver.get(self.target_group_url)
                    self.human_delay(5, 10)
                    # Navigate to Members section
                    members_selectors = [
                        "//div[@aria-label='Members']",
                        "//span[text()='Members']",
                        "//a[contains(@href, '/members/')]",
                        "//div[contains(text(), 'Members')]",
                        "//div[@role='tab' and contains(text(), 'Members')]"
                    ]
                    members_tab = None
                    for selector in members_selectors:
                        try:
                            members_tab = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if members_tab.is_displayed():
                                members_tab.click()
                                self.human_delay(2, 4)
                                break
                        except:
                            continue
                    if not members_tab:
                        self.signals.log.emit(f"Could not find Members tab for UID: {uid}")
                        continue
                    # Look for "Invite" or "Add Members" button
                    invite_selectors = [
                        "//div[@aria-label='Invite' or @aria-label='Mời']",
                        "//span[text()='Invite' or text()='Mời']",
                        "//div[contains(@aria-label, 'Invite')]//div[@role='button']",
                        "//div[@aria-label='Add Members']",
                        "//span[text()='Add Members']",
                        "//div[contains(@aria-label, 'Add Members')]//div[@role='button']",
                        "//div[@role='button' and contains(text(), 'Invite')]",
                        "//div[@role='button' and contains(text(), 'Add Members')]"
                    ]
                    invite_button = None
                    for selector in invite_selectors:
                        try:
                            invite_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if invite_button.is_displayed():
                                invite_button.click()
                                self.human_delay(2, 4)
                                break
                        except:
                            continue
                    if not invite_button:
                        self.signals.log.emit(f"Could not find Invite/Add Members button for UID: {uid}")
                        continue
                    # Wait for invite dialog to appear
                    invite_dialog_selectors = [
                        "//div[@role='dialog']",
                        "//div[@aria-label='Invite friends to group']",
                        "//div[contains(@aria-label, 'Invite')]",
                        "//div[contains(text(), 'Invite friends')]"
                    ]
                    invite_dialog = None
                    for selector in invite_dialog_selectors:
                        try:
                            invite_dialog = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if invite_dialog.is_displayed():
                                break
                        except:
                            continue
                    if not invite_dialog:
                        self.signals.log.emit(f"Invite dialog did not appear for UID: {uid}")
                        continue
                    # Find friends to invite - this is tricky as Facebook limits visibility
                    # We'll try to find all visible friend elements and invite them
                    friend_selectors = [
                        "//div[@role='checkbox']",
                        "//div[@aria-label='Select']",
                        "//div[contains(@aria-label, 'Invite')]//div[@role='button']",
                        "//div[@role='button' and contains(@aria-label, 'Invite')]",
                        "//div[@role='button' and contains(text(), 'Invite')]",
                        "//div[contains(@class, 'friend') or contains(@class, 'user')]//div[@role='button']"
                    ]
                    invited_count = 0
                    max_invites = 10  # Limit to avoid being flagged
                    for selector in friend_selectors:
                        try:
                            friend_elements = driver.find_elements(By.XPATH, selector)
                            for friend in friend_elements:
                                if invited_count >= max_invites:
                                    break
                                if friend.is_displayed() and friend.is_enabled():
                                    try:
                                        # Scroll to friend element
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", friend)
                                        self.human_delay(0.5, 1)
                                        # Click to invite
                                        friend.click()
                                        invited_count += 1
                                        self.signals.log.emit(f"Invited friend {invited_count} for UID: {uid}")
                                        self.human_delay(1, 2)
                                        # Check if we've reached the limit
                                        if invited_count >= max_invites:
                                            break
                                    except Exception as e:
                                        self.signals.log.emit(f"Error inviting individual friend: {e}")
                                        continue
                            if invited_count > 0:
                                break
                        except Exception as e:
                            self.signals.log.emit(f"Error finding friends with selector {selector}: {e}")
                            continue
                    # If no friends were found with above selectors, try scrolling and finding more
                    if invited_count == 0:
                        self.signals.log.emit(f"No friends found to invite for UID: {uid}")
                        continue
                    # Look for "Send Invites" or "Done" button
                    send_invites_selectors = [
                        "//div[@aria-label='Send Invites']",
                        "//span[text()='Send Invites']",
                        "//div[@aria-label='Done']",
                        "//span[text()='Done']",
                        "//div[@role='button' and contains(text(), 'Send')]",
                        "//div[@role='button' and contains(text(), 'Done')]"
                    ]
                    send_button = None
                    for selector in send_invites_selectors:
                        try:
                            send_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if send_button.is_displayed():
                                send_button.click()
                                self.signals.log.emit(f"Sent {invited_count} invites for UID: {uid}")
                                self.human_delay(3, 5)
                                break
                        except:
                            continue
                    if not send_button:
                        self.signals.log.emit(f"Could not find Send Invites/Done button for UID: {uid}")
                        continue
                    self.signals.log.emit(f"✓ Successfully invited {invited_count} friends to group for UID: {uid}")
                    # --- ADDED: Increment task count ---
                    if invited_count > 0:
                        self.signals.task_completed.emit(uid)
                    # --- END ADDED ---
                elif action == "Share to Wall":
                    self.signals.log.emit(f"Simulating 'Share to Wall' for UID: {uid}")
                    driver.get("https://www.facebook.com/")
                    self.human_delay(5, 10)
                    # --- ENHANCED: Find and use the "What's on your mind?" box ---
                    # Common selectors for the create post box
                    create_post_selectors = [
                        "//span[contains(text(), 'on your mind') or contains(text(), 'Bạn đang nghĩ gì thế?')]/ancestor::div[@role='button']",
                        "//div[@aria-label='Create a post' or @aria-label='Tạo bài viết']",
                        "//div[contains(@class, 'create_post')]//div[@role='button']",
                        "//div[@role='button' and @aria-label='What\'s on your mind?']",
                        "//div[@role='button' and contains(@aria-label, 'Create post')]",
                        "//div[@role='button' and contains(text(), 'What\'s on your mind?')]",
                        "//div[@role='button' and contains(text(), 'on your mind')]"
                    ]
                    create_post_button = None
                    for selector in create_post_selectors:
                        try:
                            create_post_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if create_post_button.is_displayed():
                                break
                        except:
                            continue
                    if create_post_button:
                        create_post_button.click()
                        self.human_delay(2, 4)
                        # Now find the text input area within the dialog
                        # Switch to the active element or find the textbox
                        try:
                            # Wait for the modal/dialog to appear
                            post_dialog = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                            )
                            # Find the textbox within the dialog
                            textbox = post_dialog.find_element(By.XPATH, ".//div[@role='textbox' and @contenteditable='true']")
                            textbox.click()
                            self.human_delay(1, 2)
                            # Type a simple message
                            sample_messages = [
                                "Hello from my automated script!",
                                "Just testing the share function.",
                                "Have a great day!",
                                "Posted via automation.",
                                "Automated post from my Facebook bot!",
                                "Testing automated content sharing.",
                                "This post was created automatically!",
                                "Hello Facebook friends! Just sharing some automated content."
                            ]
                            message = random.choice(sample_messages)
                            for char in message:
                                textbox.send_keys(char)
                                time.sleep(random.uniform(0.05, 0.2))
                            self.human_delay(1, 2)
                            # Find and click the "Post" button
                            post_button_selectors = [
                                "//div[@aria-label='Post' or @aria-label='Đăng']",
                                "//span[text()='Post' or text()='Đăng']/ancestor::div[@role='button']",
                                "//div[@data-testid='react-composer-post-button']",
                                "//div[@role='button' and contains(text(), 'Post')]",
                                "//div[@role='button' and contains(text(), 'Đăng')]",
                                "//div[@role='button' and @aria-label='Publish']"
                            ]
                            post_button = None
                            for selector in post_button_selectors:
                                try:
                                    post_button = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                    if post_button.is_displayed():
                                        break
                                except:
                                    continue
                            if post_button:
                                post_button.click()
                                self.signals.log.emit(f"Shared a post to the wall.")
                                # Wait for the post to be published
                                self.human_delay(3, 5)
                                # --- ADDED: Increment task count ---
                                self.signals.task_completed.emit(uid)
                                # --- END ADDED ---
                            else:
                                self.signals.log.emit(f"Could not find 'Post' button.")
                        except Exception as e:
                            self.signals.log.emit(f"Error while trying to share to wall: {e}")
                    else:
                        self.signals.log.emit(f"Could not find 'Create Post' button.")
                elif action == "Share to Group" and self.target_group_url:
                    self.signals.log.emit(f"Simulating 'Share to Group' for UID: {uid}")
                    driver.get(self.target_group_url)
                    self.human_delay(5, 10)
                    # --- ENHANCED: Similar to "Share to Wall" but within a group ---
                    # Look for the group's post composer
                    group_post_selectors = [
                        "//span[contains(text(), 'Write something') or contains(text(), 'Viết nội dung...')]/ancestor::div[@role='button']",
                        "//div[@aria-label='Write something...' or @aria-label='Viết nội dung...']",
                        "//div[contains(@class, 'group_post')]//div[@role='button']",
                        "//div[@role='button' and @aria-label='Write something...']",
                        "//div[@role='button' and contains(text(), 'Write something')]",
                        "//div[@role='button' and contains(text(), 'Viết nội dung')]"
                    ]
                    group_post_button = None
                    for selector in group_post_selectors:
                        try:
                            group_post_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if group_post_button.is_displayed():
                                break
                        except:
                            continue
                    if group_post_button:
                        group_post_button.click()
                        self.human_delay(2, 4)
                        try:
                            # Wait for the input area
                            textbox = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']"))
                            )
                            textbox.click()
                            self.human_delay(1, 2)
                            sample_messages = [
                                "Hello group members!",
                                "Sharing this from my script.",
                                "Hope you all are having a good week!",
                                "Automated group post.",
                                "Hello from the automation bot!",
                                "Testing group sharing functionality.",
                                "This post was shared automatically!",
                                "Greetings from my Facebook automation tool!"
                            ]
                            message = random.choice(sample_messages)
                            for char in message:
                                textbox.send_keys(char)
                                time.sleep(random.uniform(0.05, 0.2))
                            self.human_delay(1, 2)
                            # Find and click the "Post" button
                            post_button_selectors = [
                                "//div[@aria-label='Post' or @aria-label='Đăng']",
                                "//span[text()='Post' or text()='Đăng']/ancestor::div[@role='button']",
                                "//div[@role='button' and contains(text(), 'Post')]",
                                "//div[@role='button' and contains(text(), 'Đăng')]",
                                "//div[@role='button' and @aria-label='Publish']"
                            ]
                            post_button = None
                            for selector in post_button_selectors:
                                try:
                                    post_button = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                    if post_button.is_displayed():
                                        break
                                except:
                                    continue
                            if post_button:
                                post_button.click()
                                self.signals.log.emit(f"Shared a post to the group.")
                                self.human_delay(3, 5)
                                # --- ADDED: Increment task count ---
                                self.signals.task_completed.emit(uid)
                                # --- END ADDED ---
                            else:
                                self.signals.log.emit(f"Could not find 'Post' button in group.")
                        except Exception as e:
                            self.signals.log.emit(f"Error while trying to share to group: {e}")
                    else:
                        self.signals.log.emit(f"Could not find group post composer.")
            except Exception as e:
                self.signals.log.emit(f"Error performing scheduled action '{action}' for {uid}: {e}")

    def get_comment_text(self):
        """Get comment text - either from random comments or the main comment text"""
        if self.random_comments:
            return random.choice(self.random_comments)
        return self.comment_text

    def react_to_post(self, driver, uid, react_type):
        """React to the post with a specific emotion - ENHANCED VERSION"""
        try:
            self.signals.log.emit(f"😊 START: react_to_post with {react_type} for UID: {uid}")
            # First, try to find the reaction button container
            reaction_container_selectors = [
                "//div[@aria-label='Like' or @aria-label='Like this post']",
                "//div[contains(@aria-label, 'Like') and @role='button']",
                "//div[@data-testid='ufi-inline-reaction']",
                "//div[contains(@class, 'reaction')]",
                "//div[contains(@aria-label, 'React')]",
                "//span[text()='Like']/ancestor::div[@role='button']",
                "//div[@aria-label='React' or @aria-label='Phản ứng']",
                "//div[@role='button' and contains(@aria-label, 'Like')]",
                "//div[@role='button' and contains(@aria-label, 'React')]"
            ]
            reaction_button = None
            for selector in reaction_container_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            reaction_button = element
                            break
                    if reaction_button:
                        break
                except:
                    continue
            if not reaction_button:
                # Try one more approach - look for any button with like in aria-label
                try:
                    elements = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'like') or contains(@aria-label, 'Like')]")
                    for element in elements:
                        if element.is_displayed() and "button" in element.get_attribute("role"):
                            reaction_button = element
                            break
                except:
                    pass
            if reaction_button and reaction_button.is_displayed():
                # Scroll to the button
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
                self.human_delay(1, 2)
                # Try to hover to reveal reactions
                try:
                    ActionChains(driver).move_to_element(reaction_button).perform()
                    self.human_delay(1, 2)
                except:
                    pass
                # Click to open reactions if needed
                try:
                    reaction_button.click()
                    self.human_delay(1, 2)
                except:
                    pass
                # Now find the specific reaction
                reaction_selectors = {
                    'like': [
                        "//div[@aria-label='Like']",
                        "//div[contains(@aria-label, 'Like')]//span[text()='Like']",
                        "//div[contains(@aria-label, 'Like')]//div[contains(@class, 'like')]",
                        "//div[@data-testid='react_love']//preceding::div[@aria-label='Like'][1]",
                        "//div[@aria-label='Like' or @aria-label='Thích']",
                        "//div[@role='button' and @aria-label='Like']"
                    ],
                    'love': [
                        "//div[@aria-label='Love']",
                        "//div[contains(@aria-label, 'Love')]//span[text()='Love']",
                        "//div[@data-testid='react_love']",
                        "//div[contains(@class, 'love')]",
                        "//div[@aria-label='Love' or @aria-label='Yêu thích']",
                        "//div[@role='button' and @aria-label='Love']"
                    ],
                    'care': [
                        "//div[@aria-label='Care']",
                        "//div[contains(@aria-label, 'Care')]//span[text()='Care']",
                        "//div[@data-testid='react_care']",
                        "//div[contains(@class, 'care')]",
                        "//div[@aria-label='Care' or @aria-label='Thương thương']",
                        "//div[@role='button' and @aria-label='Care']"
                    ],
                    'haha': [
                        "//div[@aria-label='Haha']",
                        "//div[contains(@aria-label, 'Haha')]//span[text()='Haha']",
                        "//div[@data-testid='react_haha']",
                        "//div[contains(@class, 'haha')]",
                        "//div[@aria-label='Haha']",
                        "//div[@role='button' and @aria-label='Haha']"
                    ],
                    'wow': [
                        "//div[@aria-label='Wow']",
                        "//div[contains(@aria-label, 'Wow')]//span[text()='Wow']",
                        "//div[@data-testid='react_wow']",
                        "//div[contains(@class, 'wow')]",
                        "//div[@aria-label='Wow']",
                        "//div[@role='button' and @aria-label='Wow']"
                    ],
                    'sad': [
                        "//div[@aria-label='Sad']",
                        "//div[contains(@aria-label, 'Sad')]//span[text()='Sad']",
                        "//div[@data-testid='react_sad']",
                        "//div[contains(@class, 'sad')]",
                        "//div[@aria-label='Sad' or @aria-label='Buồn']",
                        "//div[@role='button' and @aria-label='Sad']"
                    ],
                    'angry': [
                        "//div[@aria-label='Angry']",
                        "//div[contains(@aria-label, 'Angry')]//span[text()='Angry']",
                        "//div[@data-testid='react_angry']",
                        "//div[contains(@class, 'angry')]",
                        "//div[@aria-label='Angry' or @aria-label='Phẫn nộ']",
                        "//div[@role='button' and @aria-label='Angry']"
                    ]
                }
                if react_type in reaction_selectors:
                    reaction_found = False
                    for selector in reaction_selectors[react_type]:
                        try:
                            reaction_element = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if reaction_element.is_displayed():
                                # Scroll to element
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_element)
                                self.human_delay(0.5, 1)
                                # Try clicking
                                try:
                                    reaction_element.click()
                                    reaction_found = True
                                    break
                                except:
                                    # If click fails, try JavaScript click
                                    try:
                                        driver.execute_script("arguments[0].click();", reaction_element)
                                        reaction_found = True
                                        break
                                    except:
                                        continue
                        except:
                            continue
                    if reaction_found:
                        self.human_delay(1, 2)
                        self.signals.interaction.emit(uid, f"React ({react_type})", "Success")
                        # --- ADDED: Increment task count ---
                        self.signals.task_completed.emit(uid)
                        # --- END ADDED ---
                        self.signals.log.emit(f"✓ Reacted with {react_type} for UID: {uid}")
                    else:
                        # Fallback: Just click the main reaction button
                        try:
                            reaction_button.click()
                            self.human_delay(1, 2)
                            self.signals.interaction.emit(uid, "React (Like)", "Success")
                            # --- ADDED: Increment task count ---
                            self.signals.task_completed.emit(uid)
                            # --- END ADDED ---
                            self.signals.log.emit(f"✓ Liked post for UID: {uid} (specific reaction not available)")
                        except:
                            self.signals.interaction.emit(uid, f"React ({react_type})", "Failed - Could not click")
                            self.signals.log.emit(f"✗ Could not click reaction {react_type} for UID: {uid}")
                else:
                    # Just click the main reaction button
                    try:
                        reaction_button.click()
                        self.human_delay(1, 2)
                        self.signals.interaction.emit(uid, "React (Like)", "Success")
                        # --- ADDED: Increment task count ---
                        self.signals.task_completed.emit(uid)
                        # --- END ADDED ---
                        self.signals.log.emit(f"✓ Liked post for UID: {uid}")
                    except:
                        self.signals.interaction.emit(uid, "React", "Failed - Could not click")
                        self.signals.log.emit(f"✗ Could not click reaction button for UID: {uid}")
            else:
                self.signals.interaction.emit(uid, "React", "Failed - Button not found")
                self.signals.log.emit(f"✗ React button not found for UID: {uid}")
        except Exception as e:
            self.signals.interaction.emit(uid, "React", f"Error: {str(e)}")
            self.signals.log.emit(f"Error reacting to post for {uid}: {e}")

    def like_post(self, driver, uid):
        """Like the post"""
        try:
            self.signals.log.emit(f"👍 START: like_post for UID: {uid}")
            # Find like buttons - try different selectors
            like_selectors = [
                "//div[@aria-label='Like' or @aria-label='Like this post']",
                "//span[text()='Like' or text()='Like this post']",
                "//a[contains(@aria-pressed, 'false') and contains(@role, 'button') and contains(@aria-label, 'Like')]",
                "//div[contains(@aria-label, 'Like') and not(contains(@aria-pressed, 'true'))]",
                "//div[contains(@data-testid, 'fb-ufi-likelink')]",
                "//div[@aria-label='Like' or @aria-label='Thích']",
                "//div[@role='button' and @aria-label='Like']",
                "//div[@role='button' and contains(@aria-label, 'Like')]"
            ]
            like_button = None
            for selector in like_selectors:
                try:
                    like_button = driver.find_element(By.XPATH, selector)
                    if like_button.is_displayed():
                        break
                except:
                    continue
            if like_button and like_button.is_displayed():
                # Scroll to the button to ensure it's clickable
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
                self.human_delay(1, 2)
                like_button.click()
                self.human_delay(1, 2)
                self.signals.interaction.emit(uid, "Like", "Success")
                # --- ADDED: Increment task count ---
                self.signals.task_completed.emit(uid)
                # --- END ADDED ---
                self.signals.log.emit(f"✓ Liked post for UID: {uid}")
            else:
                # Check if already liked
                already_liked_selectors = [
                    "//div[@aria-label='Unlike' or @aria-label='Unlike this post']",
                    "//span[text()='Liked' or text()='Unlike']",
                    "//div[contains(@aria-label, 'Like') and contains(@aria-pressed, 'true')]",
                    "//div[@aria-label='Unlike' or @aria-label='Bỏ thích']",
                    "//div[@role='button' and @aria-label='Unlike']"
                ]
                for selector in already_liked_selectors:
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        if element.is_displayed():
                            self.signals.interaction.emit(uid, "Like", "Already liked")
                            self.signals.log.emit(f"✓ Post already liked for UID: {uid}")
                            return
                    except:
                        continue
                self.signals.interaction.emit(uid, "Like", "Failed - Button not found")
                self.signals.log.emit(f"✗ Like button not found for UID: {uid}")
        except Exception as e:
            self.signals.interaction.emit(uid, "Like", f"Error: {str(e)}")
            self.signals.log.emit(f"Error liking post for {uid}: {e}")

    def comment_on_post(self, driver, uid, comment_text):
        """Comment on the post"""
        try:
            self.signals.log.emit(f"💬 START: comment_on_post for UID: {uid}")
            self.signals.log.emit(f"📝 Comment text to post: {comment_text[:50]}")
            # Scroll down a bit to make sure comment box is visible
            driver.execute_script("window.scrollBy(0, 500);")
            self.human_delay(2, 3)
            # Find comment box - try different selectors
            comment_selectors = [
                "//div[contains(@aria-label, 'Write a comment')]",
                "//div[contains(@aria-label, 'Write a comment')]//div[@role='textbox']",
                "//div[contains(@class, 'commentable_item')]//div[contains(@role, 'textbox')]",
                "//form[contains(@class, 'comment_form')]//div[contains(@role, 'textbox')]",
                "//div[contains(@data-testid, 'ufi_comment_composer')]//div[contains(@role, 'textbox')]",
                "//div[contains(@class, 'notranslate') and @role='textbox']",
                "//textarea[contains(@aria-label, 'Write a comment')]",
                "//div[@role='textbox' and @aria-label='Write a comment...']",
                "//div[@contenteditable='true' and @role='textbox']"
            ]
            comment_box = None
            for selector in comment_selectors:
                try:
                    comment_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if comment_box.is_displayed():
                        break
                except:
                    continue
            if comment_box and comment_box.is_displayed():
                # Scroll to the comment box
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_box)
                self.human_delay(1, 2)
                # Click to focus
                comment_box.click()
                self.human_delay(1, 2)
                # Clear any existing text
                driver.execute_script("arguments[0].innerText = '';", comment_box)
                self.human_delay(0.5, 1)
                # Type comment with human-like delays
                for char in comment_text:
                    if not self.running:
                        return
                    comment_box.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2))
                self.human_delay(1, 2)
                # Find and click post button or press Enter
                post_selectors = [
                    "//div[@aria-label='Press Enter to post' or @aria-label='Comment']",
                    "//button[contains(@type, 'submit') and contains(@value, 'Post')]",
                    "//div[contains(text(), 'Comment') and @role='button']",
                    "//input[@value='Post' or @value='Comment']",
                    "//div[contains(@aria-label, 'Post')]",
                    "//div[@aria-label='Comment']",
                    "//div[@role='button' and contains(text(), 'Comment')]",
                    "//div[@role='button' and contains(@aria-label, 'Comment')]"
                ]
                post_button = None
                for selector in post_selectors:
                    try:
                        post_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if post_button.is_displayed():
                            break
                    except:
                        continue
                if post_button and post_button.is_displayed():
                    post_button.click()
                else:
                    # Try pressing Enter if button not found
                    comment_box.send_keys(Keys.ENTER)
                self.human_delay(2, 4)
                self.signals.interaction.emit(uid, "Comment", "Success")
                # --- ADDED: Increment task count ---
                self.signals.task_completed.emit(uid)
                # --- END ADDED ---
                self.signals.log.emit(f"✓ Commented on post for UID: {uid}")
            else:
                self.signals.interaction.emit(uid, "Comment", "Failed - Comment box not found")
                self.signals.log.emit(f"✗ Comment box not found for UID: {uid}")
        except Exception as e:
            self.signals.interaction.emit(uid, "Comment", f"Error: {str(e)}")
            self.signals.log.emit(f"Error commenting on post for {uid}: {e}")

    def human_delay(self, min_sec=1, max_sec=3):
        if self.running:
            time.sleep(random.uniform(min_sec, max_sec))

    def login_with_uid_pass_stealth(self, uid, pw):
        """Stealth UID/Pass login with undetected chromedriver - WITH SESSION REUSE"""
        profile_dir = os.path.join(os.getcwd(), "chrome_profiles", f"profile_{uid}")
        os.makedirs(profile_dir, exist_ok=True)
        options = uc.ChromeOptions()
        options.user_data_dir = profile_dir
        options.add_argument("--window-size=800,600")  # Open with small size
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Add proxy if available
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            self.driver = driver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # --- NEW: Apply grid layout positioning ---
            if self.window_position:
                x, y, width, height = self.window_position
                try:
                    driver.set_window_size(width, height)
                    driver.set_window_position(x, y)
                    self.signals.log.emit(f"Positioned window at ({x}, {y}) with size {width}x{height}")
                except Exception as e:
                    self.signals.log.emit(f"Error setting window position/size: {e}")
            # --- END NEW ---
            # --- NEW: Check if already logged in FIRST ---
            driver.get("https://www.facebook.com/")
            self.human_delay(3, 5)
            # Check for elements that indicate a logged-in state
            if self.is_logged_in(driver):
                self.signals.log.emit(f"✓ Session reused for UID: {uid} (Already Logged In)")
                return True, driver
            # --- If not logged in, proceed with normal login ---
            self.signals.log.emit(f"Session not found. Logging in UID: {uid}")
            driver.get("https://www.facebook.com/login")
            self.human_delay(2, 4)
            # Wait for email field
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            # Clear field first
            email_field.clear()
            self.human_delay(0.5, 1)
            # Type with human-like delays
            for char in uid:
                if not self.running:
                    break
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            self.human_delay(1, 2)
            # Find password field
            password_field = driver.find_element(By.ID, "pass")
            password_field.clear()
            self.human_delay(0.5, 1)
            for char in pw:
                if not self.running:
                    break
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            self.human_delay(1, 2)
            # Click login button
            login_button = driver.find_element(By.NAME, "login")
            login_button.click()
            # Wait for login to complete
            self.human_delay(5, 8)
            # Check if login was successful
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@role, 'main')] | //div[@id='userNav'] | //span[contains(text(), 'Home')]"))
                )
                self.signals.log.emit(f"Successfully logged in UID={uid}")
                # Save cookies for potential future use
                if self.config_manager.get("reuse_sessions", True) and self.config_manager.get("session_storage", "profile") == "cookies":
                    cookies = driver.get_cookies()
                    self.save_account_session(uid, cookies)
                return True, driver
            except:
                self.signals.log.emit(f"Login may have failed for UID={uid}")
                # Check for error message
                try:
                    error_element = driver.find_element(By.XPATH, "//div[contains(text(), 'incorrect') or contains(text(), 'Invalid') or contains(text(), 'error') or contains(text(), 'Wrong')]")
                    if error_element:
                        self.signals.log.emit(f"Error message: {error_element.text[:50]}...")
                except:
                    pass
                return False, driver
        except Exception as e:
            self.signals.log.emit(f"UID/Pass login error for {uid}: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False, None

    def login_with_token_cookie_stealth(self, uid, token, cookie_str):
        """Stealth login via token + cookie"""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # --- ADDED: Headless Mode ---
        if self.config_manager.get("headless", False):
            options.add_argument("--headless")
        # --- END ADDED ---
        # Add proxy if available
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            self.driver = driver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # --- NEW: Apply grid layout positioning ---
            if self.window_position:
                x, y, width, height = self.window_position
                try:
                    driver.set_window_size(width, height)
                    driver.set_window_position(x, y)
                    self.signals.log.emit(f"Positioned window at ({x}, {y}) with size {width}x{height}")
                except Exception as e:
                    self.signals.log.emit(f"Error setting window position/size: {e}")
            # --- END NEW ---
            self.signals.log.emit(f"Logging in with token for UID: {uid}")
            driver.get("https://www.facebook.com")
            self.human_delay(2, 4)
            # Parse and set cookies
            cookies = self.parse_cookies(cookie_str)
            for cookie in cookies:
                try:
                    driver.add_cookie({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.facebook.com')
                    })
                except Exception as e:
                    self.signals.log.emit(f"Error adding cookie {cookie.get('name','?')}: {e}")
            # Set the token as a cookie too if it's not already in the cookie string
            if token and not any(c.get('name') == 'token' for c in cookies):
                try:
                    driver.add_cookie({
                        'name': 'token',
                        'value': token,
                        'domain': '.facebook.com'
                    })
                except Exception as e:
                    self.signals.log.emit(f"Error adding token cookie: {e}")
            driver.refresh()
            self.human_delay(3, 5)
            # Check if login was successful
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@role, 'main')] | //div[@id='userNav'] | //span[contains(text(), 'Home')]"))
                )
                self.signals.log.emit("Successfully logged in via token/cookie")
                # Save cookies for future use
                if self.config_manager.get("reuse_sessions", True) and self.config_manager.get("session_storage", "profile") == "cookies":
                    cookies = driver.get_cookies()
                    self.save_account_session(uid, cookies)
                # --- ENHANCED: Check for CAPTCHA or Verification ---
                # List of potential indicators for security challenges
                captcha_indicators = [
                    "//div[contains(text(), 'security check')]",
                    "//div[contains(text(), 'CAPTCHA')]",
                    "//div[contains(text(), 'challenge')]",
                    "//div[contains(text(), 'verify')]",
                    "//iframe[contains(@src, 'captcha')]",
                    "//iframe[contains(@title, 'verification')]",
                    "//div[contains(@class, 'captcha')]",
                    "//div[contains(@class, 'challenge')]",
                    # Look for the image CAPTCHA element
                    "//img[contains(@src, 'captcha')]",
                    # Look for common button texts
                    "//button[contains(text(), 'Continue')]",
                    "//button[contains(text(), 'Submit')]",
                    "//button[contains(text(), 'Verify')]"
                ]
                for indicator in captcha_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                self.signals.log.emit(f"⚠️ CAPTCHA or Security Check detected for UID: {uid}. Marking as 'Error'.")
                                return False, driver
                    except:
                        continue
                return True, driver
            except:
                self.signals.log.emit("Token/Cookie login may have failed")
                return False, driver
        except Exception as e:
            self.signals.log.emit(f"Token/Cookie login error: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False, None

    def parse_cookies(self, cookie_str):
        """Parse cookie string into dictionary format"""
        cookies = []
        try:
            # Try to parse as JSON first
            if cookie_str and (cookie_str.strip().startswith('{') or cookie_str.strip().startswith('[')):
                return json.loads(cookie_str)
        except:
            pass
        if not cookie_str:
            return cookies
        # Parse as string format: name=value; name2=value2
        for cookie in cookie_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                name, value = cookie.split('=', 1)
                cookies.append({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
        return cookies

    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
# --- END MODIFIED ---

# --- NEW: Parallel Login Manager (Mostly unchanged, but uses db_manager) ---
class ParallelLoginManager(QObject):
    """Manages parallel execution of account workers."""
    finished = pyqtSignal()
    progress_updated = pyqtSignal(int, int)  # completed, total
    worker_finished = pyqtSignal(int, str)  # row_index, status
    log_message = pyqtSignal(str)
    interaction_update = pyqtSignal(str, str, str)  # uid, action, status
    account_status_update = pyqtSignal(str, str, bool, bool)  # uid, status, increment_login_count, increment_task_count
    task_completed = pyqtSignal(str)  # uid
    def __init__(self, accounts, use_proxies, post_url, comment_text, actions, random_comments, react_type, db_manager, target_group_url, schedule_actions, config_manager):
        super().__init__()
        print(f"🔧 DEBUG: ParallelLoginManager.__init__ called")
        print(f"🔧 DEBUG: post_url={post_url}")
        print(f"🔧 DEBUG: actions={actions}")
        print(f"🔧 DEBUG: react_type={react_type}")
        print(f"🔧 DEBUG: comment_text={'Yes' if comment_text else 'No'}")
        print(f"🔧 DEBUG: random_comments={'Yes' if random_comments else 'No'}")
        
        self.accounts = accounts
        self.use_proxies = use_proxies
        self.post_url = post_url
        self.comment_text = comment_text
        self.actions = actions
        self.random_comments = random_comments
        self.react_type = react_type
        # --- MODIFIED: Use db_manager instead of account_manager ---
        self.db_manager = db_manager
        # --- END MODIFIED ---
        self.target_group_url = target_group_url
        self.schedule_actions = schedule_actions
        self.config_manager = config_manager
        self.proxies = self.load_proxies() if use_proxies else []
        self.thread_pool = QThreadPool()
        self.max_concurrent = self.config_manager.get("max_concurrent_browsers", 3)
        self.thread_pool.setMaxThreadCount(self.max_concurrent)
        self.completed_count = 0
        self.total_count = len(accounts)
        self.running = True
        # --- NEW: Grid Layout Management ---
        self.window_positions = []
        if self.config_manager.get("grid_layout", True):
            self.calculate_grid_positions(self.max_concurrent)
    def calculate_grid_positions(self, num_windows):
        """Calculate optimal grid positions for browser windows"""
        try:
            # Get primary monitor resolution
            monitors = get_monitors()
            if monitors:
                primary_monitor = monitors[0]
                screen_width = primary_monitor.width
                screen_height = primary_monitor.height
            else:
                # Fallback for systems where screeninfo doesn't work
                screen_width = 1920
                screen_height = 1080
            # Get config values
            spacing = self.config_manager.get("grid_spacing", 10)
            default_size = self.config_manager.get("default_window_size", [800, 600])
            window_width = default_size[0]
            window_height = default_size[1]
            # Calculate grid dimensions
            if num_windows <= 1:
                cols, rows = 1, 1
            elif num_windows <= 2:
                cols, rows = 2, 1
            elif num_windows <= 4:
                cols, rows = 2, 2
            elif num_windows <= 6:
                cols, rows = 3, 2
            elif num_windows <= 9:
                cols, rows = 3, 3
            else:
                # For more than 9 windows, calculate dynamically
                cols = int(num_windows ** 0.5)
                if cols * cols < num_windows:
                    cols += 1
                rows = (num_windows + cols - 1) // cols
            # Calculate actual window size to fit screen
            available_width = screen_width - (cols + 1) * spacing
            available_height = screen_height - (rows + 1) * spacing - 100  # Leave space for taskbar
            max_window_width = available_width // cols
            max_window_height = available_height // rows
            # Use smaller of configured size or calculated size
            window_width = min(window_width, max_window_width)
            window_height = min(window_height, max_window_height)
            # Calculate positions
            self.window_positions = []
            for i in range(num_windows):
                row = i // cols
                col = i % cols
                x = spacing + col * (window_width + spacing)
                y = spacing + row * (window_height + spacing)
                self.window_positions.append((x, y, window_width, window_height))
            self.log_message.emit(f"Calculated {cols}x{rows} grid layout for {num_windows} concurrent windows")
        except Exception as e:
            self.log_message.emit(f"Error calculating grid positions: {e}")
            # Fallback to default positions
            default_size = self.config_manager.get("default_window_size", [800, 600])
            for i in range(num_windows):
                x = (i % 3) * (default_size[0] + 20)
                y = (i // 3) * (default_size[1] + 20)
                self.window_positions.append((x, y, default_size[0], default_size[1]))
    def load_proxies(self):
        """Load proxies from file if exists"""
        proxies = []
        try:
            if os.path.exists("proxies.txt"):
                with open("proxies.txt", "r") as f:
                    proxies = [line.strip() for line in f.readlines() if line.strip()]
        except:
            pass
        return proxies
    def get_proxy(self, index):
        """Get proxy for account index if available"""
        if self.proxies and index < len(self.proxies):
            return self.proxies[index]
        return None
    def start(self):
        """Start processing all accounts in parallel"""
        self.completed_count = 0
        self.running = True
        # Create and start workers
        for i, account in enumerate(self.accounts):
            if not self.running:
                break
            # Get proxy for this account
            proxy = self.get_proxy(i)
            # Get window position (cycle through available positions)
            window_position = None
            if self.window_positions:
                window_position = self.window_positions[i % len(self.window_positions)]
            
            # Debug logging before creating worker
            self.log_message.emit(f"🔧 DEBUG: Creating AccountWorker {i+1}")
            self.log_message.emit(f"🔧 DEBUG: Passing to worker:")
            self.log_message.emit(f"   - post_url: {self.post_url}")
            self.log_message.emit(f"   - actions: {self.actions}")
            self.log_message.emit(f"   - react_type: {self.react_type}")
            self.log_message.emit(f"   - comment_text: {'Yes' if self.comment_text else 'No'}")
            self.log_message.emit(f"   - random_comments: {'Yes' if self.random_comments else 'No'}")
            
            # Create worker
            worker = AccountWorker(
                account, i, self.use_proxies, self.post_url, self.comment_text, 
                self.actions, self.random_comments, self.react_type, 
                self.db_manager, self.target_group_url, self.schedule_actions, 
                self.config_manager, proxy, window_position
            )
            # Connect signals
            worker.signals.finished.connect(self.on_worker_finished)
            worker.signals.log.connect(self.log_message.emit)
            worker.signals.interaction.connect(self.interaction_update.emit)
            worker.signals.account_status.connect(self.account_status_update.emit)
            worker.signals.task_completed.connect(self.task_completed.emit)
            worker.signals.progress.connect(self.on_worker_progress)
            # Start worker
            self.thread_pool.start(worker)
        # Monitor thread pool
        self.monitor_thread_pool()
    def on_worker_finished(self, row_index, status):
        """Handle worker finished signal"""
        self.worker_finished.emit(row_index, status)
    def on_worker_progress(self, count):
        """Handle worker progress signal"""
        self.completed_count += count
        self.progress_updated.emit(self.completed_count, self.total_count)
        # If all workers are done, emit finished signal
        if self.completed_count >= self.total_count:
            self.finished.emit()
    def monitor_thread_pool(self):
        """Monitor thread pool and emit finished signal when done"""
        # This is handled by the worker progress signals
        pass
    def stop(self):
        """Stop all workers"""
        self.running = False
        # Note: QThreadPool doesn't provide a direct way to cancel all running tasks
        # We rely on workers checking self.running flag
        self.log_message.emit("Stopping all workers...")
# --- END NEW ---

class AddAccountDialog(QDialog):
    """Dialog for adding a new account"""
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Add New Account")
        self.setModal(True)
        self.resize(500, 400)
        layout = QVBoxLayout()
        # Form layout for account details
        form_layout = QFormLayout()
        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("Enter UID (required)")
        form_layout.addRow("UID:", self.uid_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password (optional)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter token (optional)")
        form_layout.addRow("Token:", self.token_input)
        self.cookie_input = QTextEdit()
        self.cookie_input.setMaximumHeight(80)
        self.cookie_input.setPlaceholderText("Enter cookie string (optional)")
        form_layout.addRow("Cookie:", self.cookie_input)
        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        form_layout.addRow("Category:", self.category_combo)
        layout.addLayout(form_layout)
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
    def get_account_data(self):
        """Return the account data from the dialog"""
        return {
            'uid': self.uid_input.text().strip(),
            'password': self.password_input.text().strip(),
            'token': self.token_input.text().strip(),
            'cookie': self.cookie_input.toPlainText().strip(),
            'category': self.category_combo.currentText()
        }

class AddCategoryDialog(QDialog):
    """Dialog for adding a new category"""
    def __init__(self, existing_categories, parent=None):
        super().__init__(parent)
        self.existing_categories = existing_categories
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Add New Category")
        self.setModal(True)
        self.resize(300, 100)
        layout = QVBoxLayout()
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Enter category name")
        layout.addWidget(QLabel("Category Name:"))
        layout.addWidget(self.category_input)
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
    def get_category_name(self):
        """Return the category name from the dialog"""
        return self.category_input.text().strip()

# --- REDESIGNED: Account Selection Dialog (Adapted for SQLite) ---
class AccountSelectionDialog(QDialog):
    """Redesigned dialog for selecting accounts with improved table view."""
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        # --- MODIFIED: Use db_manager instead of account_manager ---
        self.db_manager = db_manager
        # --- END MODIFIED ---
        self.selected_accounts = []
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Select Accounts")
        self.resize(900, 600)
        layout = QVBoxLayout()
        # Search and filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_combo = QComboBox()
        # --- MODIFIED: Get categories from DB ---
        self.category_combo.addItems(["All Categories"] + self.get_categories())
        # --- END MODIFIED ---
        self.category_combo.currentIndexChanged.connect(self.filter_accounts)
        filter_layout.addWidget(self.category_combo)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by UID...")
        self.search_input.textChanged.connect(self.filter_accounts)
        filter_layout.addWidget(self.search_input)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.populate_table)
        filter_layout.addWidget(refresh_btn)
        layout.addLayout(filter_layout)
        # Create table widget with improved styling
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # Updated to 7 columns (added task_count)
        self.table.setHorizontalHeaderLabels(["Select", "UID", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        # Apply styling to table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 8px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QCheckBox {
                margin-left: 15px;
            }
        """)
        # Enable dragging selection
        self.table.setDragEnabled(False)
        self.table.setAcceptDrops(False)
        layout.addWidget(self.table)
        # Buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_accounts)
        button_layout.addWidget(select_all_btn)
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_selections)
        button_layout.addWidget(clear_all_btn)
        button_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        # Populate table
        self.populate_table()
        # Connect right-click context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
    # --- MODIFIED: Get categories from DB ---
    def get_categories(self):
        """Get unique categories from the database."""
        try:
            accounts = self.db_manager.get_all_accounts()
            categories = set(acc['category'] for acc in accounts)
            return sorted(list(categories))
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return ["Default", "Working", "Testing", "Backup", "VIP"]
    # --- END MODIFIED ---
    def populate_table(self):
        """Populate the table with accounts"""
        self.table.setRowCount(0)
        category_filter = self.category_combo.currentText()
        search_text = self.search_input.text().lower()
        # --- MODIFIED: Fetch accounts from DB ---
        accounts = self.db_manager.get_all_accounts()
        # --- END MODIFIED ---
        # Filter by category
        if category_filter != "All Categories":
            accounts = [acc for acc in accounts if acc['category'] == category_filter]
        # Filter by search text
        if search_text:
            accounts = [acc for acc in accounts if search_text in acc['uid'].lower()]
        self.table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left: 15px;")
            self.table.setCellWidget(row, 0, checkbox)
            # UID
            uid_item = QTableWidgetItem(account['uid'])
            self.table.setItem(row, 1, uid_item)
            # Category
            category_item = QTableWidgetItem(account['category'])
            self.table.setItem(row, 2, category_item)
            # Status
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.table.setItem(row, 3, status_item)
            # Last Login
            last_login_item = QTableWidgetItem(account['last_login'] or "Never")
            self.table.setItem(row, 4, last_login_item)
            # Login Count
            login_count_item = QTableWidgetItem(str(account['login_count']))
            self.table.setItem(row, 5, login_count_item)
            # Task Count (NEW)
            task_count_item = QTableWidgetItem(str(account['task_count']))
            self.table.setItem(row, 6, task_count_item)
            # Store account data in the row
            for col in range(1, 7):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, account)
    def filter_accounts(self):
        """Filter accounts based on category and search text"""
        self.populate_table()
    def select_all_accounts(self):
        """Select all accounts in the table"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    def clear_all_selections(self):
        """Clear all selections in the table"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    def show_context_menu(self, pos):
        """Show context menu for right-click on table"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        uid_item = self.table.item(row, 1)
        if not uid_item:
            return
        uid = uid_item.text()
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4A90E2;
            }
        """)
        # Login submenu
        login_menu = QMenu("Login", self)
        login_menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4A90E2;
            }
        """)
        login_pass_action = login_menu.addAction("Login with UID/Password")
        login_token_action = login_menu.addAction("Login with Token/Cookie")
        menu.addMenu(login_menu)
        # Connect actions
        login_pass_action.triggered.connect(lambda: self.login_account(uid, "password"))
        login_token_action.triggered.connect(lambda: self.login_account(uid, "token"))
        menu.exec(self.table.mapToGlobal(pos))
    def login_account(self, uid, method):
        """Login to the selected account"""
        # --- MODIFIED: Get account from DB ---
        account = self.db_manager.get_account_by_uid(uid)
        # --- END MODIFIED ---
        if not account:
            return
        if method == "password" and (not account['uid'] or not account['password']):
            QMessageBox.warning(self, "Missing Info", "UID and Password are required for this method.")
            return
        elif method == "token" and (not account['token'] and not account['cookie']):
            QMessageBox.warning(self, "Missing Info", "Token or Cookie is required for this method.")
            return
        # Create a temporary login thread for this single account
        accounts = [(account['uid'], account['password'], account['token'], account['cookie'])]
        # Create and start login thread
        login_manager = ParallelLoginManager(accounts, False, None, None, None, None, None, self.db_manager, config_manager=self.config_manager)
        def on_login_finished():
            self.populate_table()  # Refresh table to show updated status
        login_manager.finished.connect(on_login_finished)
        login_manager.log_message.connect(lambda msg: print(f"Login: {msg}"))
        login_manager.start()
        QMessageBox.information(self, "Login Started", f"Login process started for UID: {uid}")
    def accept(self):
        """Override accept to collect selected accounts."""
        self.selected_accounts = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                uid_item = self.table.item(row, 1)
                if uid_item:
                    uid = uid_item.text()
                    # --- MODIFIED: Get full account data from DB ---
                    account = self.db_manager.get_account_by_uid(uid)
                    if account:
                        self.selected_accounts.append(account)
                    # --- END MODIFIED ---
        super().accept()
    def get_selected_accounts(self):
        """Return the list of selected accounts."""
        return self.selected_accounts

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Facebook Farm Tool")
        icon_path = os.path.join("logo", "logo.png")  # Path relative to the script
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Logo file not found at {icon_path}")
        # --- CRITICAL FIX: Initialize ConfigManager with error handling ---
        try:
            self.config_manager = ConfigManager()
            print("ConfigManager initialized successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize ConfigManager: {e}")
            # Create a default config_manager to prevent total crash
            class DummyConfigManager:
                def get(self, key, default=None):
                    return default
                def set(self, key, value):
                    pass
            self.config_manager = DummyConfigManager()
            print("Using DummyConfigManager to continue.")
        self.resize(1300, 850)
        self.center_window()
        self.login_manager = None  # Changed from login_thread to login_manager
        # --- MODIFIED: Initialize Database Manager ---
        self.db_manager = AccountDBManager()
        print("AccountDBManager initialized successfully.")
        # --- END MODIFIED ---
        # Apply global dark theme stylesheet
        self.apply_dark_theme()
               # Create tabs
        self.tabs = QTabWidget()

        # --- FIX: Initialize category_filter_combo early to avoid AttributeError ---
        self.category_filter_combo = QComboBox()  # Temporary placeholder
        # --- END FIX ---
        self.create_dashboard_tab()
        self.create_manager_tab()
        self.create_import_custom_tab()
        # --- NEW TABS ---
        self.create_account_info_tab()  # New Tab 1
        self.create_schedule_tab()      # New Tab 2
        self.create_automation_actions_tab()  # New Automation Actions Tab
        # --- Settings Tab Moved to the End ---
        self.create_settings_tab()      # Now positioned last
        # Set central widget
        container = QWidget()
        container.setStyleSheet("background-color: #1A1A1A;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        # Add system monitor
        self.system_monitor = SystemMonitorWidget()
        main_layout.addWidget(self.system_monitor)
        # Add tabs
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(container)
        # Update system monitor with account count
        self.update_system_monitor()
        # Connect signals
        self.connect_signals()
        # --- ADDED: Load settings from config ---
        try:
            self.load_settings_from_config()
            print("Settings loaded from config successfully.")
        except Exception as e:
            print(f"Error loading settings from config: {e}")
        # --- END ADDED ---
    def apply_dark_theme(self):
        """Apply a global dark theme to the application."""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(26, 26, 26))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(37, 37, 37))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(30, 30, 30))
        self.setPalette(dark_palette)
        # Apply stylesheet for consistent styling
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1A1A1A;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #E0E0E0;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 8px 15px;
                margin: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #3A3A3A;
            }
            /* Style for the custom title bar (if implemented later) */
            #CustomTitleBar {
                background-color: #2D2D2D;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 5px;
            }
            #CustomTitleBar QLabel {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 14px;
            }
            #CustomTitleBar QPushButton {
                background-color: transparent;
                border: none;
                color: #E0E0E0;
                font-size: 16px;
                width: 30px;
                height: 30px;
            }
            #CustomTitleBar QPushButton:hover {
                background-color: #4A90E2;
                border-radius: 4px;
            }
        """)
    def get_groupbox_style(self):
        """Return stylesheet for QGroupBox."""
        return """
            QGroupBox {
                background-color: #252525;
                border: 2px solid #404040;
                border-radius: 10px;
                margin-top: 1ex;
                padding: 15px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #FFFFFF;
            }
        """
    def get_textedit_style(self):
        """Return stylesheet for QTextEdit."""
        return """
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 8px;
                selection-background-color: #4A90E2;
                selection-color: #FFFFFF;
            }
        """
    def get_lineedit_style(self):
        """Return stylesheet for QLineEdit."""
        return """
            QLineEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 6px;
                selection-background-color: #4A90E2;
            }
        """
    def get_checkbox_style(self):
        """Return stylesheet for QCheckBox."""
        return """
            QCheckBox {
                color: #E0E0E0;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #2D2D2D;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #4A90E2;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #5DBF60;
                border: 2px solid #5DBF60;
            }
        """
    def get_button_style(self, normal_color, hover_color):
        """Return stylesheet for QPushButton with specified colors."""
        return f"""
            QPushButton {{
                background-color: {normal_color};
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: #333333;
            }}
            QPushButton:disabled {{
                background-color: #3A3A3A;
                color: #777777;
            }}
        """
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(screen.center())
        self.move(frame.topLeft())
    def connect_signals(self):
        """Connect all signals and slots"""
        # Dashboard tab signals
        self.category_combo.currentIndexChanged.connect(self.update_dashboard_stats)
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        # Manager tab signals
        self.select_account_btn.clicked.connect(self.open_account_selection_dialog)
        self.auto_login_btn.clicked.connect(self.start_auto_login_selected)
        self.interact_btn.clicked.connect(self.start_interaction_selected)
        self.stop_btn.clicked.connect(self.stop_login_process)
        self.react_checkbox.stateChanged.connect(self.toggle_react_checkboxes)
        # Import Custom tab signals
        self.start_btn.clicked.connect(self.parse_textarea)
        self.add_account_btn.clicked.connect(self.show_add_account_dialog)
        self.add_category_btn.clicked.connect(self.show_add_category_dialog)
        self.delete_category_btn.clicked.connect(self.delete_selected_category)
        self.category_filter_combo.currentIndexChanged.connect(self.filter_accounts_by_category)
        self.refresh_accounts_btn.clicked.connect(self.load_accounts_to_table)
        # Connect right-click context menus for all tables
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(lambda pos: self.open_context_menu(pos, self.table))
        self.selection_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.selection_table.customContextMenuRequested.connect(lambda pos: self.open_context_menu(pos, self.selection_table))
        # --- NEW: Account Info Tab Signals ---
        self.profile_browse_btn.clicked.connect(lambda: self.browse_file(self.profile_path_input))
        self.cover_browse_btn.clicked.connect(lambda: self.browse_file(self.cover_path_input))
        self.start_profile_upload_btn.clicked.connect(self.start_profile_upload)
        self.info_select_account_btn.clicked.connect(self.open_account_info_selection_dialog)
        # --- NEW: Schedule Tab Signals ---
        self.schedule_select_account_btn.clicked.connect(self.open_schedule_account_selection_dialog)
        self.start_schedule_btn.clicked.connect(self.start_scheduled_actions)
        self.stop_schedule_btn.clicked.connect(self.stop_scheduled_actions)
        # --- NEW: Automation Actions Tab Signals ---
        self.automation_select_account_btn.clicked.connect(self.open_automation_account_selection_dialog)
        self.start_automation_btn.clicked.connect(self.start_automation_actions)
        self.stop_automation_btn.clicked.connect(self.stop_automation_actions)
        # --- ADDED: Settings Tab Signals ---
        self.save_settings_btn.clicked.connect(self.save_settings_to_config)
        # --- END ADDED ---
        # --- MODIFIED: Connect DB Manager signals ---
        # Connect account status update signal
        if hasattr(self, 'login_manager') and self.login_manager:
            self.login_manager.account_status_update.connect(self.on_account_status_update)
        # --- END MODIFIED ---
    def browse_file(self, line_edit):
        """Open file dialog and set the selected file path to the given QLineEdit."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)
    def create_dashboard_tab(self):
        """Create the dashboard tab with statistics and charts"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout()
        # Title
        title_label = QLabel("Dashboard Overview")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4A90E2; margin: 10px 0;")
        layout.addWidget(title_label)
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_combo = QComboBox()
        # --- MODIFIED: Populate categories from DB ---
        self.update_category_combo()
        # --- END MODIFIED ---
        filter_layout.addWidget(self.category_combo)
        self.refresh_btn = QPushButton("Refresh Stats")
        self.refresh_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Stats cards
        stats_layout = QHBoxLayout()
        # Total Accounts Card
        total_card = self.create_stat_card("Total Accounts", "0", "#4A90E2")
        stats_layout.addWidget(total_card)
        # Working Accounts Card
        working_card = self.create_stat_card("Working Accounts", "0", "#4CAF50")
        stats_layout.addWidget(working_card)
        # Failed Accounts Card
        failed_card = self.create_stat_card("Failed Accounts", "0", "#E74C3C")
        stats_layout.addWidget(failed_card)
        # --- NEW: Error Accounts Card ---
        error_card = self.create_stat_card("Error/Banned Accounts", "0", "#9932CC")  # Purple for errors
        stats_layout.addWidget(error_card)
        # --- FIXED: Added Unknown Accounts Card ---
        unknown_card = self.create_stat_card("Unknown Accounts", "0", "#F39C12")
        stats_layout.addWidget(unknown_card)
        layout.addLayout(stats_layout)
        # Additional stats
        additional_stats_layout = QHBoxLayout()
        # Average Login Count
        avg_login_card = self.create_stat_card("Avg. Login Count", "0.0", "#9B59B6")
        additional_stats_layout.addWidget(avg_login_card)
        # Recently Added
        recent_card = self.create_stat_card("Added Today", "0", "#3498DB")
        additional_stats_layout.addWidget(recent_card)
        # Most Used Category
        category_card = self.create_stat_card("Most Used Category", "Default", "#E67E22")
        additional_stats_layout.addWidget(category_card)
        layout.addLayout(additional_stats_layout)
        # Detailed stats table
        layout.addWidget(QLabel("Account Status Breakdown:"))
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)  # Updated to 6 columns
        self.stats_table.setHorizontalHeaderLabels(["Category", "Total", "Working", "Failed", "Error", "Unknown"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stats_table)
        dashboard_widget.setLayout(layout)
        self.tabs.addTab(dashboard_widget, "Dashboard")
        # Store references to cards for updating
        self.total_accounts_card = total_card.findChild(QLabel, "value")
        self.working_accounts_card = working_card.findChild(QLabel, "value")
        self.failed_accounts_card = failed_card.findChild(QLabel, "value")
        self.error_accounts_card = error_card.findChild(QLabel, "value")  # Reference to new card
        self.unknown_accounts_card = unknown_card.findChild(QLabel, "value") # FIXED: Added this line
        self.avg_login_card = avg_login_card.findChild(QLabel, "value")
        self.recent_card = recent_card.findChild(QLabel, "value")
        self.category_card = category_card.findChild(QLabel, "value")
        # Initial update
        self.update_dashboard_stats()
    def create_stat_card(self, title, value, color):
        """Create a styled statistics card"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D2D;
                border-radius: 10px;
                border: 1px solid #404040;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #AAAAAA; font-size: 14px; font-weight: bold;")
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()
        return card
    def update_dashboard_stats(self):
        """Update dashboard statistics"""
        category_filter = self.category_combo.currentText()
        # --- MODIFIED: Fetch accounts from DB ---
        if category_filter == "All Categories":
            accounts = self.db_manager.get_all_accounts()
        else:
            accounts = [acc for acc in self.db_manager.get_all_accounts() if acc['category'] == category_filter]
        # --- END MODIFIED ---
        total = len(accounts)
        working = len([acc for acc in accounts if acc['status'] == 'Working'])
        failed = len([acc for acc in accounts if acc['status'] == 'Failed'])
        # --- NEW: Count 'Error' status separately ---
        error = len([acc for acc in accounts if acc['status'] == 'Error'])
        unknown = len([acc for acc in accounts if acc['status'] == 'Unknown'])
        # Update cards
        self.total_accounts_card.setText(str(total))
        self.working_accounts_card.setText(str(working))
        self.failed_accounts_card.setText(str(failed))
        self.error_accounts_card.setText(str(error))  # Update new card
        self.unknown_accounts_card.setText(str(unknown)) # Assuming this is defined elsewhere, if not, add it
        # Update average login count
        if total > 0:
            avg_login = sum(acc['login_count'] for acc in accounts) / total
            self.avg_login_card.setText(f"{avg_login:.1f}")
        else:
            self.avg_login_card.setText("0.0")
        # Update recently added
        today = QDate.currentDate().toString("yyyy-MM-dd")
        added_today = len([acc for acc in accounts if acc.get('created_date', '') == today])
        self.recent_card.setText(str(added_today))
        # Update most used category
        if category_filter == "All Categories":
            category_counts = {}
            # --- MODIFIED: Get accounts from DB ---
            for acc in self.db_manager.get_all_accounts():
                cat = acc['category']
                category_counts[cat] = category_counts.get(cat, 0) + 1
            # --- END MODIFIED ---
            if category_counts:
                most_used = max(category_counts, key=category_counts.get)
                self.category_card.setText(most_used)
            else:
                self.category_card.setText("None")
        else:
            self.category_card.setText(category_filter)
        # Update stats table
        self.update_stats_table()
    def update_stats_table(self):
        """Update the statistics table"""
        category_filter = self.category_combo.currentText()
        # --- MODIFIED: Get categories from DB ---
        if category_filter == "All Categories":
            categories = self.get_categories()
        else:
            categories = [category_filter]
        # --- END MODIFIED ---
        self.stats_table.setRowCount(len(categories))
        for i, category in enumerate(categories):
            # --- MODIFIED: Get accounts from DB ---
            accounts = [acc for acc in self.db_manager.get_all_accounts() if acc['category'] == category]
            # --- END MODIFIED ---
            total = len(accounts)
            working = len([acc for acc in accounts if acc['status'] == 'Working'])
            failed = len([acc for acc in accounts if acc['status'] == 'Failed'])
            # --- NEW: Count 'Error' status ---
            error = len([acc for acc in accounts if acc['status'] == 'Error'])
            unknown = len([acc for acc in accounts if acc['status'] == 'Unknown'])
            self.stats_table.setItem(i, 0, QTableWidgetItem(category))
            self.stats_table.setItem(i, 1, QTableWidgetItem(str(total)))
            self.stats_table.setItem(i, 2, QTableWidgetItem(str(working)))
            self.stats_table.setItem(i, 3, QTableWidgetItem(str(failed)))
            self.stats_table.setItem(i, 4, QTableWidgetItem(str(error)))  # New column
            self.stats_table.setItem(i, 5, QTableWidgetItem(str(unknown)))
        # Color code the status cells
        for row in range(self.stats_table.rowCount()):
            for col in range(2, 6):  # Updated to include Error column
                item = self.stats_table.item(row, col)
                if item:
                    value = int(item.text())
                    if value > 0:
                        if col == 2:  # Working
                            item.setForeground(QColor("#4CAF50"))
                        elif col == 3:  # Failed
                            item.setForeground(QColor("#E74C3C"))
                        elif col == 4:  # Error (New)
                            item.setForeground(QColor("#9932CC"))
                        else:  # Unknown
                            item.setForeground(QColor("#F39C12"))
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        self.update_dashboard_stats()
        self.log_message("Dashboard refreshed")
    def create_manager_tab(self):
        """Create the account manager tab for selecting accounts to use"""
        manager_widget = QWidget()
        main_layout = QHBoxLayout()
        # Left side - Select Accounts to Use
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        # Top section with account selection table
        top_group = QGroupBox("Select Accounts to Use")
        top_group.setStyleSheet(self.get_groupbox_style())
        top_layout = QVBoxLayout()
        # Selection buttons
        select_button_layout = QHBoxLayout()
        self.select_account_btn = QPushButton("Select Account")
        self.select_account_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        select_button_layout.addWidget(self.select_account_btn)
        select_button_layout.addStretch()
        top_layout.addLayout(select_button_layout)
        # New Table for selecting accounts (starts empty)
        self.selection_table = QTableWidget()
        self.selection_table.setColumnCount(10)  # Updated to 10 columns (added task_count)
        self.selection_table.setHorizontalHeaderLabels(["Select", "UID", "Password", "Token", "Cookie", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.selection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.selection_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.selection_table.setSortingEnabled(True)
        # Set column widths
        self.selection_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.selection_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.selection_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        self.selection_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QCheckBox {
                margin-left: 15px; /* Center checkbox in cell */
            }
        """)
        # --- TABLE STARTS EMPTY ---
        self.selection_table.setRowCount(0)
        top_layout.addWidget(self.selection_table)
        top_group.setLayout(top_layout)
        left_layout.addWidget(top_group)
        # Buttons (moved to bottom of left side)
        button_layout = QHBoxLayout()
        self.auto_login_btn = QPushButton("Start Auto Login Selected Accounts (Stealth)")
        self.auto_login_btn.setEnabled(False)
        self.auto_login_btn.setStyleSheet(self.get_button_style("#50C878", "#60D888"))
        self.interact_btn = QPushButton("Login & Interact with Post (Selected)")
        self.interact_btn.setEnabled(False)
        self.interact_btn.setStyleSheet(self.get_button_style("#4CAF50", "#5DBF60"))
        self.stop_btn = QPushButton("Stop Process")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(self.get_button_style("#E74C3C", "#F75C4C"))
        button_layout.addWidget(self.auto_login_btn)
        button_layout.addWidget(self.interact_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        # Status area
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #E0E0E0; font-weight: bold; padding: 5px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                color: #FFFFFF;
                background-color: #2D2D2D;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        left_layout.addLayout(status_layout)
        # Log output
        log_label = QLabel("Log Output:")
        log_label.setStyleSheet("color: #E0E0E0; font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(log_label)
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(150)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(self.get_textedit_style())
        left_layout.addWidget(self.log_output)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)
        # Right side - Post Interaction
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        post_group = QGroupBox("Post Interaction")
        post_group.setStyleSheet(self.get_groupbox_style())
        post_layout = QVBoxLayout()
        # Post URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Post URL:")
        url_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        url_layout.addWidget(url_label)
        self.post_url_input = QLineEdit()
        self.post_url_input.setPlaceholderText("https://www.facebook.com/permalink.php?story_fbid=...")
        self.post_url_input.setStyleSheet(self.get_lineedit_style())
        url_layout.addWidget(self.post_url_input)
        post_layout.addLayout(url_layout)
        # Actions selection
        actions_layout = QHBoxLayout()
        actions_label = QLabel("Actions:")
        actions_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        actions_layout.addWidget(actions_label)
        self.like_checkbox = QCheckBox("Like Post")
        self.like_checkbox.setChecked(True)
        self.like_checkbox.setStyleSheet(self.get_checkbox_style())
        self.comment_checkbox = QCheckBox("Comment")
        self.comment_checkbox.setChecked(True)
        self.comment_checkbox.setStyleSheet(self.get_checkbox_style())
        self.react_checkbox = QCheckBox("React")
        self.react_checkbox.setChecked(True)
        self.react_checkbox.setStyleSheet(self.get_checkbox_style())
        self.share_checkbox = QCheckBox("Share Post")  # Added Share checkbox
        self.share_checkbox.setChecked(False)
        self.share_checkbox.setStyleSheet(self.get_checkbox_style())
        actions_layout.addWidget(self.like_checkbox)
        actions_layout.addWidget(self.comment_checkbox)
        actions_layout.addWidget(self.react_checkbox)
        actions_layout.addWidget(self.share_checkbox)  # Added to layout
        actions_layout.addStretch()
        post_layout.addLayout(actions_layout)
        # Reaction type selection
        react_layout = QHBoxLayout()
        react_label = QLabel("Reaction Type:")
        react_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        react_layout.addWidget(react_label)
        self.react_like = QCheckBox("👍 Like")
        self.react_love = QCheckBox("❤️ Love")
        self.react_care = QCheckBox("🤗 Care")
        self.react_haha = QCheckBox("😂 Haha")
        self.react_wow = QCheckBox("😮 Wow")
        self.react_sad = QCheckBox("😢 Sad")
        self.react_angry = QCheckBox("😠 Angry")
        font = QFont("Segoe UI Emoji", 9)
        for checkbox in [self.react_like, self.react_love, self.react_care, self.react_haha, self.react_wow, self.react_sad, self.react_angry]:
            checkbox.setFont(font)
            checkbox.setStyleSheet(self.get_checkbox_style())
            checkbox.setChecked(False)
        self.react_like.setChecked(True)
        react_layout.addWidget(self.react_like)
        react_layout.addWidget(self.react_love)
        react_layout.addWidget(self.react_care)
        react_layout.addWidget(self.react_haha)
        react_layout.addWidget(self.react_wow)
        react_layout.addWidget(self.react_sad)
        react_layout.addWidget(self.react_angry)
        react_layout.addStretch()
        post_layout.addLayout(react_layout)
        # Comment input with clipboard button
        comment_layout = QHBoxLayout()
        comment_label = QLabel("Comment Text:")
        comment_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        comment_layout.addWidget(comment_label)
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(60)
        self.comment_input.setPlaceholderText("Enter comment text here... (Supports Emojis 🎉)")
        self.comment_input.setStyleSheet(self.get_textedit_style())
        comment_layout.addWidget(self.comment_input)
        post_layout.addLayout(comment_layout)
        # Random comments option
        random_comments_layout = QHBoxLayout()
        self.random_comments_checkbox = QCheckBox("Use Random Comments")
        self.random_comments_checkbox.setChecked(False)
        self.random_comments_checkbox.setStyleSheet(self.get_checkbox_style())
        self.random_comments_checkbox.stateChanged.connect(self.toggle_random_comments)
        random_comments_layout.addWidget(self.random_comments_checkbox)
        random_comments_layout.addStretch()
        post_layout.addLayout(random_comments_layout)
        # Random comments input (initially hidden)
        self.random_comments_group = QGroupBox("Random Comments (One per line)")
        self.random_comments_group.setStyleSheet(self.get_groupbox_style())
        self.random_comments_group.setVisible(False)
        random_comments_inner_layout = QVBoxLayout()
        self.random_comments_input = QTextEdit()
        self.random_comments_input.setMaximumHeight(100)
        self.random_comments_input.setPlaceholderText("Enter multiple comments, one per line Each account will use a different comment (Supports Emojis 🎉)")
        self.random_comments_input.setStyleSheet(self.get_textedit_style())
        random_comments_inner_layout.addWidget(self.random_comments_input)
        self.random_comments_group.setLayout(random_comments_inner_layout)
        post_layout.addWidget(self.random_comments_group)
        # Clipboard button
        clipboard_layout = QHBoxLayout()
        self.clipboard_btn = QPushButton("Paste from Clipboard")
        self.clipboard_btn.clicked.connect(self.paste_from_clipboard)
        self.clipboard_btn.setStyleSheet(self.get_button_style("#5D5D5D", "#7A7A7A"))
        clipboard_layout.addWidget(self.clipboard_btn)
        post_layout.addLayout(clipboard_layout)
        post_group.setLayout(post_layout)
        post_group.setMaximumHeight(450)
        right_layout.addWidget(post_group)
        # Add stretch to push content to top
        right_layout.addStretch(1)
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)
        manager_widget.setLayout(main_layout)
        self.tabs.addTab(manager_widget, "Account Manager")
    def create_import_custom_tab(self):
        """Create the Import Custom tab for account import and management"""
        import_widget = QWidget()
        main_layout = QHBoxLayout()  # Changed to QHBoxLayout for left-right layout
        # Left side - Loaded Accounts Table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        # Loaded Accounts Table
        left_layout.addWidget(QLabel("Loaded Accounts:"))
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # Updated to 9 columns (added task_count)
        self.table.setHorizontalHeaderLabels(["UID", "Password", "Token", "Cookie", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
        """)
        left_layout.addWidget(self.table)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 2)  # Give more space to the table
        # Right side - Account Input and Category Management
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        # Category management
        category_group = QGroupBox("Category Management")
        category_group.setStyleSheet(self.get_groupbox_style())
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categories:"))
        # Re-initialize the combo box properly in its tab
        self.category_filter_combo = QComboBox()
        self.update_category_combo()  # Populate it with real categories
        # --- MODIFIED: Populate categories from DB ---
        self.update_category_combo()
        # --- END MODIFIED ---
        category_layout.addWidget(self.category_filter_combo)
        self.add_category_btn = QPushButton("Add Category")
        self.add_category_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        category_layout.addWidget(self.add_category_btn)
        self.delete_category_btn = QPushButton("Delete Category")
        self.delete_category_btn.setStyleSheet(self.get_button_style("#E74C3C", "#F75C4C"))
        category_layout.addWidget(self.delete_category_btn)
        category_layout.addStretch()
        category_group.setLayout(category_layout)
        right_layout.addWidget(category_group)
        # Account input area
        account_group = QGroupBox("Import Accounts")
        account_group.setStyleSheet(self.get_groupbox_style())
        account_layout = QVBoxLayout()
        self.textarea = QTextEdit()
        self.textarea.setPlaceholderText(
            "Paste accounts here, one per line: "
            "uid | password | token | cookie "
            "Example: "
            "61578965587472 | mypassword | EAAAAUazZA8jI... | c_user=6157896...; xs=SwpEsatZTEmHAbAz:1754347505-1:-1; fr=1hGiq02BRNpye4900.AW4Cq7wfR1iGZUzsjKOESeaFf06f25J8aAVW4ho567-qIgzosg.BokTik..AAA.0.0.BokTik.AWdX"
        )
        self.textarea.setStyleSheet(self.get_textedit_style())
        account_layout.addWidget(self.textarea)
        account_group.setLayout(account_layout)
        right_layout.addWidget(account_group)
        # Add account and import buttons
        button_layout = QHBoxLayout()
        self.add_account_btn = QPushButton("Add Single Account")
        self.add_account_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        button_layout.addWidget(self.add_account_btn)
        self.start_btn = QPushButton("Import Accounts ➤ Parse to Table")
        self.start_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        button_layout.addWidget(self.start_btn)
        self.refresh_accounts_btn = QPushButton("Refresh Accounts")
        self.refresh_accounts_btn.setStyleSheet(self.get_button_style("#3498DB", "#44A8E2"))
        button_layout.addWidget(self.refresh_accounts_btn)
        button_layout.addStretch()
        right_layout.addLayout(button_layout)
        # Add stretch to push content to top
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)  # Give less space to the right side
        import_widget.setLayout(main_layout)
        self.tabs.addTab(import_widget, "Import Custom")
    # --- NEW: Account Information Tab ---
    def create_account_info_tab(self):
        """Create the Account Information tab."""
        info_widget = QWidget()
        main_layout = QHBoxLayout()  # Main layout is horizontal
        # Left side - Account Selection
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        # Account selection section
        account_group = QGroupBox("Select Accounts to Use")
        account_group.setStyleSheet(self.get_groupbox_style())
        account_layout = QVBoxLayout()
        # Selection button
        self.info_select_account_btn = QPushButton("Select Account")
        self.info_select_account_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        account_layout.addWidget(self.info_select_account_btn)
        # Selected accounts table
        self.info_selection_table = QTableWidget()
        self.info_selection_table.setColumnCount(7)  # Updated to 7 columns (added task_count)
        self.info_selection_table.setHorizontalHeaderLabels(["Select", "UID", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.info_selection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.info_selection_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.info_selection_table.setSortingEnabled(True)
        # Set column widths
        self.info_selection_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.info_selection_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QCheckBox {
                margin-left: 15px; /* Center checkbox in cell */
            }
        """)
        # Start with empty table
        self.info_selection_table.setRowCount(0)
        account_layout.addWidget(self.info_selection_table)
        # Add Select All and Deselect All buttons
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.select_all_in_table(self.info_selection_table))
        select_buttons_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self.deselect_all_in_table(self.info_selection_table))
        select_buttons_layout.addWidget(deselect_all_btn)
        select_buttons_layout.addStretch()
        account_layout.addLayout(select_buttons_layout)
        # Add counter label
        self.info_selection_counter = QLabel("Selected: 0")
        self.info_selection_counter.setStyleSheet("color: #E0E0E0; font-weight: bold; padding: 5px;")
        account_layout.addWidget(self.info_selection_counter)
        account_group.setLayout(account_layout)
        left_layout.addWidget(account_group)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)  # 1 part width
        # Right side - Profile Management
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        # Title
        title_label = QLabel("Account Information & Profile Management")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4A90E2; margin: 10px 0;")
        right_layout.addWidget(title_label)
        # Profile Picture Section
        profile_group = QGroupBox("Profile Picture")
        profile_group.setStyleSheet(self.get_groupbox_style())
        profile_layout = QHBoxLayout()
        self.profile_path_input = QLineEdit()
        self.profile_path_input.setPlaceholderText("Path to profile picture...")
        self.profile_path_input.setStyleSheet(self.get_lineedit_style())
        profile_layout.addWidget(self.profile_path_input)
        self.profile_browse_btn = QPushButton("Browse...")
        self.profile_browse_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        profile_layout.addWidget(self.profile_browse_btn)
        profile_group.setLayout(profile_layout)
        right_layout.addWidget(profile_group)
        # Cover Photo Section
        cover_group = QGroupBox("Cover Photo")
        cover_group.setStyleSheet(self.get_groupbox_style())
        cover_layout = QHBoxLayout()
        self.cover_path_input = QLineEdit()
        self.cover_path_input.setPlaceholderText("Path to cover photo...")
        self.cover_path_input.setStyleSheet(self.get_lineedit_style())
        cover_layout.addWidget(self.cover_path_input)
        self.cover_browse_btn = QPushButton("Browse...")
        self.cover_browse_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        cover_layout.addWidget(self.cover_browse_btn)
        cover_group.setLayout(cover_layout)
        right_layout.addWidget(cover_group)
        # Start Process Button
        self.start_profile_upload_btn = QPushButton("Start Upload Process")
        self.start_profile_upload_btn.setStyleSheet(self.get_button_style("#4CAF50", "#5DBF60"))
        right_layout.addWidget(self.start_profile_upload_btn)
        # Log output for this tab
        log_label = QLabel("Upload Log:")
        log_label.setStyleSheet("color: #E0E0E0; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(log_label)
        self.profile_log_output = QTextEdit()
        self.profile_log_output.setMaximumHeight(150)
        self.profile_log_output.setReadOnly(True)
        self.profile_log_output.setStyleSheet(self.get_textedit_style())
        right_layout.addWidget(self.profile_log_output)
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)  # 1 part width
        info_widget.setLayout(main_layout)
        self.tabs.addTab(info_widget, "Account Info")
    # --- ENHANCED: Profile Upload Implementation ---
    def start_profile_upload(self):
        """Start the profile upload process for selected accounts."""
        selected_accounts = self.get_selected_accounts(self.info_selection_table)
        if not selected_accounts:
            QMessageBox.warning(self, "No Accounts Selected", "Please select at least one account to upload profiles.")
            return
        profile_path = self.profile_path_input.text().strip()
        cover_path = self.cover_path_input.text().strip()
        if not profile_path and not cover_path:
            QMessageBox.warning(self, "No Files", "Please select at least a profile picture or cover photo.")
            return
        self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Starting upload process for {len(selected_accounts)} accounts...")
        if profile_path:
            self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Profile Picture: {profile_path}")
        if cover_path:
            self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Cover Photo: {cover_path}")
        for i, account in enumerate(selected_accounts):
            if not hasattr(self, 'login_manager') or not self.login_manager or not self.login_manager.running:
                break
            self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Processing account {i+1}/{len(selected_accounts)}: UID {account['uid']}")
            # Perform the upload
            success = self.simulate_login_and_upload(account, profile_path, cover_path)
            if success:
                self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] ✓ Upload successful for UID: {account['uid']}")
                # --- ADDED: Increment task count ---
                self.db_manager.update_account_status(account['uid'], "Working", False, True)
                # --- END ADDED ---
            else:
                self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] ✗ Upload failed for UID: {account['uid']}")
                # --- MODIFIED: Update status in DB ---
                self.db_manager.update_account_status(account['uid'], "Error", False, False)
                # --- END MODIFIED ---
            # Random delay
            time.sleep(random.uniform(3, 7))
        self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Upload process completed.")
    def simulate_login_and_upload(self, account, profile_path, cover_path):
        """Simulate the login and upload process. Returns success boolean."""
        # --- REAL IMPLEMENTATION STARTS HERE ---
        # This is a simplified example. A real implementation would be much more complex.
        driver = None
        try:
            # Determine login method
            if account['token'] and account['cookie']:
                success, driver = self.login_with_token_cookie_for_upload(account['uid'], account['token'], account['cookie'])
            elif account['uid'] and account['password']:
                success, driver = self.login_with_uid_pass_for_upload(account['uid'], account['password'])
            else:
                self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] No valid login info for UID: {account['uid']}")
                return False
            if not success:
                return False
            # Navigate to profile
            driver.get(f"https://www.facebook.com/profile.php")
            self.human_delay_for_upload(3, 5)
            # Upload Profile Picture
            if profile_path:
                if self.upload_profile_picture(driver, profile_path):
                    self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Profile picture uploaded.")
                else:
                    self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Failed to upload profile picture.")
            # Upload Cover Photo
            if cover_path:
                if self.upload_cover_photo(driver, cover_path):
                    self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Cover photo uploaded.")
                else:
                    self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Failed to upload cover photo.")
            # Close driver
            driver.quit()
            return True
        except Exception as e:
            self.profile_log_output.append(f"[{time.strftime('%H:%M:%S')}] Error during upload: {str(e)}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return False
    def login_with_uid_pass_for_upload(self, uid, pw):
        """Simplified login for upload."""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        if self.config_manager.get("headless", False):
            options.add_argument("--headless")
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            driver.get("https://www.facebook.com/login")
            self.human_delay_for_upload(2, 4)
            email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(uid)
            password_field = driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(pw)
            login_button = driver.find_element(By.NAME, "login")
            login_button.click()
            self.human_delay_for_upload(5, 8)
            # Simple check for successful login
            if "facebook.com" in driver.current_url and "login" not in driver.current_url:
                return True, driver
            else:
                return False, driver
        except Exception:
            if driver:
                driver.quit()
            return False, None
    def login_with_token_cookie_for_upload(self, uid, token, cookie_str):
        """Simplified token/cookie login for upload."""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        if self.config_manager.get("headless", False):
            options.add_argument("--headless")
        driver = None
        try:
            driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
            driver.get("https://www.facebook.com")
            cookies = self.parse_cookies_for_upload(cookie_str)
            for cookie in cookies:
                driver.add_cookie(cookie)
            if token:
                driver.add_cookie({'name': 'token', 'value': token, 'domain': '.facebook.com'})
            driver.refresh()
            self.human_delay_for_upload(3, 5)
            if "facebook.com" in driver.current_url:
                return True, driver
            else:
                return False, driver
        except Exception:
            if driver:
                driver.quit()
            return False, None
    def parse_cookies_for_upload(self, cookie_str):
        """Simple cookie parser for upload."""
        cookies = []
        if not cookie_str:
            return cookies
        for item in cookie_str.split(';'):
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
        return cookies
    def upload_profile_picture(self, driver, file_path):
        """Attempt to upload a profile picture."""
        try:
            # Click on the profile picture element to open the uploader
            # This selector is very likely to break
            profile_pic_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//img[@alt='Your profile picture'] | //div[@aria-label='Update your profile picture']"))
            )
            profile_pic_element.click()
            self.human_delay_for_upload(2, 3)
            # Find the file input element (usually hidden)
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys(file_path)
            self.human_delay_for_upload(3, 5)
            # Click the "Save" button
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Save' or @aria-label='Lưu']"))
            )
            save_button.click()
            self.human_delay_for_upload(3, 5)
            return True
        except Exception as e:
            print(f"Error uploading profile pic: {e}")
            return False
    def upload_cover_photo(self, driver, file_path):
        """Attempt to upload a cover photo."""
        try:
            # Click on the cover photo area
            cover_photo_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Update your cover photo'] | //img[@alt='Cover Photo']"))
            )
            cover_photo_element.click()
            self.human_delay_for_upload(2, 3)
            # Find the file input
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys(file_path)
            self.human_delay_for_upload(3, 5)
            # Click "Save"
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Save' or @aria-label='Lưu']"))
            )
            save_button.click()
            self.human_delay_for_upload(3, 5)
            return True
        except Exception as e:
            print(f"Error uploading cover photo: {e}")
            return False
    def human_delay_for_upload(self, min_sec=1, max_sec=3):
        """Delay for upload simulation."""
        time.sleep(random.uniform(min_sec, max_sec))
    # --- END ENHANCED ---
    # --- NEW: Schedule Tab with Select Account ---
    def create_schedule_tab(self):
        """Create the Schedule tab for automated actions with account selection."""
        schedule_widget = QWidget()
        main_layout = QHBoxLayout()  # Changed to QHBoxLayout for left-right layout
        # Left side - Account Selection
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        # Account selection section
        account_group = QGroupBox("Select Accounts to Use")
        account_group.setStyleSheet(self.get_groupbox_style())
        account_layout = QVBoxLayout()
        # Selection button
        self.schedule_select_account_btn = QPushButton("Select Account")
        self.schedule_select_account_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        account_layout.addWidget(self.schedule_select_account_btn)
        # Selected accounts table
        self.schedule_selection_table = QTableWidget()
        self.schedule_selection_table.setColumnCount(7)  # Updated to 7 columns (added task_count)
        self.schedule_selection_table.setHorizontalHeaderLabels(["Select", "UID", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.schedule_selection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.schedule_selection_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.schedule_selection_table.setSortingEnabled(True)
        # Set column widths
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.schedule_selection_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QCheckBox {
                margin-left: 15px; /* Center checkbox in cell */
            }
        """)
        # Start with empty table
        self.schedule_selection_table.setRowCount(0)
        account_layout.addWidget(self.schedule_selection_table)
        # Add Select All and Deselect All buttons
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.select_all_in_table(self.schedule_selection_table))
        select_buttons_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self.deselect_all_in_table(self.schedule_selection_table))
        select_buttons_layout.addWidget(deselect_all_btn)
        select_buttons_layout.addStretch()
        account_layout.addLayout(select_buttons_layout)
        # Add counter label
        self.schedule_selection_counter = QLabel("Selected: 0")
        self.schedule_selection_counter.setStyleSheet("color: #E0E0E0; font-weight: bold; padding: 5px;")
        account_layout.addWidget(self.schedule_selection_counter)
        account_group.setLayout(account_layout)
        left_layout.addWidget(account_group)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)  # 1 part width
        # Right side - Schedule Actions
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        # Title
        title_label = QLabel("Automated Scheduling")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4A90E2; margin: 10px 0;")
        right_layout.addWidget(title_label)
        # Schedule Group
        schedule_group = QGroupBox("Schedule Actions")
        schedule_group.setStyleSheet(self.get_groupbox_style())
        schedule_layout = QVBoxLayout()
        # Auto View Feed
        self.auto_view_feed_cb = QCheckBox("Auto View Feed (Scroll through news feed)")
        self.auto_view_feed_cb.setStyleSheet(self.get_checkbox_style())
        schedule_layout.addWidget(self.auto_view_feed_cb)
        # Auto React to Friends' Posts
        self.auto_react_friends_cb = QCheckBox("Auto React to Friends' Posts (Randomly)")
        self.auto_react_friends_cb.setStyleSheet(self.get_checkbox_style())
        schedule_layout.addWidget(self.auto_react_friends_cb)
        # Auto Invite Friends to Group
        self.auto_invite_friends_cb = QCheckBox("Auto Invite All Friends to Join Group")
        self.auto_invite_friends_cb.setStyleSheet(self.get_checkbox_style())
        schedule_layout.addWidget(self.auto_invite_friends_cb)
        # Auto Share to Wall
        self.auto_share_wall_cb = QCheckBox("Auto Share to Wall (Random Content)")
        self.auto_share_wall_cb.setStyleSheet(self.get_checkbox_style())
        schedule_layout.addWidget(self.auto_share_wall_cb)
        # Auto Share to Group
        self.auto_share_group_cb = QCheckBox("Auto Share to Group")
        self.auto_share_group_cb.setStyleSheet(self.get_checkbox_style())
        schedule_layout.addWidget(self.auto_share_group_cb)
        # Target Group Input (for invite/share)
        target_group_layout = QHBoxLayout()
        target_group_layout.addWidget(QLabel("Target Group URL:"))
        self.target_group_input = QLineEdit()
        self.target_group_input.setPlaceholderText("https://www.facebook.com/groups/...")
        self.target_group_input.setStyleSheet(self.get_lineedit_style())
        target_group_layout.addWidget(self.target_group_input)
        schedule_layout.addLayout(target_group_layout)
        schedule_group.setLayout(schedule_layout)
        right_layout.addWidget(schedule_group)
        # Start/Stop Schedule Buttons
        button_layout = QHBoxLayout()
        self.start_schedule_btn = QPushButton("Start Scheduled Actions")
        self.start_schedule_btn.setStyleSheet(self.get_button_style("#4CAF50", "#5DBF60"))
        button_layout.addWidget(self.start_schedule_btn)
        self.stop_schedule_btn = QPushButton("Stop Schedule")
        self.stop_schedule_btn.setStyleSheet(self.get_button_style("#E74C3C", "#F75C4C"))
        self.stop_schedule_btn.setEnabled(False)
        button_layout.addWidget(self.stop_schedule_btn)
        button_layout.addStretch()
        right_layout.addLayout(button_layout)
        # Schedule Log
        log_label = QLabel("Schedule Log:")
        log_label.setStyleSheet("color: #E0E0E0; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(log_label)
        self.schedule_log_output = QTextEdit()
        self.schedule_log_output.setMaximumHeight(200)
        self.schedule_log_output.setReadOnly(True)
        self.schedule_log_output.setStyleSheet(self.get_textedit_style())
        right_layout.addWidget(self.schedule_log_output)
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)  # 1 part width
        schedule_widget.setLayout(main_layout)
        self.tabs.addTab(schedule_widget, "Schedule")
    # --- NEW: Automation Actions Tab ---
    def create_automation_actions_tab(self):
        """Create the Automation Actions tab for bulk processing."""
        automation_widget = QWidget()
        main_layout = QHBoxLayout()  # Changed to QHBoxLayout for left-right layout
        # Left side - Account Selection
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        # Account selection section
        account_group = QGroupBox("Select Accounts to Use")
        account_group.setStyleSheet(self.get_groupbox_style())
        account_layout = QVBoxLayout()
        # Selection button
        self.automation_select_account_btn = QPushButton("Select Account")
        self.automation_select_account_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        account_layout.addWidget(self.automation_select_account_btn)
        # Selected accounts table
        self.automation_selection_table = QTableWidget()
        self.automation_selection_table.setColumnCount(7)  # Updated to 7 columns (added task_count)
        self.automation_selection_table.setHorizontalHeaderLabels(["Select", "UID", "Category", "Status", "Last Login", "Login Count", "Task Count"])
        self.automation_selection_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.automation_selection_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.automation_selection_table.setSortingEnabled(True)
        # Set column widths
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.automation_selection_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252525;
                color: #E0E0E0;
                gridline-color: #3A3A3A;
                border: 1px solid #3A3A3A;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 5px;
                border: 1px solid #3A3A3A;
                font-weight: bold;
            }
            QCheckBox {
                margin-left: 15px; /* Center checkbox in cell */
            }
        """)
        # Start with empty table
        self.automation_selection_table.setRowCount(0)
        account_layout.addWidget(self.automation_selection_table)
        # Add Select All and Deselect All buttons
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self.select_all_in_table(self.automation_selection_table))
        select_buttons_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self.deselect_all_in_table(self.automation_selection_table))
        select_buttons_layout.addWidget(deselect_all_btn)
        select_buttons_layout.addStretch()
        account_layout.addLayout(select_buttons_layout)
        # Add counter label
        self.automation_selection_counter = QLabel("Selected: 0")
        self.automation_selection_counter.setStyleSheet("color: #E0E0E0; font-weight: bold; padding: 5px;")
        account_layout.addWidget(self.automation_selection_counter)
        account_group.setLayout(account_layout)
        left_layout.addWidget(account_group)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)  # 1 part width
        # Right side - Automation Actions
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        # Title
        title_label = QLabel("Automation Actions")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #4A90E2; margin: 10px 0;")
        right_layout.addWidget(title_label)
        # Actions Group
        actions_group = QGroupBox("Select Actions")
        actions_group.setStyleSheet(self.get_groupbox_style())
        actions_layout = QVBoxLayout()
        # Post URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Post URL:")
        url_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        url_layout.addWidget(url_label)
        self.automation_post_url_input = QLineEdit()
        self.automation_post_url_input.setPlaceholderText("https://www.facebook.com/permalink.php?story_fbid=...")
        self.automation_post_url_input.setStyleSheet(self.get_lineedit_style())
        url_layout.addWidget(self.automation_post_url_input)
        actions_layout.addLayout(url_layout)
        # Actions selection
        actions_checkboxes_layout = QHBoxLayout()
        actions_checkboxes_layout.addWidget(QLabel("Actions:"))
        self.automation_like_checkbox = QCheckBox("Like Post")
        self.automation_like_checkbox.setChecked(True)
        self.automation_like_checkbox.setStyleSheet(self.get_checkbox_style())
        self.automation_comment_checkbox = QCheckBox("Comment")
        self.automation_comment_checkbox.setChecked(True)
        self.automation_comment_checkbox.setStyleSheet(self.get_checkbox_style())
        self.automation_react_checkbox = QCheckBox("React")
        self.automation_react_checkbox.setChecked(True)
        self.automation_react_checkbox.setStyleSheet(self.get_checkbox_style())
        self.automation_share_checkbox = QCheckBox("Share Post")  # Added Share checkbox
        self.automation_share_checkbox.setChecked(False)
        self.automation_share_checkbox.setStyleSheet(self.get_checkbox_style())
        actions_checkboxes_layout.addWidget(self.automation_like_checkbox)
        actions_checkboxes_layout.addWidget(self.automation_comment_checkbox)
        actions_checkboxes_layout.addWidget(self.automation_react_checkbox)
        actions_checkboxes_layout.addWidget(self.automation_share_checkbox)
        actions_checkboxes_layout.addStretch()
        actions_layout.addLayout(actions_checkboxes_layout)
        # Reaction type selection
        react_layout = QHBoxLayout()
        react_label = QLabel("Reaction Type:")
        react_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        react_layout.addWidget(react_label)
        self.automation_react_like = QCheckBox("👍 Like")
        self.automation_react_love = QCheckBox("❤️ Love")
        self.automation_react_care = QCheckBox("🤗 Care")
        self.automation_react_haha = QCheckBox("😂 Haha")
        self.automation_react_wow = QCheckBox("😮 Wow")
        self.automation_react_sad = QCheckBox("😢 Sad")
        self.automation_react_angry = QCheckBox("😠 Angry")
        font = QFont("Segoe UI Emoji", 9)
        for checkbox in [self.automation_react_like, self.automation_react_love, self.automation_react_care, self.automation_react_haha, self.automation_react_wow, self.automation_react_sad, self.automation_react_angry]:
            checkbox.setFont(font)
            checkbox.setStyleSheet(self.get_checkbox_style())
            checkbox.setChecked(False)
        self.automation_react_like.setChecked(True)
        react_layout.addWidget(self.automation_react_like)
        react_layout.addWidget(self.automation_react_love)
        react_layout.addWidget(self.automation_react_care)
        react_layout.addWidget(self.automation_react_haha)
        react_layout.addWidget(self.automation_react_wow)
        react_layout.addWidget(self.automation_react_sad)
        react_layout.addWidget(self.automation_react_angry)
        react_layout.addStretch()
        actions_layout.addLayout(react_layout)
        # Comment input with clipboard button
        comment_layout = QHBoxLayout()
        comment_label = QLabel("Comment Text:")
        comment_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        comment_layout.addWidget(comment_label)
        self.automation_comment_input = QTextEdit()
        self.automation_comment_input.setMaximumHeight(60)
        self.automation_comment_input.setPlaceholderText("Enter comment text here... (Supports Emojis 🎉)")
        self.automation_comment_input.setStyleSheet(self.get_textedit_style())
        comment_layout.addWidget(self.automation_comment_input)
        actions_layout.addLayout(comment_layout)
        # Random comments option
        random_comments_layout = QHBoxLayout()
        self.automation_random_comments_checkbox = QCheckBox("Use Random Comments")
        self.automation_random_comments_checkbox.setChecked(False)
        self.automation_random_comments_checkbox.setStyleSheet(self.get_checkbox_style())
        self.automation_random_comments_checkbox.stateChanged.connect(self.toggle_automation_random_comments)
        random_comments_layout.addWidget(self.automation_random_comments_checkbox)
        random_comments_layout.addStretch()
        actions_layout.addLayout(random_comments_layout)
        # Random comments input (initially hidden)
        self.automation_random_comments_group = QGroupBox("Random Comments (One per line)")
        self.automation_random_comments_group.setStyleSheet(self.get_groupbox_style())
        self.automation_random_comments_group.setVisible(False)
        random_comments_inner_layout = QVBoxLayout()
        self.automation_random_comments_input = QTextEdit()
        self.automation_random_comments_input.setMaximumHeight(100)
        self.automation_random_comments_input.setPlaceholderText("Enter multiple comments, one per line Each account will use a different comment (Supports Emojis 🎉)")
        self.automation_random_comments_input.setStyleSheet(self.get_textedit_style())
        random_comments_inner_layout.addWidget(self.automation_random_comments_input)
        self.automation_random_comments_group.setLayout(random_comments_inner_layout)
        actions_layout.addWidget(self.automation_random_comments_group)
        # Clipboard button
        clipboard_layout = QHBoxLayout()
        self.automation_clipboard_btn = QPushButton("Paste from Clipboard")
        self.automation_clipboard_btn.clicked.connect(self.paste_to_automation_comment)
        self.automation_clipboard_btn.setStyleSheet(self.get_button_style("#5D5D5D", "#7A7A7A"))
        clipboard_layout.addWidget(self.automation_clipboard_btn)
        actions_layout.addLayout(clipboard_layout)
        actions_group.setLayout(actions_layout)
        right_layout.addWidget(actions_group)
        # Start/Stop Automation Buttons
        button_layout = QHBoxLayout()
        self.start_automation_btn = QPushButton("Start Automation")
        self.start_automation_btn.setStyleSheet(self.get_button_style("#4CAF50", "#5DBF60"))
        button_layout.addWidget(self.start_automation_btn)
        self.stop_automation_btn = QPushButton("Stop Automation")
        self.stop_automation_btn.setStyleSheet(self.get_button_style("#E74C3C", "#F75C4C"))
        self.stop_automation_btn.setEnabled(False)
        button_layout.addWidget(self.stop_automation_btn)
        button_layout.addStretch()
        right_layout.addLayout(button_layout)
        # Automation Log
        log_label = QLabel("Automation Log:")
        log_label.setStyleSheet("color: #E0E0E0; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(log_label)
        self.automation_log_output = QTextEdit()
        self.automation_log_output.setMaximumHeight(200)
        self.automation_log_output.setReadOnly(True)
        self.automation_log_output.setStyleSheet(self.get_textedit_style())
        right_layout.addWidget(self.automation_log_output)
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)  # 1 part width
        automation_widget.setLayout(main_layout)
        self.tabs.addTab(automation_widget, "Automation Actions")
    def toggle_automation_random_comments(self, state):
        """Show or hide random comments input based on checkbox state"""
        self.automation_random_comments_group.setVisible(state == Qt.CheckState.Checked.value)
    def paste_to_automation_comment(self):
        """Paste text from clipboard to automation comment input"""
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                if self.automation_random_comments_checkbox.isChecked():
                    self.automation_random_comments_input.setPlainText(clipboard_text)
                else:
                    self.automation_comment_input.setPlainText(clipboard_text)
                self.log_message("Pasted text from clipboard to automation comment field")
            else:
                self.log_message("Clipboard is empty")
        except Exception as e:
            self.log_message(f"Error accessing clipboard: {e}")
    def start_automation_actions(self):
        """Start automation actions for selected accounts."""
        selected_accounts = self.get_selected_accounts(self.automation_selection_table)
        if not selected_accounts:
            QMessageBox.warning(self, "No Accounts Selected", "Please select at least one account to automate actions.")
            return
        post_url = self.automation_post_url_input.text().strip()
        if not post_url:
            QMessageBox.warning(self, "Missing URL", "Please enter a post URL.")
            return
        actions = []
        if self.automation_like_checkbox.isChecked():
            actions.append('like')
        if self.automation_comment_checkbox.isChecked():
            actions.append('comment')
        if self.automation_react_checkbox.isChecked():
            actions.append('react')
        if self.automation_share_checkbox.isChecked():
            actions.append('share')
        if not actions:
            QMessageBox.warning(self, "No Actions Selected", "Please select at least one action to automate.")
            return
        comment_text = self.automation_comment_input.toPlainText().strip()
        random_comments = None
        if self.automation_random_comments_checkbox.isChecked():
            random_comments_text = self.automation_random_comments_input.toPlainText().strip()
            if random_comments_text:
                random_comments = [line.strip() for line in random_comments_text.splitlines() if line.strip()]
                if len(random_comments) < len(selected_accounts):
                    self.automation_log_output.append("Warning: Fewer random comments than accounts. Some accounts will reuse comments.")
        selected_reactions = self.get_automation_selected_reactions()
        react_type = selected_reactions[0] if selected_reactions else 'like'
        self.automation_log_output.append(f"[{time.strftime('%H:%M:%S')}] Starting automation for {len(selected_accounts)} accounts...")
        self.automation_log_output.append(f"[{time.strftime('%H:%M:%S')}] Post URL: {post_url}")
        self.automation_log_output.append(f"[{time.strftime('%H:%M:%S')}] Actions: {', '.join(actions)}")
        # Disable buttons
        self.start_automation_btn.setEnabled(False)
        self.stop_automation_btn.setEnabled(True)
        self.automation_select_account_btn.setEnabled(False)
        # Start the login process with automation actions
        account_tuples = [(acc['uid'], acc['password'], acc['token'], acc['cookie']) for acc in selected_accounts]
        self.start_login_process(
            accounts=account_tuples,
            use_proxies=False,
            post_url=post_url,
            comment_text=comment_text,
            actions=actions,
            random_comments=random_comments,
            react_type=react_type
        )
    def stop_automation_actions(self):
        """Stop automation actions."""
        self.stop_login_process()
        self.start_automation_btn.setEnabled(True)
        self.stop_automation_btn.setEnabled(False)
        self.automation_select_account_btn.setEnabled(True)
        self.automation_log_output.append(f"[{time.strftime('%H:%M:%S')}] Automation actions stopped.")
    def get_automation_selected_reactions(self):
        """Get the selected reaction types from automation checkboxes"""
        reactions = []
        if self.automation_react_like.isChecked(): reactions.append('like')
        if self.automation_react_love.isChecked(): reactions.append('love')
        if self.automation_react_care.isChecked(): reactions.append('care')
        if self.automation_react_haha.isChecked(): reactions.append('haha')
        if self.automation_react_wow.isChecked(): reactions.append('wow')
        if self.automation_react_sad.isChecked(): reactions.append('sad')
        if self.automation_react_angry.isChecked(): reactions.append('angry')
        return reactions
    def create_settings_tab(self):
        """Create the settings tab - now positioned last (rightmost)."""
        settings_widget = QWidget()
        main_layout = QHBoxLayout()  # Changed to QHBoxLayout for left-center-right layout
        # Left side - General Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet(self.get_groupbox_style())
        general_layout = QFormLayout()
        self.delay_min = QLineEdit()
        self.delay_max = QLineEdit()
        general_layout.addRow("Min Delay Between Accounts (sec):", self.delay_min)
        general_layout.addRow("Max Delay Between Accounts (sec):", self.delay_max)
        general_group.setLayout(general_layout)
        left_layout.addWidget(general_group)
        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)
        # Center - Proxy Settings
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        proxy_group = QGroupBox("Proxy Settings")
        proxy_group.setStyleSheet(self.get_groupbox_style())
        proxy_layout = QVBoxLayout()
        self.use_proxy_checkbox = QCheckBox("Use Proxies")
        self.use_proxy_checkbox.setStyleSheet(self.get_checkbox_style())
        proxy_layout.addWidget(self.use_proxy_checkbox)
        proxy_info = QLabel("Proxies should be listed in proxies.txt file, one per line")
        proxy_info.setStyleSheet("color: #AAAAAA; margin: 5px 0;")
        proxy_layout.addWidget(proxy_info)
        proxy_group.setLayout(proxy_layout)
        center_layout.addWidget(proxy_group)
        center_layout.addStretch()
        center_widget.setLayout(center_layout)
        main_layout.addWidget(center_widget, 1)
        # Right side - Chrome Settings
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        chrome_group = QGroupBox("Chrome Settings")
        chrome_group.setStyleSheet(self.get_groupbox_style())
        chrome_layout = QVBoxLayout()
        self.headless_checkbox = QCheckBox("Run Chrome in Headless Mode")
        self.headless_checkbox.setStyleSheet(self.get_checkbox_style())
        chrome_layout.addWidget(self.headless_checkbox)
        self.save_profiles_checkbox = QCheckBox("Save Chrome Profiles")
        self.save_profiles_checkbox.setChecked(True)
        self.save_profiles_checkbox.setStyleSheet(self.get_checkbox_style())
        chrome_layout.addWidget(self.save_profiles_checkbox)
        # Session Persistence Setting
        self.session_persistence_checkbox = QCheckBox("Enable Session Persistence (Stay Logged In)")
        self.session_persistence_checkbox.setChecked(True)
        self.session_persistence_checkbox.setStyleSheet(self.get_checkbox_style())
        chrome_layout.addWidget(self.session_persistence_checkbox)
        # Auto Relogin Setting
        self.auto_relogin_checkbox = QCheckBox("Auto Relogin on Session Failure")
        self.auto_relogin_checkbox.setChecked(True)
        self.auto_relogin_checkbox.setStyleSheet(self.get_checkbox_style())
        chrome_layout.addWidget(self.auto_relogin_checkbox)
        # --- NEW: Session Management Settings ---
        session_group = QGroupBox("Session Management")
        session_group.setStyleSheet(self.get_groupbox_style())
        session_layout = QVBoxLayout()
        self.reuse_sessions_checkbox = QCheckBox("Reuse Sessions Across Runs")
        self.reuse_sessions_checkbox.setChecked(True)
        self.reuse_sessions_checkbox.setStyleSheet(self.get_checkbox_style())
        session_layout.addWidget(self.reuse_sessions_checkbox)
        session_storage_layout = QHBoxLayout()
        session_storage_layout.addWidget(QLabel("Session Storage:"))
        self.session_storage_combo = QComboBox()
        self.session_storage_combo.addItems(["profile", "cookies"])
        session_storage_layout.addWidget(self.session_storage_combo)
        session_layout.addLayout(session_storage_layout)
        session_path_layout = QHBoxLayout()
        session_path_layout.addWidget(QLabel("Session Path:"))
        self.session_path_input = QLineEdit()
        self.session_path_input.setPlaceholderText("Folder for sessions")
        session_path_layout.addWidget(self.session_path_input)
        session_layout.addLayout(session_path_layout)
        session_group.setLayout(session_layout)
        chrome_layout.addWidget(session_group)
        # --- NEW: Grid Layout Settings ---
        grid_group = QGroupBox("Grid Layout")
        grid_group.setStyleSheet(self.get_groupbox_style())
        grid_layout = QVBoxLayout()
        self.grid_layout_checkbox = QCheckBox("Enable Grid Layout for Multiple Windows")
        self.grid_layout_checkbox.setChecked(True)
        self.grid_layout_checkbox.setStyleSheet(self.get_checkbox_style())
        grid_layout.addWidget(self.grid_layout_checkbox)
        grid_spacing_layout = QHBoxLayout()
        grid_spacing_layout.addWidget(QLabel("Grid Spacing (px):"))
        self.grid_spacing_input = QLineEdit()
        self.grid_spacing_input.setPlaceholderText("Spacing between windows")
        grid_spacing_layout.addWidget(self.grid_spacing_input)
        grid_layout.addLayout(grid_spacing_layout)
        window_size_layout = QHBoxLayout()
        window_size_layout.addWidget(QLabel("Default Window Size:"))
        self.window_width_input = QLineEdit()
        self.window_width_input.setPlaceholderText("Width")
        self.window_height_input = QLineEdit()
        self.window_height_input.setPlaceholderText("Height")
        window_size_layout.addWidget(self.window_width_input)
        window_size_layout.addWidget(self.window_height_input)
        grid_layout.addLayout(window_size_layout)
        grid_group.setLayout(grid_layout)
        chrome_layout.addWidget(grid_group)
        # --- NEW: Concurrency Settings ---
        concurrency_group = QGroupBox("Concurrency Settings")
        concurrency_group.setStyleSheet(self.get_groupbox_style())
        concurrency_layout = QVBoxLayout()
        concurrency_info = QLabel("Maximum number of browsers to run simultaneously")
        concurrency_info.setStyleSheet("color: #AAAAAA; margin: 5px 0;")
        concurrency_layout.addWidget(concurrency_info)
        concurrency_input_layout = QHBoxLayout()
        concurrency_input_layout.addWidget(QLabel("Max Concurrent Browsers:"))
        self.max_concurrent_input = QLineEdit()
        self.max_concurrent_input.setPlaceholderText("3")
        concurrency_input_layout.addWidget(self.max_concurrent_input)
        concurrency_layout.addLayout(concurrency_input_layout)
        concurrency_group.setLayout(concurrency_layout)
        chrome_layout.addWidget(concurrency_group)
        # --- END NEW ---
        chrome_group.setLayout(chrome_layout)
        right_layout.addWidget(chrome_group)
        # --- ADDED: Save Settings Button ---
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.setStyleSheet(self.get_button_style("#4A90E2", "#5AA0F2"))
        save_layout.addWidget(self.save_settings_btn)
        right_layout.addLayout(save_layout)
        # --- END ADDED ---
        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)
        settings_widget.setLayout(main_layout)
        self.tabs.addTab(settings_widget, "Settings")
    # --- ADDED: Methods for Config Persistence ---
    def load_settings_from_config(self):
        """Load settings from the config manager into the UI."""
        self.delay_min.setText(str(self.config_manager.get("delay_min", 5)))
        self.delay_max.setText(str(self.config_manager.get("delay_max", 15)))
        self.use_proxy_checkbox.setChecked(self.config_manager.get("use_proxy", False))
        self.headless_checkbox.setChecked(self.config_manager.get("headless", False))
        self.save_profiles_checkbox.setChecked(self.config_manager.get("save_profiles", True))
        self.session_persistence_checkbox.setChecked(self.config_manager.get("session_persistence", True))
        self.auto_relogin_checkbox.setChecked(self.config_manager.get("auto_relogin_on_failure", True))
        # --- NEW: Load Session Management Settings ---
        self.reuse_sessions_checkbox.setChecked(self.config_manager.get("reuse_sessions", True))
        self.session_storage_combo.setCurrentText(self.config_manager.get("session_storage", "profile"))
        self.session_path_input.setText(self.config_manager.get("session_path", "chrome_profiles"))
        # --- NEW: Load Grid Layout Settings ---
        self.grid_layout_checkbox.setChecked(self.config_manager.get("grid_layout", True))
        self.grid_spacing_input.setText(str(self.config_manager.get("grid_spacing", 10)))
        default_size = self.config_manager.get("default_window_size", [800, 600])
        self.window_width_input.setText(str(default_size[0]))
        self.window_height_input.setText(str(default_size[1]))
        # --- NEW: Load Concurrency Settings ---
        self.max_concurrent_input.setText(str(self.config_manager.get("max_concurrent_browsers", 3)))
        # --- END NEW ---
    def save_settings_to_config(self):
        """Save settings from the UI to the config manager."""
        try:
            min_delay = int(self.delay_min.text())
            max_delay = int(self.delay_max.text())
            if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
                raise ValueError("Invalid delay values")
            self.config_manager.set("delay_min", min_delay)
            self.config_manager.set("delay_max", max_delay)
            self.config_manager.set("use_proxy", self.use_proxy_checkbox.isChecked())
            self.config_manager.set("headless", self.headless_checkbox.isChecked())
            self.config_manager.set("save_profiles", self.save_profiles_checkbox.isChecked())
            self.config_manager.set("session_persistence", self.session_persistence_checkbox.isChecked())
            self.config_manager.set("auto_relogin_on_failure", self.auto_relogin_checkbox.isChecked())
            # --- NEW: Save Session Management Settings ---
            self.config_manager.set("reuse_sessions", self.reuse_sessions_checkbox.isChecked())
            self.config_manager.set("session_storage", self.session_storage_combo.currentText())
            self.config_manager.set("session_path", self.session_path_input.text().strip())
            # --- NEW: Save Grid Layout Settings ---
            self.config_manager.set("grid_layout", self.grid_layout_checkbox.isChecked())
            self.config_manager.set("grid_spacing", int(self.grid_spacing_input.text().strip()))
            default_size = [
                int(self.window_width_input.text().strip()),
                int(self.window_height_input.text().strip())
            ]
            self.config_manager.set("default_window_size", default_size)
            # --- NEW: Save Concurrency Settings ---
            max_concurrent = int(self.max_concurrent_input.text().strip())
            if max_concurrent < 1:
                raise ValueError("Max concurrent browsers must be at least 1")
            self.config_manager.set("max_concurrent_browsers", max_concurrent)
            # --- END NEW ---
            QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for delays and concurrency. Min should be <= Max, and concurrency must be at least 1.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    # --- END ADDED ---
    # --- MODIFIED: Update category combo to fetch from DB ---
    def update_category_combo(self):
        """Update category combo boxes from database"""
        # --- MODIFIED: Get categories from DB ---
        categories = self.get_categories()
        # --- END MODIFIED ---
        current_filter = self.category_filter_combo.currentText()
        current_dashboard = self.category_combo.currentText()
        self.category_filter_combo.clear()
        self.category_filter_combo.addItems(["All Categories"] + categories)
        self.category_combo.clear()
        self.category_combo.addItems(["All Categories"] + categories)
        if current_filter in ["All Categories"] + categories:
            self.category_filter_combo.setCurrentText(current_filter)
        if current_dashboard in ["All Categories"] + categories:
            self.category_combo.setCurrentText(current_dashboard)
    # --- MODIFIED: Get categories from DB ---
    def get_categories(self):
        """Get unique categories from the database."""
        try:
            accounts = self.db_manager.get_all_accounts()
            categories = set(acc['category'] for acc in accounts)
            return sorted(list(categories))
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return ["Default", "Working", "Testing", "Backup", "VIP"]
    # --- END MODIFIED ---
    def show_add_account_dialog(self):
        """Show dialog to add a new account"""
        dialog = AddAccountDialog(self.get_categories(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            account_data = dialog.get_account_data()
            if account_data['uid']:
                category = account_data['category']
                # --- MODIFIED: Add account to DB ---
                success = self.db_manager.add_account(
                    account_data['uid'],
                    account_data['password'],
                    account_data['token'],
                    account_data['cookie'],
                    category
                )
                if success:
                    self.log_message(f"Added new account: {account_data['uid']} to category: {category}")
                    self.load_accounts_to_table()
                    self.update_system_monitor()
                    self.update_dashboard_stats()
                else:
                    QMessageBox.warning(self, "Error", "An account with this UID already exists!")
                # --- END MODIFIED ---
            else:
                QMessageBox.warning(self, "Error", "UID is required!")
    def show_add_category_dialog(self):
        """Show dialog to add a new category"""
        dialog = AddCategoryDialog(self.get_categories(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_name = dialog.get_category_name()
            if category_name:
                # --- MODIFIED: Add category to DB (via account update) ---
                # Since categories are derived from accounts, we don't store them separately.
                # We'll just update the combo boxes.
                self.update_category_combo()
                self.log_message(f"Added new category: {category_name} (Note: Categories are dynamic based on accounts)")
                # --- END MODIFIED ---
            else:
                QMessageBox.warning(self, "Error", "Category name cannot be empty!")
    def delete_selected_category(self):
        """Delete the selected category"""
        category_name = self.category_filter_combo.currentText()
        if category_name == "All Categories":
            QMessageBox.warning(self, "Error", "Cannot delete 'All Categories'!")
            return
        if category_name == "Default":
            QMessageBox.warning(self, "Error", "Cannot delete 'Default' category!")
            return
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete category '{category_name}'? All accounts in this category will be moved to 'Default'.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # --- MODIFIED: Update accounts in DB to move to 'Default' ---
            accounts = self.db_manager.get_all_accounts()
            moved_count = 0
            for account in accounts:
                if account['category'] == category_name:
                    self.db_manager.update_account_category(account['uid'], "Default")
                    moved_count += 1
            if moved_count > 0:
                self.log_message(f"Moved {moved_count} accounts from '{category_name}' to 'Default'")
            self.update_category_combo()
            self.load_accounts_to_table()
            self.update_dashboard_stats()
            # --- END MODIFIED ---
    def filter_accounts_by_category(self):
        """Filter accounts by selected category"""
        self.load_accounts_to_table()
    def toggle_random_comments(self, state):
        """Show or hide random comments input based on checkbox state"""
        self.random_comments_group.setVisible(state == Qt.CheckState.Checked.value)
    def toggle_react_checkboxes(self, state):
        """Enable or disable reaction checkboxes based on react checkbox state"""
        enabled = state == Qt.CheckState.Checked.value
        for checkbox in [self.react_like, self.react_love, self.react_care, self.react_haha, self.react_wow, self.react_sad, self.react_angry]:
            checkbox.setEnabled(enabled)
    def get_selected_reactions(self):
        """Get the selected reaction types from checkboxes"""
        reactions = []
        if self.react_like.isChecked(): reactions.append('like')
        if self.react_love.isChecked(): reactions.append('love')
        if self.react_care.isChecked(): reactions.append('care')
        if self.react_haha.isChecked(): reactions.append('haha')
        if self.react_wow.isChecked(): reactions.append('wow')
        if self.react_sad.isChecked(): reactions.append('sad')
        if self.react_angry.isChecked(): reactions.append('angry')
        return reactions
    def paste_from_clipboard(self):
        """Paste text from clipboard to comment input"""
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                if self.random_comments_checkbox.isChecked():
                    self.random_comments_input.setPlainText(clipboard_text)
                else:
                    self.comment_input.setPlainText(clipboard_text)
                self.log_message("Pasted text from clipboard to comment field")
            else:
                self.log_message("Clipboard is empty")
        except Exception as e:
            self.log_message(f"Error accessing clipboard: {e}")
    def log_message(self, message):
        """Add message to log output"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
    def parse_textarea(self):
        """Split textarea input into table rows and save to account manager"""
        text = self.textarea.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Data", "Please paste some accounts first.")
            return
        new_accounts = 0
        for line in text.splitlines():
            if line.strip():
                parts = [part.strip() for part in line.split("|")]
                while len(parts) < 4:
                    parts.append("")
                uid, password, token, cookie = parts[:4]
                if uid:
                    # --- MODIFIED: Check if account exists in DB ---
                    existing = self.db_manager.get_account_by_uid(uid)
                    if not existing:
                        current_category = self.category_filter_combo.currentText()
                        if current_category == "All Categories":
                            current_category = "Default"
                        # --- MODIFIED: Add to DB ---
                        success = self.db_manager.add_account(uid, password, token, cookie, current_category)
                        if success:
                            new_accounts += 1
                        # --- END MODIFIED ---
        self.load_accounts_to_table()
        self.update_system_monitor()
        self.update_dashboard_stats()
        self.status_label.setText(f"Imported {new_accounts} new accounts")
        self.log_message(f"Imported {new_accounts} new accounts from input")
    def load_accounts_to_table(self):
        """Load accounts from account manager to both tables"""
        category_filter = self.category_filter_combo.currentText()
        # --- MODIFIED: Fetch accounts from DB ---
        if category_filter == "All Categories":
            accounts = self.db_manager.get_all_accounts()
        else:
            accounts = [acc for acc in self.db_manager.get_all_accounts() if acc['category'] == category_filter]
        # --- END MODIFIED ---
        # Populate the main table (in Import Custom tab)
        self.table.setRowCount(len(accounts))
        for r, account in enumerate(accounts):
            self.table.setItem(r, 0, QTableWidgetItem(account['uid']))
            self.table.setItem(r, 1, QTableWidgetItem(account['password']))
            self.table.setItem(r, 2, QTableWidgetItem(account['token']))
            self.table.setItem(r, 3, QTableWidgetItem(account['cookie']))
            self.table.setItem(r, 4, QTableWidgetItem(account['category']))
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            # --- NEW: Color for 'Error' status ---
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.table.setItem(r, 5, status_item)
            self.table.setItem(r, 6, QTableWidgetItem(account['last_login'] or "Never"))
            self.table.setItem(r, 7, QTableWidgetItem(str(account['login_count'])))
            # --- ADDED: Task Count column ---
            self.table.setItem(r, 8, QTableWidgetItem(str(account['task_count'])))
            # --- END ADDED ---
        # Populate the selection table (in Account Manager tab)
        # --- TABLE IS NOW POPULATED ONLY VIA THE DIALOG ---
        # We leave it empty here as per the new requirement.
        # The user must click "Select Account" to populate it.
        self.selection_table.setRowCount(0)
        has_accounts = len(accounts) > 0
        self.auto_login_btn.setEnabled(has_accounts)
        self.interact_btn.setEnabled(has_accounts)
        self.status_label.setText(f"Loaded {len(accounts)} accounts")
        self.log_message(f"Loaded {len(accounts)} accounts")
    def open_context_menu(self, pos: QPoint, table):
        """Right click menu with nested Login submenu for any table"""
        item = table.itemAt(pos)
        if not item:
            return
        row = item.row()
        uid_item = table.item(row, 0) if table.columnCount() > 0 else None
        if not uid_item:
            return
        uid = uid_item.text()
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4A90E2;
            }
        """)
        # Login submenu
        login_menu = QMenu("Login", self)
        login_menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4A90E2;
            }
        """)
        login_pass_action = login_menu.addAction("Login with UID/Password")
        login_token_action = login_menu.addAction("Login with Token/Cookie")
        menu.addMenu(login_menu)
        # For the main table, also add category change
        if table == self.table:
            # Category submenu
            category_menu = QMenu("Change Category", self)
            category_menu.setStyleSheet("""
                QMenu {
                    background-color: #2D2D2D;
                    color: #E0E0E0;
                    border: 1px solid #555555;
                }
                QMenu::item:selected {
                    background-color: #4A90E2;
                }
            """)
            # --- MODIFIED: Get categories from DB ---
            for category in self.get_categories():
                action = category_menu.addAction(category)
                action.triggered.connect(lambda checked, cat=category: self.change_account_category(uid, cat))
            # --- END MODIFIED ---
            menu.addMenu(category_menu)
            # Other actions for main table
            copy_action = menu.addAction("Copy UID")
            delete_action = menu.addAction("Delete Account")
            # Connect actions
            copy_action.triggered.connect(lambda: self.copy_uid(uid))
            delete_action.triggered.connect(lambda: self.delete_account(row))
        # Connect login actions
        login_pass_action.triggered.connect(lambda: self.login_single_account_from_table(table, row, "password"))
        login_token_action.triggered.connect(lambda: self.login_single_account_from_table(table, row, "token"))
        menu.exec(table.mapToGlobal(pos))
    def login_single_account_from_table(self, table, row, method):
        """Login to a single account from any table"""
        uid = table.item(row, 0).text()
        # --- MODIFIED: Get account from DB ---
        account = self.db_manager.get_account_by_uid(uid)
        # --- END MODIFIED ---
        if not account:
            return
        if method == "password" and (not account['uid'] or not account['password']):
            QMessageBox.warning(self, "Missing Info", "UID and Password are required for this method.")
            return
        elif method == "token" and (not account['token'] and not account['cookie']):
            QMessageBox.warning(self, "Missing Info", "Token or Cookie is required for this method.")
            return
        self.log_message(f"Starting {method} login for UID: {uid}")
        # Create accounts tuple for login thread
        accounts = [(account['uid'], account['password'], account['token'], account['cookie'])]
        # Create and start login manager
        login_manager = ParallelLoginManager(accounts, False, None, None, None, None, None, self.db_manager, config_manager=self.config_manager)
        def on_login_finished():
            # Refresh all tables to show updated status
            self.load_accounts_to_table()
            if hasattr(self, 'schedule_selection_table'):
                # If we're in the schedule tab, refresh that table too
                self.refresh_schedule_selection_table()
            if hasattr(self, 'info_selection_table'):
                # If we're in the account info tab, refresh that table too
                self.refresh_info_selection_table()
            if hasattr(self, 'automation_selection_table'):
                # If we're in the automation tab, refresh that table too
                self.refresh_automation_selection_table()
        login_manager.finished.connect(on_login_finished)
        login_manager.log_message.connect(self.log_message)
        login_manager.start()
    def change_account_category(self, uid, new_category):
        """Change account category"""
        # --- MODIFIED: Update category in DB ---
        success = self.db_manager.update_account_category(uid, new_category)
        if success:
            self.load_accounts_to_table()
            self.update_dashboard_stats()
            self.log_message(f"Changed category for {uid} to {new_category}")
        else:
            QMessageBox.warning(self, "Error", "Failed to update category.")
        # --- END MODIFIED ---
    def copy_uid(self, uid):
        """Copy UID to clipboard"""
        pyperclip.copy(uid)
        self.log_message(f"Copied UID: {uid} to clipboard")
    def delete_account(self, row):
        """Delete account from table and account manager"""
        uid = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete account {uid}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # --- MODIFIED: Delete from DB ---
            success = self.db_manager.delete_account(uid)
            if success:
                self.load_accounts_to_table()
                self.update_system_monitor()
                self.update_dashboard_stats()
                self.log_message(f"Deleted account: {uid}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete account.")
            # --- END MODIFIED ---
    # --- MODIFIED: Method for the "Select Account" button in Account Manager ---
    def open_account_selection_dialog(self):
        """Open the account selection dialog and populate the selection table."""
        # --- MODIFIED: Pass db_manager to dialog ---
        dialog = AccountSelectionDialog(self.db_manager, self)
        # --- END MODIFIED ---
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_accounts = dialog.get_selected_accounts()
            if selected_accounts:
                self.populate_selection_table(selected_accounts)
                self.log_message(f"Selected {len(selected_accounts)} accounts via dialog.")
            else:
                self.log_message("No accounts selected.")
    # --- NEW: Method for the "Select Account" button in Schedule Tab ---
    def open_schedule_account_selection_dialog(self):
        """Open the account selection dialog and populate the schedule selection table."""
        # --- MODIFIED: Pass db_manager to dialog ---
        dialog = AccountSelectionDialog(self.db_manager, self)
        # --- END MODIFIED ---
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_accounts = dialog.get_selected_accounts()
            if selected_accounts:
                self.populate_schedule_selection_table(selected_accounts)
                self.log_message(f"Selected {len(selected_accounts)} accounts for scheduling via dialog.")
            else:
                self.log_message("No accounts selected for scheduling.")
    # --- NEW: Method for the "Select Account" button in Account Info Tab ---
    def open_account_info_selection_dialog(self):
        """Open the account selection dialog and populate the account info selection table."""
        # --- MODIFIED: Pass db_manager to dialog ---
        dialog = AccountSelectionDialog(self.db_manager, self)
        # --- END MODIFIED ---
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_accounts = dialog.get_selected_accounts()
            if selected_accounts:
                self.populate_info_selection_table(selected_accounts)
                self.log_message(f"Selected {len(selected_accounts)} accounts for profile upload via dialog.")
            else:
                self.log_message("No accounts selected for profile upload.")
    # --- NEW: Method for the "Select Account" button in Automation Actions Tab ---
    def open_automation_account_selection_dialog(self):
        """Open the account selection dialog and populate the automation selection table."""
        # --- MODIFIED: Pass db_manager to dialog ---
        dialog = AccountSelectionDialog(self.db_manager, self)
        # --- END MODIFIED ---
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_accounts = dialog.get_selected_accounts()
            if selected_accounts:
                self.populate_automation_selection_table(selected_accounts)
                self.log_message(f"Selected {len(selected_accounts)} accounts for automation via dialog.")
            else:
                self.log_message("No accounts selected for automation.")
    # --- MODIFIED: Method to populate the selection table from dialog ---
    def populate_selection_table(self, accounts):
        """Populate the selection table with accounts from the dialog."""
        self.selection_table.setRowCount(len(accounts))
        for r, account in enumerate(accounts):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:15px;")
            checkbox.stateChanged.connect(lambda state, row=r: self.update_selection_counter(self.selection_table, getattr(self, 'manager_selection_counter', None)))
            self.selection_table.setCellWidget(r, 0, checkbox)
            # UID
            uid_item = QTableWidgetItem(account['uid'])
            self.selection_table.setItem(r, 1, uid_item)
            # Password
            password_item = QTableWidgetItem(account['password'])
            self.selection_table.setItem(r, 2, password_item)
            # Token
            token_item = QTableWidgetItem(account['token'])
            self.selection_table.setItem(r, 3, token_item)
            # Cookie
            cookie_item = QTableWidgetItem(account['cookie'])
            self.selection_table.setItem(r, 4, cookie_item)
            # Category
            category_item = QTableWidgetItem(account['category'])
            self.selection_table.setItem(r, 5, category_item)
            # Status
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.selection_table.setItem(r, 6, status_item)
            # Last Login
            last_login_item = QTableWidgetItem(account['last_login'] or "Never")
            self.selection_table.setItem(r, 7, last_login_item)
            # Login Count
            login_count_item = QTableWidgetItem(str(account['login_count']))
            self.selection_table.setItem(r, 8, login_count_item)
            # Task Count (NEW)
            task_count_item = QTableWidgetItem(str(account['task_count']))
            self.selection_table.setItem(r, 9, task_count_item)
        # Enable buttons if accounts are present
        has_accounts = len(accounts) > 0
        self.auto_login_btn.setEnabled(has_accounts)
        self.interact_btn.setEnabled(has_accounts)
        # Initialize counter
        self.update_selection_counter(self.selection_table, getattr(self, 'manager_selection_counter', None))
    # --- NEW: Method to populate the schedule selection table from dialog ---
    def populate_schedule_selection_table(self, accounts):
        """Populate the schedule selection table with accounts from the dialog."""
        self.schedule_selection_table.setRowCount(len(accounts))
        for r, account in enumerate(accounts):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:15px;")
            checkbox.stateChanged.connect(lambda state, row=r: self.update_selection_counter(self.schedule_selection_table, self.schedule_selection_counter))
            self.schedule_selection_table.setCellWidget(r, 0, checkbox)
            # UID
            uid_item = QTableWidgetItem(account['uid'])
            self.schedule_selection_table.setItem(r, 1, uid_item)
            # Category
            category_item = QTableWidgetItem(account['category'])
            self.schedule_selection_table.setItem(r, 2, category_item)
            # Status
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.schedule_selection_table.setItem(r, 3, status_item)
            # Last Login
            last_login_item = QTableWidgetItem(account['last_login'] or "Never")
            self.schedule_selection_table.setItem(r, 4, last_login_item)
            # Login Count
            login_count_item = QTableWidgetItem(str(account['login_count']))
            self.schedule_selection_table.setItem(r, 5, login_count_item)
            # Task Count (NEW)
            task_count_item = QTableWidgetItem(str(account['task_count']))
            self.schedule_selection_table.setItem(r, 6, task_count_item)
        # Enable start button if accounts are present
        has_accounts = len(accounts) > 0
        self.start_schedule_btn.setEnabled(has_accounts)
        # Initialize counter
        self.update_selection_counter(self.schedule_selection_table, self.schedule_selection_counter)
    # --- NEW: Method to populate the account info selection table from dialog ---
    def populate_info_selection_table(self, accounts):
        """Populate the account info selection table with accounts from the dialog."""
        self.info_selection_table.setRowCount(len(accounts))
        for r, account in enumerate(accounts):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:15px;")
            checkbox.stateChanged.connect(lambda state, row=r: self.update_selection_counter(self.info_selection_table, self.info_selection_counter))
            self.info_selection_table.setCellWidget(r, 0, checkbox)
            # UID
            uid_item = QTableWidgetItem(account['uid'])
            self.info_selection_table.setItem(r, 1, uid_item)
            # Category
            category_item = QTableWidgetItem(account['category'])
            self.info_selection_table.setItem(r, 2, category_item)
            # Status
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.info_selection_table.setItem(r, 3, status_item)
            # Last Login
            last_login_item = QTableWidgetItem(account['last_login'] or "Never")
            self.info_selection_table.setItem(r, 4, last_login_item)
            # Login Count
            login_count_item = QTableWidgetItem(str(account['login_count']))
            self.info_selection_table.setItem(r, 5, login_count_item)
            # Task Count (NEW)
            task_count_item = QTableWidgetItem(str(account['task_count']))
            self.info_selection_table.setItem(r, 6, task_count_item)
        # Initialize counter
        self.update_selection_counter(self.info_selection_table, self.info_selection_counter)
    # --- NEW: Method to populate the automation selection table from dialog ---
    def populate_automation_selection_table(self, accounts):
        """Populate the automation selection table with accounts from the dialog."""
        self.automation_selection_table.setRowCount(len(accounts))
        for r, account in enumerate(accounts):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:15px;")
            checkbox.stateChanged.connect(lambda state, row=r: self.update_selection_counter(self.automation_selection_table, self.automation_selection_counter))
            self.automation_selection_table.setCellWidget(r, 0, checkbox)
            # UID
            uid_item = QTableWidgetItem(account['uid'])
            self.automation_selection_table.setItem(r, 1, uid_item)
            # Category
            category_item = QTableWidgetItem(account['category'])
            self.automation_selection_table.setItem(r, 2, category_item)
            # Status
            status_item = QTableWidgetItem(account['status'])
            if account['status'] == 'Working':
                status_item.setForeground(QColor("#4CAF50"))
            elif account['status'] == 'Failed':
                status_item.setForeground(QColor("#E74C3C"))
            elif account['status'] == 'Error':
                status_item.setForeground(QColor("#9932CC"))
            else:
                status_item.setForeground(QColor("#F39C12"))
            self.automation_selection_table.setItem(r, 3, status_item)
            # Last Login
            last_login_item = QTableWidgetItem(account['last_login'] or "Never")
            self.automation_selection_table.setItem(r, 4, last_login_item)
            # Login Count
            login_count_item = QTableWidgetItem(str(account['login_count']))
            self.automation_selection_table.setItem(r, 5, login_count_item)
            # Task Count (NEW)
            task_count_item = QTableWidgetItem(str(account['task_count']))
            self.automation_selection_table.setItem(r, 6, task_count_item)
        # Enable start button if accounts are present
        has_accounts = len(accounts) > 0
        self.start_automation_btn.setEnabled(has_accounts)
        # Initialize counter
        self.update_selection_counter(self.automation_selection_table, self.automation_selection_counter)
    # --- NEW: Helper method to refresh schedule selection table ---
    def refresh_schedule_selection_table(self):
        """Refresh the schedule selection table with current account data."""
        # Get currently selected UIDs
        selected_uids = []
        for row in range(self.schedule_selection_table.rowCount()):
            uid_item = self.schedule_selection_table.item(row, 1)
            if uid_item:
                selected_uids.append(uid_item.text())
        # Get updated account data
        updated_accounts = []
        for uid in selected_uids:
            # --- MODIFIED: Get account from DB ---
            account = self.db_manager.get_account_by_uid(uid)
            if account:
                updated_accounts.append(account)
            # --- END MODIFIED ---
        # Repopulate table
        self.populate_schedule_selection_table(updated_accounts)
    # --- NEW: Helper method to refresh account info selection table ---
    def refresh_info_selection_table(self):
        """Refresh the account info selection table with current account data."""
        # Get currently selected UIDs
        selected_uids = []
        for row in range(self.info_selection_table.rowCount()):
            uid_item = self.info_selection_table.item(row, 1)
            if uid_item:
                selected_uids.append(uid_item.text())
        # Get updated account data
        updated_accounts = []
        for uid in selected_uids:
            # --- MODIFIED: Get account from DB ---
            account = self.db_manager.get_account_by_uid(uid)
            if account:
                updated_accounts.append(account)
            # --- END MODIFIED ---
        # Repopulate table
        self.populate_info_selection_table(updated_accounts)
    # --- NEW: Helper method to refresh automation selection table ---
    def refresh_automation_selection_table(self):
        """Refresh the automation selection table with current account data."""
        # Get currently selected UIDs
        selected_uids = []
        for row in range(self.automation_selection_table.rowCount()):
            uid_item = self.automation_selection_table.item(row, 1)
            if uid_item:
                selected_uids.append(uid_item.text())
        # Get updated account data
        updated_accounts = []
        for uid in selected_uids:
            # --- MODIFIED: Get account from DB ---
            account = self.db_manager.get_account_by_uid(uid)
            if account:
                updated_accounts.append(account)
            # --- END MODIFIED ---
        # Repopulate table
        self.populate_automation_selection_table(updated_accounts)
    def get_selected_accounts(self, table=None):
        """Get list of selected accounts from the specified table"""
        if table is None:
            table = self.selection_table
        selected_accounts = []
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget and checkbox_widget.isChecked():
                uid = table.item(row, 1).text()
                # --- MODIFIED: Get full account data from DB ---
                account = self.db_manager.get_account_by_uid(uid)
                if account:
                    selected_accounts.append(account)
                # --- END MODIFIED ---
        return selected_accounts
    def start_auto_login_selected(self):
        """Start auto login for selected accounts"""
        selected_accounts = self.get_selected_accounts()
        if not selected_accounts:
            QMessageBox.warning(self, "No Accounts Selected", "Please select at least one account to login.")
            return
        account_tuples = [(acc['uid'], acc['password'], acc['token'], acc['cookie']) for acc in selected_accounts]
        self.start_login_process(account_tuples, False)
    def start_interaction_selected(self):
        """Start login and interaction with post for selected accounts"""
        self.log_message("=" * 80)
        self.log_message("🚀 START INTERACTION SELECTED - Button clicked!")
        self.log_message("=" * 80)
        
        selected_accounts = self.get_selected_accounts()
        if not selected_accounts:
            QMessageBox.warning(self, "No Accounts Selected", "Please select at least one account to interact.")
            return
        
        self.log_message(f"✅ Selected {len(selected_accounts)} accounts")
        
        post_url = self.post_url_input.text().strip()
        self.log_message(f"📋 Post URL: {post_url}")
        if not post_url:
            QMessageBox.warning(self, "Missing URL", "Please enter a post URL.")
            return
        
        actions = []
        if self.like_checkbox.isChecked():
            actions.append('like')
        if self.comment_checkbox.isChecked():
            actions.append('comment')
        if self.react_checkbox.isChecked():
            actions.append('react')
        if self.share_checkbox.isChecked():  # Added share action
            actions.append('share')
        
        self.log_message(f"✅ Actions selected: {actions}")
        
        if not actions:
            QMessageBox.warning(self, "No Actions", "Please select at least one action.")
            return
        
        comment_text = self.comment_input.toPlainText().strip()
        self.log_message(f"📝 Comment text: {comment_text if comment_text else '(empty)'}")
        
        random_comments = None
        if self.random_comments_checkbox.isChecked():
            random_comments_text = self.random_comments_input.toPlainText().strip()
            if random_comments_text:
                random_comments = [line.strip() for line in random_comments_text.splitlines() if line.strip()]
                self.log_message(f"✅ Random comments: {len(random_comments)} comments loaded")
                if len(random_comments) < len(selected_accounts):
                    self.log_message("⚠️ Warning: Fewer random comments than accounts. Some accounts will reuse comments.")
            else:
                self.log_message("⚠️ Random comments checkbox is checked but no comments provided")
        
        selected_reactions = self.get_selected_reactions()
        react_type = selected_reactions[0] if selected_reactions else 'like'
        self.log_message(f"😊 Reaction type: {react_type}")
        
        account_tuples = [(acc['uid'], acc['password'], acc['token'], acc['cookie']) for acc in selected_accounts]
        
        self.log_message("🎯 CALLING start_login_process with:")
        self.log_message(f"   - Accounts: {len(account_tuples)}")
        self.log_message(f"   - Post URL: {post_url}")
        self.log_message(f"   - Actions: {actions}")
        self.log_message(f"   - React Type: {react_type}")
        self.log_message(f"   - Comment Text: {'Yes' if comment_text else 'No'}")
        self.log_message(f"   - Random Comments: {'Yes' if random_comments else 'No'}")
        self.log_message("=" * 80)
        
        self.start_login_process(account_tuples, False, post_url, comment_text, actions, random_comments, react_type)
    def start_login_process(self, accounts, use_proxies=False, post_url=None, comment_text=None, actions=None, random_comments=None, react_type=None, target_group_url=None, schedule_actions=None):
        """Start the login process using parallel execution"""
        self.log_message("🔧 DEBUG: start_login_process called")
        self.log_message(f"🔧 DEBUG: Parameters received:")
        self.log_message(f"   - accounts: {len(accounts)}")
        self.log_message(f"   - post_url: {post_url}")
        self.log_message(f"   - actions: {actions}")
        self.log_message(f"   - comment_text: {'Yes' if comment_text else 'No'}")
        self.log_message(f"   - random_comments: {'Yes' if random_comments else 'No'}")
        self.log_message(f"   - react_type: {react_type}")
        self.log_message(f"   - target_group_url: {target_group_url}")
        self.log_message(f"   - schedule_actions: {schedule_actions}")
        
        if self.login_manager and self.login_manager.running:
            self.log_message("A process is already running. Please stop it first.")
            return
        # Disable UI elements
        self.start_btn.setEnabled(False)
        self.auto_login_btn.setEnabled(False)
        self.interact_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_account_btn.setEnabled(False)
        self.add_category_btn.setEnabled(False)
        self.delete_category_btn.setEnabled(False)
        self.select_account_btn.setEnabled(False)
        if hasattr(self, 'schedule_select_account_btn'):
            self.schedule_select_account_btn.setEnabled(False)
        if hasattr(self, 'info_select_account_btn'):
            self.info_select_account_btn.setEnabled(False)
        if hasattr(self, 'automation_select_account_btn'):
            self.automation_select_account_btn.setEnabled(False)
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(accounts))
        self.progress_bar.setValue(0)
        # Create and start parallel login manager
        self.login_manager = ParallelLoginManager(
            accounts, use_proxies, post_url, comment_text, actions, 
            random_comments, react_type, self.db_manager, 
            target_group_url, schedule_actions, self.config_manager
        )
        # Connect signals
        self.login_manager.worker_finished.connect(self.update_table_status)
        self.login_manager.log_message.connect(self.log_message)
        self.login_manager.interaction_update.connect(self.update_interaction_status)
        # --- MODIFIED: Connect to new handler ---
        self.login_manager.account_status_update.connect(self.on_account_status_update)
        # --- END MODIFIED ---
        self.login_manager.task_completed.connect(self.on_task_completed)
        self.login_manager.progress_updated.connect(self.update_progress_bar)
        self.login_manager.finished.connect(self.login_finished)
        # Start the process
        self.login_manager.start()
    def update_progress_bar(self, completed, total):
        """Update the progress bar"""
        self.progress_bar.setValue(completed)
        if completed >= total:
            self.progress_bar.setVisible(False)
    def stop_login_process(self):
        """Stop the login process"""
        if self.login_manager and self.login_manager.running:
            self.login_manager.stop()
            self.log_message("Process stopped by user")
        self.login_finished()
    def login_finished(self):
        """Clean up after login process finishes"""
        self.start_btn.setEnabled(True)
        self.auto_login_btn.setEnabled(True)
        self.interact_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_account_btn.setEnabled(True)
        self.add_category_btn.setEnabled(True)
        self.delete_category_btn.setEnabled(True)
        self.select_account_btn.setEnabled(True)
        if hasattr(self, 'schedule_select_account_btn'):
            self.schedule_select_account_btn.setEnabled(True)
        if hasattr(self, 'info_select_account_btn'):
            self.info_select_account_btn.setEnabled(True)
        if hasattr(self, 'automation_select_account_btn'):
            self.automation_select_account_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Process completed")
        self.log_message("All accounts processed")
        self.load_accounts_to_table()
        self.update_dashboard_stats()
    def update_table_status(self, row, status):
        """Update status in table for specific row"""
        try:
            row_idx = int(row)
            item = QTableWidgetItem(status)
            if "Success" in status:
                item.setForeground(QColor("#4CAF50"))
                item.setText("✓ " + status)
            elif "Failed" in status or "Error" in status:
                item.setForeground(QColor("#E74C3C"))
                item.setText("✗ " + status)
            elif "Skipped" in status:
                item.setForeground(QColor("#F39C12"))
                item.setText("⚠️ " + status)
            else:
                item.setText("🔄 " + status)  # Running indicator
            self.table.setItem(row_idx, 5, item)
        except Exception as e:
            print(f"Error updating table status: {e}")
    def update_interaction_status(self, uid, action, status):
        """Log interaction status"""
        try:
            self.log_message(f"Account {uid} - {action}: {status}")
        except Exception as e:
            print(f"Error updating interaction status: {e}")
    # --- MODIFIED: New handler for account status updates ---
    def on_account_status_update(self, uid, status, increment_login_count, increment_task_count):
        """Handle account status updates from workers."""
        success = self.db_manager.update_account_status(uid, status, increment_login_count, increment_task_count)
        if not success:
            self.log_message(f"Failed to update status for UID: {uid}")
    # --- END MODIFIED ---
    # --- MODIFIED: Handler for task completed signal ---
    def on_task_completed(self, uid):
        """Handle task completed signal."""
        # The task count is already incremented in the worker via account_status_update.
        # We just need to refresh the UI.
        self.load_accounts_to_table()
        if hasattr(self, 'schedule_selection_table'):
            self.refresh_schedule_selection_table()
        if hasattr(self, 'info_selection_table'):
            self.refresh_info_selection_table()
        if hasattr(self, 'automation_selection_table'):
            self.refresh_automation_selection_table()
        self.log_message(f"Task completed for UID: {uid}")
    # --- END MODIFIED ---
    def update_system_monitor(self):
        """Update system monitor with current account count"""
        # --- MODIFIED: Get account count from DB ---
        count = len(self.db_manager.get_all_accounts())
        # --- END MODIFIED ---
        self.system_monitor.update_accounts_count(count)
    # --- NEW: Select All / Deselect All for any table ---
    def select_all_in_table(self, table):
        """Select all checkboxes in the given table."""
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_widget.setChecked(True)
        self.update_selection_counter(table)
    def deselect_all_in_table(self, table):
        """Deselect all checkboxes in the given table."""
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_widget.setChecked(False)
        self.update_selection_counter(table)
    def update_selection_counter(self, table, counter_label=None):
        """Update the counter label for the given table."""
        count = 0
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget and checkbox_widget.isChecked():
                count += 1
        if counter_label:
            counter_label.setText(f"Selected: {count}")
    # --- NEW: Placeholder for Account Info Tab Function ---
    # (Already implemented above in the enhanced profile upload section)
    # --- NEW: Placeholder for Schedule Tab Functions ---
    def start_scheduled_actions(self):
        """Start scheduled actions for selected accounts."""
        selected_accounts = self.get_selected_accounts(self.schedule_selection_table)
        if not selected_accounts:
            QMessageBox.warning(self, "No Accounts Selected", "Please select at least one account to schedule actions.")
            return
        actions = []
        if self.auto_view_feed_cb.isChecked():
            actions.append("View Feed")
        if self.auto_react_friends_cb.isChecked():
            actions.append("React to Friends' Posts")
        if self.auto_invite_friends_cb.isChecked():
            actions.append("Invite Friends to Group")
        if self.auto_share_wall_cb.isChecked():
            actions.append("Share to Wall")
        if self.auto_share_group_cb.isChecked():
            actions.append("Share to Group")
        if not actions:
            QMessageBox.warning(self, "No Actions Selected", "Please select at least one action to schedule.")
            return
        target_group = self.target_group_input.text().strip()
        self.schedule_log_output.append(f"[{time.strftime('%H:%M:%S')}] Starting scheduled actions for {len(selected_accounts)} accounts: {', '.join(actions)}")
        if target_group:
            self.schedule_log_output.append(f"[{time.strftime('%H:%M:%S')}] Target Group: {target_group}")
        # Disable buttons
        self.start_schedule_btn.setEnabled(False)
        self.stop_schedule_btn.setEnabled(True)
        self.schedule_select_account_btn.setEnabled(False)
        # Start the login process with schedule actions
        account_tuples = [(acc['uid'], acc['password'], acc['token'], acc['cookie']) for acc in selected_accounts]
        self.start_login_process(
            accounts=account_tuples,
            use_proxies=False,
            post_url=None,
            comment_text=None,
            actions=None,
            random_comments=None,
            react_type=None,
            target_group_url=target_group,
            schedule_actions=actions
        )
    def stop_scheduled_actions(self):
        """Stop scheduled actions."""
        self.stop_login_process()
        self.start_schedule_btn.setEnabled(True)
        self.stop_schedule_btn.setEnabled(False)
        self.schedule_select_account_btn.setEnabled(True)
        self.schedule_log_output.append(f"[{time.strftime('%H:%M:%S')}] Scheduled actions stopped.")
    def closeEvent(self, event):
        """Handle application close event to clean up resources."""
        if self.login_manager and self.login_manager.running:
            self.login_manager.stop()
        if hasattr(self, 'system_monitor'):
            self.system_monitor.stop_monitoring()
        # --- MODIFIED: Close database connection ---
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        # --- END MODIFIED ---
        event.accept()
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        print("QApplication created successfully.")
        try:
            window = MainWindow()
            print("MainWindow created successfully.")
            window.show()
            sys.exit(app.exec())
        except Exception as e:
            print(f"Error creating MainWindow: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    except Exception as e:
        print(f"Error creating QApplication: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)