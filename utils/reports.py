import json
import csv
from datetime import datetime, timezone
import os

REPORT_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

def write_reports(changes):
    """
    Write JSON and CSV summary for today's changes. Returns JSON path.
    """
    if not changes:
        # write empty file
        filename = datetime.utcnow().strftime("%Y-%m-%d") + "-changes.json"
        path = os.path.join(REPORT_DIR, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([], fh, indent=2)
        return path

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = os.path.join(REPORT_DIR, f"{date_str}-changes.json")
    csv_path = os.path.join(REPORT_DIR, f"{date_str}-changes.csv")

    # JSON
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(changes, fh, default=str, indent=2)

    # CSV summary
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["detected_at", "book_id", "source_url", "change_type", "changed_fields"])
        for c in changes:
            writer.writerow([c.get("detected_at"), str(c.get("book_id")), c.get("source_url"), c.get("change_type"), json.dumps(c.get("changed_fields"))])

    return json_path
