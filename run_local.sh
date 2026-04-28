#!/usr/bin/env sh
set -eu

python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
