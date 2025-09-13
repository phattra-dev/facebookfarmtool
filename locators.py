from selenium.webdriver.common.by import By

class FacebookLocators:
    """Centralized repository for Facebook web element locators."""

    # --- Login Page ---
    EMAIL_FIELD = (By.ID, "email")
    PASSWORD_FIELD = (By.ID, "pass")
    LOGIN_BUTTON = (By.NAME, "login")

    # --- Generic Logged-In Indicators ---
    LOGGED_IN_INDICATORS = [
        (By.XPATH, "//div[@aria-label='Account']"),
        (By.XPATH, "//span[contains(text(), 'Home')]"),
        (By.XPATH, "//a[@aria-label='Messenger']"),
        (By.XPATH, "//div[@id='userNav']"),
        (By.XPATH, "//span[contains(text(), 'Groups')]"),
        (By.XPATH, "//div[@role='navigation']//a[@href='/']"),
        (By.XPATH, "//div[@aria-label='Create post']"),
        (By.XPATH, "//div[@aria-label='What's on your mind?']"),
        (By.XPATH, "//div[@aria-label='Create a post']"),
        (By.XPATH, "//span[contains(text(), 'News Feed')]"),
        (By.XPATH, "//div[@role='banner']//a[@href='/']")
    ]

    # --- Post Interaction ---
    # Share Button
    SHARE_BUTTONS = [
        (By.XPATH, "//div[@aria-label='Send this to friends or post it on your Timeline.']"),
        (By.XPATH, "//div[@aria-label='Share']"),
        (By.XPATH, "//div[contains(@aria-label, 'Share')]//span[text()='Share']"),
        (By.XPATH, "//div[contains(@class, 'share_button')]//div[@role='button']"),
        (By.XPATH, "//div[@data-testid='UFI2ShareLink']"),
        (By.XPATH, "//div[contains(@class, 'reaction')]/following::div[contains(@aria-label, 'Share')][1]"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Send this to friends')]"),
        (By.XPATH, "//span[text()='Share']/ancestor::div[@role='button']")
    ]

    # Share Now Button
    SHARE_NOW_BUTTONS = [
        (By.XPATH, "//span[text()='Share Now' or text()='Share to News Feed']"),
        (By.XPATH, "//div[@aria-label='Share Now' or @aria-label='Share to News Feed']"),
        (By.XPATH, "//span[contains(text(), 'Share Now')]"),
        (By.XPATH, "//div[contains(@aria-label, 'Share Now')]"),
        (By.XPATH, "//div[@role='menuitem']//span[text()='Share Now']"),
        (By.XPATH, "//div[@role='menuitem']//div[@aria-label='Share Now']")
    ]

    # Comment Box
    COMMENT_BOXES = [
        (By.XPATH, "//div[contains(@aria-label, 'Write a comment')]"),
        (By.XPATH, "//div[contains(@aria-label, 'Write a comment')]//div[@role='textbox']"),
        (By.XPATH, "//div[contains(@class, 'commentable_item')]//div[contains(@role, 'textbox')]"),
        (By.XPATH, "//form[contains(@class, 'comment_form')]//div[contains(@role, 'textbox')]"),
        (By.XPATH, "//div[contains(@data-testid, 'ufi_comment_composer')]//div[contains(@role, 'textbox')]"),
        (By.XPATH, "//div[contains(@class, 'notranslate') and @role='textbox']"),
        (By.XPATH, "//textarea[contains(@aria-label, 'Write a comment')]"),
        (By.XPATH, "//div[@role='textbox' and @aria-label='Write a comment...']"),
        (By.XPATH, "//div[@contenteditable='true' and @role='textbox']")
    ]

    # Post Button (for comments)
    POST_BUTTONS = [
        (By.XPATH, "//div[@aria-label='Press Enter to post' or @aria-label='Comment']"),
        (By.XPATH, "//button[contains(@type, 'submit') and contains(@value, 'Post')]"),
        (By.XPATH, "//div[contains(text(), 'Comment') and @role='button']"),
        (By.XPATH, "//input[@value='Post' or @value='Comment']"),
        (By.XPATH, "//div[contains(@aria-label, 'Post')]"),
        (By.XPATH, "//div[@aria-label='Comment']"),
        (By.XPATH, "//div[@role='button' and contains(text(), 'Comment')]"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Comment')]")
    ]

    # Reaction Button (Main)
    REACTION_BUTTONS = [
        (By.XPATH, "//div[@aria-label='Like' or @aria-label='Like this post']"),
        (By.XPATH, "//div[contains(@aria-label, 'Like') and @role='button']"),
        (By.XPATH, "//div[@data-testid='ufi-inline-reaction']"),
        (By.XPATH, "//div[contains(@class, 'reaction')]"),
        (By.XPATH, "//div[contains(@aria-label, 'React')]"),
        (By.XPATH, "//span[text()='Like']/ancestor::div[@role='button']"),
        (By.XPATH, "//div[@aria-label='React' or @aria-label='Phản ứng']"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Like')]"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'React')]")
    ]

    # Specific Reactions
    REACTION_TYPES = {
        'like': [
            (By.XPATH, "//div[@aria-label='Like']"),
            (By.XPATH, "//div[@aria-label='Like' or @aria-label='Thích']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Like']")
        ],
        'love': [
            (By.XPATH, "//div[@aria-label='Love']"),
            (By.XPATH, "//div[@aria-label='Love' or @aria-label='Yêu thích']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Love']")
        ],
        'care': [
            (By.XPATH, "//div[@aria-label='Care']"),
            (By.XPATH, "//div[@aria-label='Care' or @aria-label='Thương thương']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Care']")
        ],
        'haha': [
            (By.XPATH, "//div[@aria-label='Haha']"),
            (By.XPATH, "//div[@aria-label='Haha']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Haha']")
        ],
        'wow': [
            (By.XPATH, "//div[@aria-label='Wow']"),
            (By.XPATH, "//div[@aria-label='Wow']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Wow']")
        ],
        'sad': [
            (By.XPATH, "//div[@aria-label='Sad']"),
            (By.XPATH, "//div[@aria-label='Sad' or @aria-label='Buồn']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Sad']")
        ],
        'angry': [
            (By.XPATH, "//div[@aria-label='Angry']"),
            (By.XPATH, "//div[@aria-label='Angry' or @aria-label='Phẫn nộ']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Angry']")
        ]
    }

    # Like Button (Specific)
    LIKE_BUTTONS = [
        (By.XPATH, "//div[@aria-label='Like' or @aria-label='Like this post']"),
        (By.XPATH, "//span[text()='Like' or text()='Like this post']"),
        (By.XPATH, "//a[contains(@aria-pressed, 'false') and contains(@role, 'button') and contains(@aria-label, 'Like')]"),
        (By.XPATH, "//div[contains(@aria-label, 'Like') and not(contains(@aria-pressed, 'true'))]"),
        (By.XPATH, "//div[contains(@data-testid, 'fb-ufi-likelink')]"),
        (By.XPATH, "//div[@aria-label='Like' or @aria-label='Thích']"),
        (By.XPATH, "//div[@role='button' and @aria-label='Like']"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Like')]")
    ]

    # Already Liked Indicators
    ALREADY_LIKED_INDICATORS = [
        (By.XPATH, "//div[@aria-label='Unlike' or @aria-label='Unlike this post']"),
        (By.XPATH, "//span[text()='Liked' or text()='Unlike']"),
        (By.XPATH, "//div[contains(@aria-label, 'Like') and contains(@aria-pressed, 'true')]"),
        (By.XPATH, "//div[@aria-label='Unlike' or @aria-label='Bỏ thích']"),
        (By.XPATH, "//div[@role='button' and @aria-label='Unlike']")
    ]

    # CAPTCHA Indicators
    CAPTCHA_INDICATORS = [
        (By.XPATH, "//div[contains(text(), 'security check')]"),
        (By.XPATH, "//div[contains(text(), 'CAPTCHA')]"),
        (By.XPATH, "//div[contains(text(), 'challenge')]"),
        (By.XPATH, "//div[contains(text(), 'verify')]"),
        (By.XPATH, "//iframe[contains(@src, 'captcha')]"),
        (By.XPATH, "//iframe[contains(@title, 'verification')]"),
        (By.XPATH, "//div[contains(@class, 'captcha')]"),
        (By.XPATH, "//div[contains(@class, 'challenge')]"),
        (By.XPATH, "//img[contains(@src, 'captcha')]"),
        (By.XPATH, "//button[contains(text(), 'Continue')]"),
        (By.XPATH, "//button[contains(text(), 'Submit')]"),
        (By.XPATH, "//button[contains(text(), 'Verify')]")
    ]