#!/bin/sh

# from https://github.com/chipsenkbeil/distant.nvim/blob/1d798b3746709ee5b1a2209d63248800cea82f09/lua/distant/lib.lua#L54-L59
if command -v curl > /dev/null 2>&1; then
    GET_CMD='curl -fL'
elif command -v wget > /dev/null 2>&1; then
    GET_CMD='wget -q -O -'
elif command -v fetch > /dev/null 2>&1; then
    GET_CMD='fetch -q -o -'
fi

if [ -z "$GET_CMD" ]; then
    echo "No external command is available. Please install curl, wget, or fetch!"
    exit 1
fi

for file in "requirements.txt" "send_mail.py"; do
    eval "$GET_CMD https://raw.githubusercontent.com/lytex/mail/master/$file" > "$file"
done

if ! command -v python3 > /dev/null 2>&1; then
    echo "python3 required to run the script"
    exit 1
fi

python3 -m pip install -r requirements.txt



