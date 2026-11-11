"""Start the Plant Taxonomy Database web app on http://127.0.0.1:8113 (local only).

python run_web.py                 # the committed ITIS subset (data/pinales_itis.db)
python run_web.py --db my.db      # any database built by the desktop app, demo.py or populate_database.py
"""
import argparse
import os

import uvicorn

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", help="taxonomy database to browse (default: data/pinales_itis.db)")
    ap.add_argument("--port", type=int, default=8113)
    a = ap.parse_args()
    if a.db:
        os.environ["PLANT_TAXONOMY_DB"] = os.path.abspath(a.db)
    print(f"Plant Taxonomy Database: http://127.0.0.1:{a.port}")
    uvicorn.run("web.app:app", host="127.0.0.1", port=a.port)
