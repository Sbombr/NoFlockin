import pandas as pd
import glob
import os

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

CATEGORY_KEYWORDS = [
    ("Missing / Endangered Person", ["missing person", "missing", "endangered", "amber"]),
    ("Violent Crime", ["shooting", "homicide", "robbery", "carjacking", "kidnapping", "assault", "shots fired"]),
    ("Stolen Vehicle / MVT", ["stolen", "mvt", "stole"]),
    ("Warrant / Wanted Person", ["warrant", "wanted", "fugitive"]),
    ("BOLO / Suspect Vehicle", ["bolo", "atl", "suspect", "suspicious", "vehicle of interest", "sus"]),
    ("Drug Investigation", ["drug", "narcotic"]),
    ("Property Crime", ["burglary", "theft", "fraud", "shoplift"]),
    ("Traffic Enforcement", ["traffic", "infraction"]),
    ("Patrol / Routine", ["patrol"]),
    ("Administrative / System", ["test", "image download", "daytime search"]),
    ("General Investigation", ["inv", "case", "investigat"]),
]


def fix_corrupted_code(text):
    if text.endswith("00:00:00"):
        date_part = text.split(" ")[0]
        pieces = date_part.split("-")
        if len(pieces) == 3:
            y, m, d = pieces
            if y.startswith("19"):
                return m + "-" + y[-2:]
            else:
                return m + "-" + d
        return text

    parts = text.split("-")
    if len(parts) == 2:
        a, b = parts[0].strip(), parts[1].strip()
        if a in MONTHS:
            return MONTHS[a] + "-" + b
        if b in MONTHS:
            return MONTHS[b] + "-" + a

    return text


def normalize_reason(raw):
    if pd.isna(raw):
        return ""
    text = str(raw).strip().lower()
    if text == "":
        return ""

    text = fix_corrupted_code(text)

    text = text.replace("+", " ")
    text = text.replace("_", " ")
    text = " ".join(text.split())

    return text


def is_radio_code(text):
    stripped = text.replace("-", "")
    return stripped.isdigit()


def categorize(normalized_text):
    if normalized_text == "":
        return "No Reason Given"

    for category, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in normalized_text:
                return category

    if is_radio_code(normalized_text):
        return "Radio Code (Unresolved)"

    return "Uncategorized"


input_dir = "./datasets"
output_dir = "./categorized_output"

os.makedirs(output_dir, exist_ok=True)

summary_rows = []

for path in sorted(glob.glob(os.path.join(input_dir, "*.csv"))):
    city = os.path.splitext(os.path.basename(path))[0]
    df = pd.read_csv(path, dtype=str)

    df["reason_normalized"] = df["reason"].apply(normalize_reason)
    df["reason_category"] = df["reason_normalized"].apply(categorize)

    out_path = os.path.join(output_dir, city + "_categorized.csv")
    df.to_csv(out_path, index=False)

    counts = df["reason_category"].value_counts()
    for category, count in counts.items():
        summary_rows.append({"city": city, "category": category, "count": count})

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(os.path.join(output_dir, "category_summary.csv"), index=False)

pivot = summary_df.pivot_table(index="category", columns="city", values="count", fill_value=0, aggfunc="sum")
pivot["total"] = pivot.sum(axis=1)
pivot = pivot.sort_values("total", ascending=False)
print(pivot)