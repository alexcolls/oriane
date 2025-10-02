#!/usr/bin/env python3
"""
test.py

Simple smoke tests for your Python Lambda scene‐based frame extractor.
Make sure you’ve set your .env (or real env vars) before running:
  export $(grep -v '^#' .env | xargs)

Usage:
  python3 test.py
"""

import os
import json
from lambda_function import lambda_handler

def test_bulk_extraction():
    # List of known shortcodes for bulk test
    codes = [
        "DE2sdOOOx_R",
        "DE2tzvUyook",
        "DE4Td6OSRQV",
        "DE4VHQovJy1",
        "DE4Y8DgJFFV",
    ]
    records = [
        {
            "body": json.dumps({
                "code": code,
                "platform": "instagram"
            })
        }
        for code in codes
    ]
    event = {"Records": records}
    print("Running bulk extraction test...")
    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2))


def test_single_extraction():
    # Single‐video test
    record = {
        "body": json.dumps({
            "code": "DIB0wE1SHVa",
            "platform": "instagram"
        })
    }
    event = {"Records": [record]}
    print("Running single extraction test...")
    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Clear any temp dirs from previous runs
    os.environ.setdefault("DEBUG", "true")
    test_bulk_extraction()
    print("\n" + "="*60 + "\n")
    test_single_extraction()
