from testr import Testr
from testr.exceptions import ElementNotFoundError
import sys
import os

automator = Testr()

# Get the executable name from the full path
app_path = "C:/Program Files (x86)/Ubisoft/Ubisoft Game Launcher/UbisoftConnect.exe"
app_name = os.path.basename(app_path)

try:
    (
        automator.chain()
            .app.launch_app(app_path, as_admin=True)
            .wait(30)
            .screen.find_text_position_and_click("Library", max_retries=3, retry_delay=2)
            .screen.find_text_position_and_click("Tom Clancy", max_retries=3, retry_delay=2)
            .screen.find_color_position_and_click("#006EF5", max_retries=3, retry_delay=2)
            # .screen.find_text_position_and_click("Play", max_retries=3, retry_delay=2)
            .wait(200)
            .screen.find_text_position_and_click("Operators", max_retries=3, retry_delay=2)
            .screen.find_text_position_and_click("Defenders", max_retries=3, retry_delay=2)

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