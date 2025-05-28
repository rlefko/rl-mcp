#!/bin/bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips='*' --proxy-headers 2>&1 | tee -a /var/log/app.log
