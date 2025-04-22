#!/usr/bin/env bash

# Render上で使われるスクリプト
apt-get update && apt-get install -y ffmpeg
pip install -r requirements.txt