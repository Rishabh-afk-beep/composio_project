"""
Export data files to frontend/data/ for the static case study page.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
FRONTEND_DATA = os.path.join(ROOT, "frontend", "data")


def main():
    os.makedirs(FRONTEND_DATA, exist_ok=True)

    for fname in ["results.json", "summary.json", "verification.json", "apps.json"]:
        src = os.path.join(DATA_DIR, fname)
        dst = os.path.join(FRONTEND_DATA, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  OK Copied {fname}")
        else:
            print(f"  SKIP Skipped {fname} (not found)")

    print(f"\nFrontend data exported to {FRONTEND_DATA}")


if __name__ == "__main__":
    main()
