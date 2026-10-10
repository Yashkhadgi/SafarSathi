import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "knowledge_base"
REQUIRED_FIELDS = (
    "id",
    "place",
    "state",
    "category",
    "text",
    "source_name",
    "source_url",
    "last_verified",
    "language",
    "tags",
)


def load_records(folder):
    records = []
    errors = []
    folder = Path(folder)
    if not folder.is_dir():
        return records, [f"KB folder does not exist: {folder}"]
    files = sorted(folder.glob("*.json"))
    if not files:
        return records, [f"No JSON files found in {folder}"]
    for path in files:
        try:
            with path.open(encoding="utf-8") as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: cannot read JSON: {exc}")
            continue
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            errors.append(f"{path.name}: top-level JSON must be an array or record object")
            continue
        for index, record in enumerate(payload, start=1):
            if not isinstance(record, dict):
                errors.append(f"{path.name}[{index}]: record must be a JSON object")
                continue
            records.append(record)
    return records, errors


def validate_records(records):
    errors = []
    seen_ids = set()
    for index, record in enumerate(records, start=1):
        label = str(record.get("id") or f"record #{index}")
        record_id = record.get("id")
        if isinstance(record_id, str) and record_id:
            if record_id in seen_ids:
                errors.append(f"{label}: duplicate id {record_id!r}")
            seen_ids.add(record_id)

        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue

        for field in REQUIRED_FIELDS[:-1]:
            if not isinstance(record[field], str):
                errors.append(f"{label}: {field} must be a string")
        if not isinstance(record["tags"], list) or any(
            not isinstance(tag, str) for tag in record["tags"]
        ):
            errors.append(f"{label}: tags must be a list of strings")
        if any(not isinstance(record[field], str) or not record[field].strip()
               for field in ("id", "place", "state", "category", "text", "language")):
            errors.append(f"{label}: id, place, state, category, text, and language must be non-empty")

        verified = record.get("last_verified")
        if isinstance(verified, str) and verified:
            try:
                if date.fromisoformat(verified).isoformat() != verified:
                    raise ValueError
            except ValueError:
                errors.append(f"{label}: last_verified must use YYYY-MM-DD format")
        elif record.get("source_name") or record.get("source_url"):
            errors.append(f"{label}: source-backed records require last_verified")

        source_name = record.get("source_name")
        source_url = record.get("source_url")
        if bool(source_name) != bool(source_url):
            errors.append(f"{label}: source_name and source_url must both be set or both be empty")
        if source_url:
            parsed = urlparse(source_url) if isinstance(source_url, str) else None
            if not parsed or parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"{label}: source_url must be an absolute HTTP(S) URL")
        elif isinstance(record.get("tags"), list) and "source_unverified" not in record["tags"]:
            errors.append(f"{label}: records without a source must include the source_unverified tag")
    return errors


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    records, errors = load_records(folder)
    errors.extend(validate_records(records))
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"PASS: validated {len(records)} records in {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
