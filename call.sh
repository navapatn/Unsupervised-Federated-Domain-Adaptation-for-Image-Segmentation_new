#!/usr/bin/env bash

mkdir -p Logs
python3 -u main.py -source "08" -target "01" -alpha 1e-6 -jdot "True" -rev 0 > Logs/output_0.log
