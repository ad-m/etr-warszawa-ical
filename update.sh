#!/bin/sh
set -eux
pip install -r requirements.txt
python3 main.py
git add .
git commit -m "Update by cron" || echo 'Nothing to commit'
