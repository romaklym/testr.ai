from testr import Testr
from testr.exceptions import ElementNotFoundError
import sys
import os

automator = Testr()

# Get the executable name from the full path
# app_path = "C:/Program Files (x86)/Ubisoft/Ubisoft Game Launcher/UbisoftConnect.exe"
app_name = "chrome.exe"

try:
    (
        automator.chain()
            .app.launch_app(app_name, as_admin=False)
            .wait(5)
            .screen.find_text_position_and_click("Search", max_retries=3, retry_delay=2)
            .input.type("facebook.com")
            .input.press("enter")
            .screen.find_template_position("x.png", max_retries=3, retry_delay=2)
            .wait(5)

    )
except ElementNotFoundError as e:
    print(f"\nError: {str(e)}")
    print("Script execution stopped due to element not being found")
    automator.app.close_app(app_name)  # Clean up by closing the app
    sys.exit(1)  # Exit with error code
except Exception as e:
    print(f"\nUnexpected error: {str(e)}")
    automator.app.close_app(app_name)  # Clean up by closing the app
    sys.exit(1)  # Exit with error code
finally:
    # Make sure the app is closed even if script succeeds
    automator.app.close_app(app_name)