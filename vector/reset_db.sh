#!/bin/bash

cd /app/mimiciv/
rm -f mimiciv.db
python3 import.py
sqlite3 mimiciv.db < mimiciv_add_patient_info.sql
sqlite3 mimiciv.db < mimiciv_update_icd_codes.sql
