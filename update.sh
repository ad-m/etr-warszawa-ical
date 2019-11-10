#!/bin/bash
set -e
git pull origin master 2>/dev/null
pip install -r requirements.txt
python3 main.py
git add .
git commit -m "Update by cron" || echo 'Nothing to commit'
git push origin master 2>/dev/null
