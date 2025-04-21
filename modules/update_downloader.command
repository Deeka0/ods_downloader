#!/bin/bash

clear

target_file="ods_downloader.py"
runtime_path="$(dirname $0)"

cd $runtime_path

echo "Attempting to upload $target_file to the server. Authenticate to continue:"
echo

scp -i ~/Documents/Dev/Python/completed/utils/deeka-key $target_file deeka@34.69.64.5:./production/downloader/

echo
echo "Done!"


# osascript -e "do shell script \"osascript -e \\\"tell application \\\\\\\"Terminal\\\\\\\" to quit\\\" &> /dev/null &\""; exit

# exit
# osascript -e 'tell application "Terminal" to quit'
# osascript -e "tell application \"System Events\" to keystroke \"w\" using command down"
# osascript -e "tell application \"System Events\" to keystroke \"q\" using command down"

