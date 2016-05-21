#!/bin/bash
git pull origin master && pip install -r requirements.txt && python3 main.py && git add . && git commit -m "Update by cron" && git push origin master
