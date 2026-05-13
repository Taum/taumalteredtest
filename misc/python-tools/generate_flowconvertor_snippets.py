import csv
import re
from pathlib import Path
# Adjust these if you move the script
BASE = Path(__file__).resolve().parents[2]  # repo root from misc/scripts/
CSV_NEW = BASE / "misc" / "uniques" / "eole-effects-new.csv"
CSV_ALL = BASE / "misc" / "uniques" / "eole-effects-all.csv"
FLOW = BASE / "modules" / "php" / "Helpers" / "FlowConvertor.php"
def load_all_abilities(csv_path):
    """Return dict[id] = {'type': type, 'text': text} from a CSV."""
    abilities = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ability_id = int(row["idGd"])
            except (KeyError, ValueError):
                continue
            abilities[ability_id] = {
                "type": row.get("type", "").strip(),
                "text": row.get("text", "").strip(),
            }
    return abilities
def extract_existing_ids(flow_path):
    """Extract all numeric IDs used as keys (e.g. 532 => [) in FlowConvertor."""
    content = flow_path.read_text(encoding="utf-8", errors="ignore")
    ids = set()
    for m in re.finditer(r"(\d+)\s*=>\s*\[", content):
        ids.add(int(m.group(1)))
    return ids
def php_escape(s: str) -> str:
    """Escape a Python string for inclusion in single-quoted PHP."""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    return s
def main():
    all_abilities = load_all_abilities(CSV_ALL)
    new_abilities = load_all_abilities(CSV_NEW)
    existing_ids = extract_existing_ids(FLOW)
    # Determine which IDs from new.csv are not yet present in FlowConvertor
    missing = {}
    for ability_id, data in new_abilities.items():
        if ability_id in existing_ids:
            continue
        # Prefer canonical data from all.csv if present
        canonical = all_abilities.get(ability_id, data)
        missing[ability_id] = canonical
    if not missing:
        print("// No new abilities found: all IDs from eole-effects-new.csv seem to already be in FlowConvertor.php")
        return
    # Group by type
    grouped = {}
    for ability_id, data in sorted(missing.items()):
        t = data["type"] or "UNKNOWN"
        grouped.setdefault(t, []).append((ability_id, data["text"]))
    for t in sorted(grouped.keys()):
        print()
        print(f"// === {t} abilities to add ===")
        for ability_id, text in grouped[t]:
            desc = php_escape(text)
            print(f"      {ability_id} => [")
            print(f"        'description' => clienttranslate('{desc}'),")
            print(f"        // TODO: implement me")
            print("      ],")
if __name__ == "__main__":
    main()