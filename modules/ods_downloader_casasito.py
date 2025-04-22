"""Module that downloads reports from ODS (HN) website"""

import shlex
from pathlib import Path
from sys import exit, platform
from time import perf_counter, sleep
from subprocess import Popen, run, DEVNULL

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except (ImportError, ModuleNotFoundError):
    print("\nModules are not installed!")
    exit("Run 'pip install requirements.txt' in the terminal to fix errors.")


def clean_up():
    """
    Removes old failed downloads and backs up completed downloads.
    """
    for file in runtime_path.iterdir():
        file_name = file.name
        if file.suffix == ".failed":
            file.unlink()
            print(f"Removed: {file_name}")
        elif file.suffix in (".xlsx", ".xls"):
            file.rename(target=backup_folder_path.joinpath(file_name))
            print(f"Backed up: {file_name}")


def ods_downloader(file_name: str, file_url: str) -> None:
    """
    Downloads new predespacho documents.
    """
    try:
        tic_dl = perf_counter()
        driver.get(file_url)
        wait.until(EC.title_is("Listado website"))
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="t-fht-wrapper"]'))) # Table wrapper
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="stickyTableHeader_1"]'))) # Table head
        wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="t-fht-tbody"]'))) # Table body
        print(f"URL load time: {int(perf_counter() - tic_dl)} seconds")

        all_table_rows = driver.find_element(By.XPATH, '//div[@class="t-fht-tbody"]').find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        
        if len(all_table_rows) < 2:
            return

        top_most_row = all_table_rows[1]

        document_data = top_most_row.find_elements(By.TAG_NAME, "td")
        document_name = document_data[0].text.strip()
        formatted_name = document_name.replace("/", "").replace(" ", "_") + ".xlsx"
        document_download_url = document_data[1].find_element(By.TAG_NAME, "a").get_attribute("href")

        print(f"\nDownloading {formatted_name}, please wait...")

        temp_destination_path = f"'{runtime_path}'" if platform == "win32" else runtime_path
        download_command = f"curl --insecure --output {formatted_name} --output-dir {temp_destination_path} {document_download_url}"

        # Launch the curler and get the job done
        try:
            with Popen(args=shlex.split(download_command), stderr=DEVNULL, shell=True if platform == "win32" else False) as curler:

                is_done = curler.poll()
                while is_done is None:
                    sleep(1)
                    is_done = curler.poll()

                print(f"{formatted_name} successfully downloaded.")
        except:
            move_command = f"mv {runtime_path.joinpath(formatted_name)} {runtime_path.joinpath(f'{formatted_name}.failed')}"

            # Rename failed downloads by appending a '.failed' suffix to their names
            if platform == "win32": move_command = 'powershell -command ' + '"&{' + move_command + '}"'

            run(args=shlex.split(move_command), stderr=DEVNULL, shell=True if platform == "win32" else False)
            print(f"{file_name} failed to download.")
        finally:
            curler.terminate()
            curler.wait()
    except:
        print(f"\n{file_name} failed to download.")



if __name__ == "__main__":

    runtime_path: Path = Path(__file__).parent
    backup_folder_path = runtime_path.joinpath("backup")

    # Check for backup folder folder
    if not backup_folder_path.is_dir():
        backup_folder_path.mkdir(parents=True, exist_ok=True)

    tic = perf_counter()
    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, timeout=30)
    print(f"Browser opening time: {int(perf_counter() - tic)} seconds")

    urlF = {
        "url" : "https://appcnd.enee.hn:3200/odsprd/f?p=110:4:::::p4_id:4",
        "name" : "Predespacho Final",
    }

    urlS = {
        "url" : "https://appcnd.enee.hn:3200/odsprd/f?p=110:4:::::p4_id:5",
        "name" : "Predespacho Semanal",
    }

    try:
        clean_up()
        for i in (urlF, urlS):
            try:
                tic_i = perf_counter()
                ods_downloader(file_name=i["name"], file_url=i["url"])
                print(f"Runtime for {i['name']}: {int(perf_counter() - tic_i)} seconds")
            except KeyboardInterrupt:
                print("\nInterrupted by user!")
            finally:
                sleep(1)
                continue
    finally:
        driver.quit()
        exit("Exiting.")


