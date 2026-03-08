import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://places.googleapis.com/v1/places:searchText"

# Basic + Pro fields — keeps costs low under the free $200/mo credit
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.businessStatus",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "nextPageToken",
])


def search_places(query, max_results=60):
    """Call Google Places Text Search (New) and return all pages of results."""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not api_key or api_key == "paste_your_api_key_here":
        raise ValueError("Set your GOOGLE_PLACES_API_KEY in the .env file.")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    all_places = []
    page_token = None

    while len(all_places) < max_results:
        body = {"textQuery": query, "pageSize": 20}
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(API_URL, json=body, headers=headers, timeout=15)
        if resp.status_code != 200:
            error = resp.json().get("error", {})
            msg = error.get("message", resp.text)
            raise RuntimeError(f"API error ({resp.status_code}): {msg}")

        data = resp.json()
        places = data.get("places", [])
        all_places.extend(places)

        page_token = data.get("nextPageToken")
        if not page_token or not places:
            break

    return all_places[:max_results]


def flatten(place):
    """Turn a place dict into a flat row for display / CSV."""
    dn = place.get("displayName", {})
    loc = place.get("location", {})
    ptype = place.get("primaryTypeDisplayName", {})
    return {
        "Name": dn.get("text", ""),
        "Address": place.get("formattedAddress", ""),
        "Phone": place.get("nationalPhoneNumber", ""),
        "Website": place.get("websiteUri", ""),
        "Rating": place.get("rating", ""),
        "Reviews": place.get("userRatingCount", ""),
        "Type": ptype.get("text", ""),
        "Status": place.get("businessStatus", ""),
        "Lat": loc.get("latitude", ""),
        "Lng": loc.get("longitude", ""),
        "Google Maps": place.get("googleMapsUri", ""),
    }


COLUMNS = list(flatten({}).keys())


# ── GUI ──────────────────────────────────────────────────────────────────


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Google Places Scraper")
        self.geometry("1100x620")
        self.minsize(800, 400)
        self.rows = []

        self._build_input_bar()
        self._build_table()
        self._build_status_bar()

    # ── widgets ──────────────────────────────────────────────────────────

    def _build_input_bar(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")

        ttk.Label(bar, text="Keyword:").pack(side="left")
        self.keyword_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.keyword_var, width=20).pack(side="left", padx=(4, 12))

        ttk.Label(bar, text="Category:").pack(side="left")
        self.category_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.category_var, width=20).pack(side="left", padx=(4, 12))

        ttk.Label(bar, text="City:").pack(side="left")
        self.city_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.city_var, width=20).pack(side="left", padx=(4, 12))

        ttk.Button(bar, text="Search", command=self._on_search).pack(side="left", padx=(8, 4))
        ttk.Button(bar, text="Export CSV", command=self._on_export).pack(side="left", padx=4)

    def _build_table(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.tree = ttk.Treeview(container, columns=COLUMNS, show="headings", selectmode="browse")

        col_widths = {
            "Name": 180, "Address": 220, "Phone": 110, "Website": 150,
            "Rating": 50, "Reviews": 60, "Type": 100, "Status": 80,
            "Lat": 80, "Lng": 80, "Google Maps": 160,
        }
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), minwidth=40)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", padding=4).pack(
            fill="x", side="bottom"
        )

    # ── actions ──────────────────────────────────────────────────────────

    def _build_query(self):
        parts = []
        kw = self.keyword_var.get().strip()
        cat = self.category_var.get().strip()
        city = self.city_var.get().strip()
        if kw:
            parts.append(kw)
        if cat:
            parts.append(cat)
        if city:
            parts.append(f"in {city}")
        return " ".join(parts)

    def _on_search(self):
        query = self._build_query()
        if not query:
            messagebox.showwarning("Input needed", "Enter at least a keyword, category, or city.")
            return

        self.status_var.set(f"Searching: {query} …")
        self.update_idletasks()

        try:
            places = search_places(query)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error")
            return

        self.tree.delete(*self.tree.get_children())
        self.rows = [flatten(p) for p in places]
        for row in self.rows:
            self.tree.insert("", "end", values=[row[c] for c in COLUMNS])

        self.status_var.set(f"Found {len(self.rows)} results for '{query}'")

    def _on_export(self):
        if not self.rows:
            messagebox.showinfo("Nothing to export", "Run a search first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="places_export.csv",
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(self.rows)

        self.status_var.set(f"Exported {len(self.rows)} rows → {path}")


if __name__ == "__main__":
    App().mainloop()
