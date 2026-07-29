#!/bin/zsh
cd "$(dirname "$0")" || exit 1
python3 -m pip install -r requirements.txt
pyinstaller --clean --noconfirm PrismStudio.spec
