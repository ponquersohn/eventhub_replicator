#!/bin/bash
python3.10 -m venv .venv 
source .venv/bin/activate 

find . -name requirements.txt -exec pip install -r {} \;
