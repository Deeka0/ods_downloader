

import shlex
from time import sleep
from pathlib import Path
from random import uniform
from sys import exit, platform
from shutil import get_terminal_size
from os import system #, get_terminal_size
from subprocess import Popen, run, DEVNULL


if platform not in ("darwin", "linux", "ios", "android", "win32"):
    exit("OS configurations not available yet.")


# Sort shell arguments for subprocesses
shell_arg: bool = True if platform == "win32" else False

# Core paths
runtime_path: Path = Path(__file__).parent
parent_runtime_path: Path = runtime_path.parent
desktop_path: Path = Path("~/Desktop").expanduser()


# UTILITY FUNCTIONS

def clear() -> int:
    """
    Clears the screen using the subprocess module.
    """
    return run(args=["cls" if platform == "win32" else "clear"], shell=shell_arg)


def clear_by_OS() -> int:
    """
    Clears the screen using the os module.
    """
    return system(command="cls" if platform == "win32" else "clear")


def clean_up_driver_logs() -> None:
    """
    Clears the working directories of runtime generated 'driver.log' files.
    """
    paths = (runtime_path, Path.cwd())
    for path in paths:
        for file in path.iterdir():
            if file.name == "driver.log":
                file.unlink()


def cprint(text: str) -> None:
    """
    Prints the text to the horizontal centre of the screen.
    - text: Text to be printed.
    """
    # columns, lines = get_terminal_size()
    print(text.center(get_terminal_size().columns))


def sleepify(lower_bound: float, upper_bound: float) -> None:
    """
    Sleeps for a random period of time.
    - lower_bound: Minimum time to sleep.
    - Upper_bound: Maximum time to sleep.
    """
    sleep(uniform(lower_bound, upper_bound))


def run_in_terminal_tab(command: str, platform: str = platform, wait_timer: int = 2, 
                           is_windows_batch_file: bool = False, use_cmd: bool = False, 
                           ) -> int:
    """
    Runs a shell command in a seperate terminal tab.
    """
    match platform:
        
        # For Windows
        case "win32":
            # For batch files
            batch_flag = "@echo off, setlocal enableDelayedExpansion" if is_windows_batch_file else ""
            shell_flag = f'wt -w 0 nt {"cmd /k" if use_cmd else "powershell"} {command}'

            prompt_command = f'''
            {batch_flag}
            {shell_flag}
            timeout /t {wait_timer} /nobreak > nul'''
    
        # For macOS
        case "darwin":
            prompt_command = f'''
            osascript -e 'tell application "Terminal" to activate' \
            -e 'tell application "System Events" to tell process "Terminal" to keystroke "t" using command down' \
            -e 'tell application "Terminal" to do script "{command}" in selected tab of the front window'
            sleep {wait_timer}
            '''

        # For Linux
        case "linux":
            prompt_command = f'''
            #!/bin/bash
            gnome-terminal --tab-with-profile=auto --title="tab$i" -e "{command}"
            sleep {wait_timer}
            '''

    return system(prompt_command)


def win32_analyser(command: str) -> str:
    """
    Returns a valid subprocess runner command for Windows.
    - command: Command to process.
    """
    return 'powershell -command ' + '"&{' + command + '}"'


def win32_hider(path: Path | str, full_stealth: bool = False) -> None:
    """
    Recursively hides files and folders on windows.
    - path: File or folder path.
    - full_stealth: Enforces use of the system flag '+s'.
    """
    # if path.is_dir():
    #     run(args=shlex.split(f"attrib +h {'+s' if full_stealth else ''} /s /d '{path}\*'"), stderr=DEVNULL)
    
    run(args=shlex.split(f"attrib +h {'+s' if full_stealth else ''} '{path}'"), stderr=DEVNULL)


def downloader(destination_path: Path | str, download_url: str, custom_file_name: str = None, verify_cert: bool = True) -> bool:
    """
    Downloads whatever with curl.
    - destination_path: Path to store downloaded file.
    - download_url: File download url.
    - custom_file_name: Custom file name for downloaded file.
    - verify_cert: Flag for certificate verification.
    """
    # -k/--insecure
    # --cacert [file]
    temp_destination_path = f"'{destination_path}'" if platform == "win32" else destination_path

    if custom_file_name:
        # download_command = f"curl {'--insecure' if not verify_cert else ''} --output {custom_file_name} --create-dirs -O --output-dir {temp_destination_path} {download_url}"
        download_command = f"curl {'--insecure' if not verify_cert else ''} --output {custom_file_name} --output-dir {temp_destination_path} {download_url}"

        # Essential for renaming of failed downloads
        move_command = f"mv {destination_path.joinpath(custom_file_name)} {destination_path.joinpath(f'{custom_file_name}.failed')}"

    else:
        # download_command = f"curl {'--insecure' if not verify_cert else ''} --create-dirs -O --output-dir {temp_destination_path} {download_url}"
        download_command = f"curl {'--insecure' if not verify_cert else ''} -O --output-dir {temp_destination_path} {download_url}"

        # Essential for renaming of failed downloads
        file_name = download_url.split('/')[-1]
        move_command = f"mv {destination_path.joinpath(file_name)} {destination_path.joinpath(f'{file_name}.failed')}"

    # Launch the curler and get the job done
    try:
        with Popen(args=shlex.split(download_command), stderr=DEVNULL, shell=shell_arg) as curler:

            is_done = curler.poll()
            while is_done is None:
                sleep(1)
                is_done = curler.poll()
                
            return True
    except:
        # Rename failed downloads by appending a '.failed' suffix to their names
        if platform == "win32": move_command = win32_analyser(command=move_command)

        run(args=shlex.split(move_command), stderr=DEVNULL, shell=shell_arg)
        return False
    finally:
        curler.terminate()
        curler.wait()





# TO-DO
# 



# Done
# Use subprocess to run commands
# Type annotations


