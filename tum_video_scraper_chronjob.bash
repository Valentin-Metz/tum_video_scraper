#!/bin/bash

source ./venv/bin/activate
nice 15 python3 -m pip install --upgrade pip
nice 15 python3 -m pip install -r requirements.txt
nice 15 python3 main.py