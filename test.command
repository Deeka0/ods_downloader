#!/bin/bash

clear

target_files="*.py"
runtime_path="$(dirname $0)"

cd $runtime_path

echo "Attempting to upload $target_file to the server. Authenticate to continue:"
echo

scp $target_files monarch@198.144.183.148:./production/fbninja/modules/

echo
echo "Done!"


# osascript -e "do shell script \"osascript -e \\\"tell application \\\\\\\"Terminal\\\\\\\" to quit\\\" &> /dev/null &\""; exit

exit
# osascript -e 'tell application "Terminal" to quit'
# osascript -e "tell application \"System Events\" to keystroke \"w\" using command down"
# osascript -e "tell application \"System Events\" to keystroke \"q\" using command down"

