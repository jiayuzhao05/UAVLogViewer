#!/usr/bin/env python3
"""
Download a sample MAVLink flight log (.bin or .tlog) for testing the chatbot.
Run from project root: python examples/download_sample_bin.py
"""
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)

# Working: vtol.tlog from ArduPilot UAVLogViewer (same sample as plot.ardupilot.org)
VTOL_TLOG_URL = "https://raw.githubusercontent.com/ArduPilot/UAVLogViewer/master/src/assets/vtol.tlog"

# ArduPilot autotest .BIN URLs (may return 404 when test run expires)
AUTOTEST_BIN_URLS = [
    "https://autotest.ardupilot.org/ArduSub-TestLogDownloadLogRestart-00000008.BIN",
    "https://autotest.ardupilot.org/Rover-Scripting-00000005.BIN",
    "https://autotest.ardupilot.org/Copter-common-00000001.BIN",
]

# Reliable .bin from ArduPilot_binParser (GitHub, ~12MB)
BIN_GITHUB_URL = "https://raw.githubusercontent.com/Crazy-Al/ArduPilot_binParser/main/Examples/ExampleBinFiles/00000009.BIN"

OUTPUT_DIR = Path(__file__).parent


def download_sample(prefer_bin=False):
    """Download a sample flight log. Set prefer_bin=True to get .bin first."""
    # 1. Try .BIN first if requested
    if prefer_bin:
        # Try reliable GitHub .bin first
        try:
            print(f"Downloading .bin: {BIN_GITHUB_URL}")
            r = requests.get(BIN_GITHUB_URL, timeout=60)
            if r.status_code == 200 and len(r.content) > 100:
                out = OUTPUT_DIR / "sample_flight.bin"
                out.write_bytes(r.content)
                print(f"✓ Downloaded to {out}")
                print(f"  Size: {len(r.content):,} bytes")
                return True
        except Exception as e:
            print(f"  Failed: {e}")
        for url in AUTOTEST_BIN_URLS:
            try:
                print(f"Downloading .bin: {url}")
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 100:
                    out = OUTPUT_DIR / "sample_flight.bin"
                    out.write_bytes(r.content)
                    print(f"✓ Downloaded to {out}")
                    print(f"  Size: {len(r.content):,} bytes")
                    return True
            except Exception as e:
                print(f"  Failed: {e}")

    # 2. Try vtol.tlog (reliable fallback)
    try:
        print(f"Downloading: {VTOL_TLOG_URL}")
        r = requests.get(VTOL_TLOG_URL, timeout=30)
        if r.status_code == 200 and len(r.content) > 100:
            out = OUTPUT_DIR / "sample_flight.tlog"
            out.write_bytes(r.content)
            print(f"✓ Downloaded to {out}")
            print(f"  Size: {len(r.content):,} bytes")
            return True
    except Exception as e:
        print(f"  Failed: {e}")

    # 3. Try autotest .BIN URLs (if not tried yet)
    if not prefer_bin:
        for url in AUTOTEST_BIN_URLS:
            try:
                print(f"Trying: {url}")
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 100:
                    out = OUTPUT_DIR / "sample_flight.bin"
                    out.write_bytes(r.content)
                    print(f"✓ Downloaded to {out}")
                    return True
            except Exception as e:
                print(f"  Failed: {e}")

    print("\n✗ All download attempts failed.")
    print("\nAlternative: Use your own .bin/.tlog from Mission Planner or MAVProxy")
    return False


if __name__ == "__main__":
    prefer_bin = "--bin" in sys.argv
    success = download_sample(prefer_bin=prefer_bin)
    sys.exit(0 if success else 1)
