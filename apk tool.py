import os
import sys
import subprocess
import requests
import zipfile
import shutil
import curses  # Now works on Windows with windows-curses
import time

# Function to install dependencies automatically
def install_dependencies():
    dependencies = ["requests", "windows-curses"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"{dep} is already installed.")
        except ImportError:
            print(f"{dep} is missing. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Function to initialize curses
def init_curses():
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Selected option
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Unselected option
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Border color
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Loading bar color
        return stdscr
    except Exception as e:
        print(f"Failed to initialize curses: {e}")
        sys.exit(1)

# Function to clean up curses
def cleanup_curses(stdscr):
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

# Function to display a bordered menu with arrow key navigation
def display_menu(stdscr, title, options, selected_index):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Draw border
    stdscr.attron(curses.color_pair(3))
    stdscr.border()
    stdscr.attroff(curses.color_pair(3))

    # Add title with massive borders
    title_border = "╔" + "═" * (len(title) + 4) + "╗"
    title_text = f"║  {title}  ║"
    title_border_bottom = "╚" + "═" * (len(title) + 4) + "╝"

    stdscr.addstr(2, (width - len(title_border)) // 2, title_border, curses.color_pair(3))
    stdscr.addstr(3, (width - len(title_text)) // 2, title_text, curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(4, (width - len(title_border_bottom)) // 2, title_border_bottom, curses.color_pair(3))

    # Add options
    for i, option in enumerate(options):
        x = (width - len(option)) // 2
        y = 6 + i * 2  # Add more spacing between options
        if i == selected_index:
            stdscr.addstr(y, x, f"> {option} <", curses.color_pair(1) | curses.A_BOLD)
        else:
            stdscr.addstr(y, x, f"  {option}  ", curses.color_pair(2))
    stdscr.refresh()

# Function to display a game-like loading bar
def display_loading_bar(stdscr, progress):
    height, width = stdscr.getmaxyx()
    bar_width = 50
    bar_x = (width - bar_width) // 2
    bar_y = height // 2

    # Draw the loading bar
    stdscr.addstr(bar_y - 1, bar_x, "[" + " " * bar_width + "]", curses.color_pair(4))
    stdscr.addstr(bar_y - 1, bar_x + 1, "=" * int(progress * bar_width), curses.color_pair(4))
    stdscr.refresh()

# Function to download a file with a real progress bar
def download_file(stdscr, url, output_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 KB
    downloaded_size = 0

    with open(output_path, "wb") as f:
        for data in response.iter_content(block_size):
            f.write(data)
            downloaded_size += len(data)
            progress = downloaded_size / total_size
            display_loading_bar(stdscr, progress)
            stdscr.refresh()

# Function to install ADB
def install_adb(stdscr):
    adb_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    zip_path = os.path.join(os.getcwd(), "platform-tools.zip")
    extract_path = os.path.join(os.getcwd(), "platform-tools")

    # Check if ADB already exists
    if os.path.exists(extract_path):
        stdscr.clear()
        stdscr.addstr(0, 0, "ADB is already installed.", curses.color_pair(4) | curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()
        return

    # Download ADB
    stdscr.clear()
    stdscr.addstr(0, 0, "Downloading ADB...", curses.A_BOLD)
    stdscr.refresh()
    download_file(stdscr, adb_url, zip_path)

    # Extract ADB
    stdscr.clear()
    stdscr.addstr(0, 0, "Extracting ADB...", curses.A_BOLD)
    stdscr.refresh()
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # Move contents of nested platform-tools folder
    nested_path = os.path.join(extract_path, "platform-tools")
    if os.path.exists(nested_path):
        for item in os.listdir(nested_path):
            shutil.move(os.path.join(nested_path, item), os.path.join(extract_path, item))
        os.rmdir(nested_path)  # Remove the now-empty nested folder

    # Clean up
    os.remove(zip_path)
    stdscr.clear()
    stdscr.addstr(0, 0, "ADB installed successfully!", curses.color_pair(4) | curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

# Function to validate GitHub URL
def is_valid_github_url(url):
    return url.startswith("https://github.com/") and url.endswith(".apk")

# Function to install APK to a connected Android device
def install_apk(stdscr, apk_path):
    adb_path = os.path.join(os.getcwd(), "platform-tools", "adb.exe")
    if not os.path.exists(adb_path):
        stdscr.clear()
        stdscr.addstr(0, 0, "ADB not found. Please install ADB first.", curses.color_pair(2))
        stdscr.refresh()
        stdscr.getch()
        return False

    # Check if a device is connected
    result = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
    if "device" not in result.stdout:
        stdscr.clear()
        stdscr.addstr(0, 0, "No device connected. Please connect an Android device.", curses.color_pair(2))
        stdscr.refresh()
        stdscr.getch()
        return False

    # Install APK
    stdscr.clear()
    stdscr.addstr(0, 0, "Installing APK...", curses.A_BOLD)
    stdscr.refresh()
    result = subprocess.run([adb_path, "install", apk_path], capture_output=True, text=True)
    if "Success" in result.stdout:
        stdscr.clear()
        stdscr.addstr(0, 0, "APK installed successfully!", curses.color_pair(4) | curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()
        return True
    else:
        stdscr.clear()
        stdscr.addstr(0, 0, "Failed to install APK.", curses.color_pair(2))
        stdscr.refresh()
        stdscr.getch()
        return False

# Function to handle custom text input
def get_user_input(stdscr, prompt, y, x, max_length):
    stdscr.addstr(y, x, prompt, curses.color_pair(2))
    stdscr.refresh()
    input_text = ""
    while True:
        key = stdscr.getch()
        if key == curses.KEY_BACKSPACE or key == 127:  # Handle backspace
            if len(input_text) > 0:
                input_text = input_text[:-1]
                stdscr.addstr(y, x + len(prompt) + len(input_text), " ")  # Clear the last character
        elif key == ord("\n"):  # Enter key
            break
        elif len(input_text) < max_length and key >= 32 and key <= 126:  # Printable characters
            input_text += chr(key)
        stdscr.addstr(y, x + len(prompt), input_text.ljust(max_length))  # Update the input field
        stdscr.refresh()
    return input_text

# Function to display the GitHub URL entry page
def display_url_entry(stdscr):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Add title with massive borders
    title = "Enter GitHub Release URL"
    title_border = "╔" + "═" * (len(title) + 4) + "╗"
    title_text = f"║  {title}  ║"
    title_border_bottom = "╚" + "═" * (len(title) + 4) + "╝"

    stdscr.addstr(2, (width - len(title_border)) // 2, title_border, curses.color_pair(3))
    stdscr.addstr(3, (width - len(title_text)) // 2, title_text, curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(4, (width - len(title_border_bottom)) // 2, title_border_bottom, curses.color_pair(3))

    # Add input prompt
    prompt = "Enter URL: "
    url = get_user_input(stdscr, prompt, 6, (width - len(prompt) - 50) // 2, 50)
    return url

# Function to find Package-Bundle files
def find_package_bundles():
    bundle_files = []
    for file in os.listdir():
        if "Package-Bundle" in file and file.endswith(".txt"):
            bundle_files.append(file)
    return bundle_files

# Function to process a Package-Bundle file
def process_package_bundle(stdscr, bundle_file):
    with open(bundle_file, "r") as f:
        urls = f.read().splitlines()

    for url in urls:
        # Fetch the latest release from the repository
        repo_api_url = f"https://api.github.com/repos/{url.split('/')[3]}/{url.split('/')[4]}/releases/latest"
        response = requests.get(repo_api_url)
        if response.status_code != 200:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Failed to fetch release for {url}. Skipping...", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()
            continue

        release_data = response.json()
        apk_asset = None
        for asset in release_data.get("assets", []):
            if asset["name"].endswith(".apk"):
                apk_asset = asset
                break

        if not apk_asset:
            stdscr.clear()
            stdscr.addstr(0, 0, f"No APK found in the latest release of {url}. Skipping...", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()
            continue

        # Download the APK
        apk_folder = os.path.join(os.getcwd(), "apk_setup_apks")
        os.makedirs(apk_folder, exist_ok=True)
        apk_path = os.path.join(apk_folder, apk_asset["name"])

        stdscr.clear()
        stdscr.addstr(0, 0, f"Downloading {apk_asset['name']}...", curses.A_BOLD)
        stdscr.refresh()
        download_file(stdscr, apk_asset["browser_download_url"], apk_path)

        # Install the APK
        if install_apk(stdscr, apk_path):
            stdscr.clear()
            stdscr.addstr(0, 0, f"Successfully installed {apk_asset['name']}!", curses.color_pair(4) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()
        else:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Failed to install {apk_asset['name']}.", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()

# Function to display the bundle selection screen
def display_bundle_selection(stdscr, bundles):
    selected_index = 0
    while True:
        display_menu(stdscr, "Select a Package-Bundle", bundles, selected_index)
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_index = (selected_index - 1) % len(bundles)
        elif key == curses.KEY_DOWN:
            selected_index = (selected_index + 1) % len(bundles)
        elif key == ord("\n"):  # Enter key
            return bundles[selected_index]
        elif key == 27:  # Escape key
            return None

# Main function
def main(stdscr):
    # Ask if the user wants to install ADB
    options = ["Yes", "No"]
    selected_index = 0
    while True:
        display_menu(stdscr, "Do you want to install ADB?\n(won't be deleted after!!)", options, selected_index)
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_index = (selected_index - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected_index = (selected_index + 1) % len(options)
        elif key == ord("\n"):  # Enter key
            if selected_index == 0:  # Yes
                install_adb(stdscr)
            break

    # Main loop for APK setup
    while True:
        # Choose installation method
        methods = ["Github URL", "Package"]
        selected_index = 0
        while True:
            display_menu(stdscr, "Choose Installation Method", methods, selected_index)
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_index = (selected_index - 1) % len(methods)
            elif key == curses.KEY_DOWN:
                selected_index = (selected_index + 1) % len(methods)
            elif key == ord("\n"):  # Enter key
                if selected_index == 0:  # Github URL
                    url = display_url_entry(stdscr)

                    # Validate GitHub URL
                    if not is_valid_github_url(url):
                        stdscr.clear()
                        stdscr.addstr(0, 0, "Invalid GitHub URL. Please try again.", curses.color_pair(2))
                        stdscr.refresh()
                        stdscr.getch()
                        continue

                    # Download APK
                    apk_folder = os.path.join(os.getcwd(), "apk_setup_apks")
                    os.makedirs(apk_folder, exist_ok=True)
                    apk_path = os.path.join(apk_folder, os.path.basename(url))

                    stdscr.clear()
                    stdscr.addstr(0, 0, "Downloading...", curses.A_BOLD)
                    stdscr.refresh()
                    download_file(stdscr, url, apk_path)

                    # Ask to install or cancel
                    options = ["Install", "Cancel"]
                    selected_index = 0
                    while True:
                        display_menu(stdscr, "Successfully Downloaded!", options, selected_index)
                        key = stdscr.getch()
                        if key == curses.KEY_UP:
                            selected_index = (selected_index - 1) % len(options)
                        elif key == curses.KEY_DOWN:
                            selected_index = (selected_index + 1) % len(options)
                        elif key == ord("\n"):  # Enter key
                            if selected_index == 0:  # Install
                                if install_apk(stdscr, apk_path):
                                    break
                            else:  # Cancel
                                os.remove(apk_path)
                                break
                else:  # Package
                    bundle_files = find_package_bundles()
                    if not bundle_files:
                        stdscr.clear()
                        stdscr.addstr(0, 0, "No Package-Bundle files found.", curses.color_pair(2))
                        stdscr.refresh()
                        stdscr.getch()
                        continue

                    # Select a bundle
                    selected_bundle = display_bundle_selection(stdscr, bundle_files)
                    if not selected_bundle:
                        continue

                    # Process the selected bundle
                    process_package_bundle(stdscr, selected_bundle)

                    stdscr.clear()
                    stdscr.addstr(0, 0, "installed or nah, went through", curses.color_pair(4) | curses.A_BOLD)
                    stdscr.refresh()
                    stdscr.getch()
                break

# Run the program
if __name__ == "__main__":
    # Install dependencies immediately
    install_dependencies()

    # Initialize curses and run the main function
    stdscr = init_curses()
    try:
        main(stdscr)
    finally:
        cleanup_curses(stdscr)