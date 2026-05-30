#!/bin/bash
# Run Pixel Pet from source.
cd "$(dirname "$0")" || exit 1
exec python3.11 pet.py
