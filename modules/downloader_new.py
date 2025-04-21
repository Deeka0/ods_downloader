

# CUSTOM MODULES
from base import clear
from automateLite import EC, By, generate_puppies, initialize_chrome_session, downloader


# ### REMOVE ###
# from sys import path as exporter
# exporter.append("/Users/dark/Documents/Dev/Python/completed")
##
# from utils.modules.base import clear
# from utils.modules.automateLite import (EC, By, generate_puppies, 
#                                         initialize_chrome_session, downloader)
# from traceback import print_exc
# ### REMOVE ###

from time import sleep
from pathlib import Path
from sys import exit, platform
from argparse import ArgumentParser


parser = ArgumentParser(
    prog="Predespacho Daemon",
    description="Fetches files form the CND server.",
    epilog="Let's demonize CNDz."
)

parser.add_argument("-p", "--port", type=int, default=9001)
parser.add_argument("-b", "--binary", type=str, default="default")
parser.add_argument("-m", "--mode", type=str, default="debug")
args = parser.parse_args()

if args.binary not in ("default", "undetected"):
    exit(f"Invalid binary '{args.binary}'.")

if args.mode not in ("debug", "release"):
    exit(f"Invalid mode '{args.mode}'.")


def clean_up():
    """
    Removes old failed downloads and backs up completed downloads.
    """
    for file in temp_folder_path.iterdir():
        if file.suffix not in (".xlsx", ".xls"):
            file.unlink()
        else:
            file.rename(target=backup_folder_path.joinpath(file.name))


def handler(file_name: str, file_url: str) -> None:
    """
    Downloads new predespacho documents.
    """
    try:
        driver.get(file_url)
        wait.until(EC.title_is("Listado website"))
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="t-fht-wrapper"]'))) # Table wrapper
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="stickyTableHeader_1"]'))) # Table head
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="t-fht-tbody"]'))) # Table body

        all_table_rows = driver.find_element(By.XPATH, '//div[@class="t-fht-tbody"]').find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        
        if len(all_table_rows) < 2:
              return

        top_most_row = all_table_rows[1]

        document_data = top_most_row.find_elements(By.TAG_NAME, "td")
        document_name = document_data[0].text.strip()
        formatted_name = document_name.replace("/", "").replace(" ", "_") + ".xlsx"
        document_download_url = document_data[1].find_element(By.TAG_NAME, "a").get_attribute("href")

        print(f"\nDownloading {formatted_name}, please wait...")
        is_downloaded = downloader(destination_path=temp_folder_path, download_url=document_download_url, custom_file_name=formatted_name)
        if not is_downloaded:
            print(f"{file_name} failed to download.")
        else:
            print(f"{formatted_name} successfully downloaded.")
    except:
        print(f"\n{file_name} failed to download.")



if __name__ == "__main__":

    clear()

    # Core paths
    runtime_path: Path = Path(__file__).parent
    parent_runtime_path: Path = runtime_path.parent
    desktop_path: Path = Path("~/Desktop").expanduser()

    # Hidden runtime files
    runtime_folder: Path = parent_runtime_path.joinpath(".runtime")

    # User files
    user_folder: Path = parent_runtime_path.joinpath("user")
    backup_folder_path: Path = user_folder.joinpath("backup")
    temp_folder_path: Path = user_folder.joinpath("temp")

    # Unify chrome binaries
    match args.binary:
        case "default":
            binary_executable_path: Path = runtime_folder.joinpath("chromedriver.exe" if platform == "win32" else "chromedriver")
        case "undetected":
            binary_executable_path: Path = runtime_folder.joinpath("undetected_chromedriver.exe" if platform == "win32" else "undetected_chromedriver")

    # Sort runtime modes
    is_debug: bool = True if args.mode == "debug" else False

    # Check for backup folder
    if not backup_folder_path.is_dir():
        backup_folder_path.mkdir(parents=True, exist_ok=True)

    # Check for temp folder
    if not temp_folder_path.is_dir():
        temp_folder_path.mkdir(parents=True, exist_ok=True)

    urlF = {
        # "url" : "https://otr.ods.org.hn:3200/odsprd/f?p=110:4:::::p4_id:4",
        "url" : "https://appcnd.enee.hn:3200/odsprd/f?p=110:4:::::p4_id:4",
        "name" : "Predespacho Final",
    }

    urlS = {
        # "url" : "https://otr.ods.org.hn:3200/odsprd/f?p=110:4:::::p4_id:5",
        "url" : "https://appcnd.enee.hn:3200/odsprd/f?p=110:4:::::p4_id:5",
        "name" : "Predespacho Semanal",
    }

    # Launch the browser and get the job done
    new_chrome = initialize_chrome_session(port=args.port, headless=True)
    if not new_chrome:
        exit()

    try:
        driver, wait, action = generate_puppies(
            port=args.port, 
            binary_executable_path=binary_executable_path, 
            debug_mode=is_debug, 
            load_images=False
            )
    except:
        new_chrome.terminate()
        new_chrome.wait()
        exit()

    try:
        clean_up()
        for provider in (urlF, urlS):

            try:
                handler(file_name=provider["name"], file_url=provider["url"])
            except KeyboardInterrupt:
                print("\nInterrupted by user!")
            finally:
                sleep(3)
                continue
    finally:
        driver.quit()
        new_chrome.terminate()
        new_chrome.wait()
        exit("Exiting.")




