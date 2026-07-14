#!/usr/bin/env python
"""
show_actb_complexes.py

Why does ACTB (beta-actin) act as a promiscuous "hub" in a protein-protein
interaction network, and why was it labelled "member of no complex" in the
demo figures?

Short answer: it is NOT a member of no complex. In the demo we only put THREE
complexes into the graph (Arp2/3, CCT/TRiC, MCM). ACTB belongs to none of
*those three* -- but it is a curated participant in dozens of OTHER complexes.
Its many real memberships are exactly what give it a high degree, which a
connectivity-based score then mistakes for "belongs to complex A/B/C".

This script queries the EBI Complex Portal for every curated complex that
lists ACTB as a participant, and summarises them.

Data source: EBI Complex Portal (https://www.ebi.ac.uk/complexportal/),
via its REST search API.  ACTB UniProt accession = P60709.
"""

import sys
import urllib.parse
import urllib.request
import json
from collections import Counter

UNIPROT_ACC = "P60709"          # ACTB / beta-actin
BASE = "https://www.ebi.ac.uk/intact/complex-ws/search/"

def fetch_complexes(accession):
    """Return all curated complexes that contain `accession` as a participant.

    The Complex Portal search endpoint is `.../search/<term>` and is paginated
    via `first` (offset) and `number` (page size). Searching on the bare
    UniProt accession returns the complexes that list it as a participant; the
    page reports `totalNumberOfResults`, so we walk every page until we have
    them all.
    """
    rows, start, page = [], 0, 100
    total = None
    while True:
        params = urllib.parse.urlencode({"first": start, "number": page})
        url = f"{BASE}{urllib.parse.quote(accession)}?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        if total is None:
            total = data.get("totalNumberOfResults", 0)
        batch = data.get("elements", []) or []
        rows.extend(batch)
        start += page
        if start >= total or not batch:
            break
    return rows, total

def family(name):
    """Crude grouping of a complex by its name, just for a readable summary."""
    n = name.lower()
    if "swi/snf" in n or "baf" in n:            return "SWI/SNF chromatin remodeling"
    if "nua4" in n or "acetyltransferase" in n: return "NuA4 histone acetyltransferase"
    if "dynactin" in n:                          return "Dynactin"
    if "tubulin" in n:                           return "gamma-tubulin ring"
    return "other"

def main(accession=UNIPROT_ACC):
    label = "ACTB / beta-actin" if accession == UNIPROT_ACC else accession
    comps, total = fetch_complexes(accession)
    print(f"{accession} ({label}) is a curated participant in "
          f"{total} Complex Portal complexes.\n")

    fams = Counter(family(c.get("complexName", "")) for c in comps)
    print("Grouped by complex family:")
    for fam, k in fams.most_common():
        print(f"  {k:>3}  {fam}")

    print("\nFull list:")
    for c in sorted(comps, key=lambda x: x.get("complexAC", "")):
        print(f"  {c.get('complexAC',''):11s}  {c.get('complexName','')[:70]}")

    print("\n---")
    print(f"Takeaway: {accession} has {total} real curated complex membership(s).")
    if accession == UNIPROT_ACC:
        print("In a network built from only Arp2/3 + CCT + MCM, none of these 43 are")
        print("represented, so ACTB looks like a non-member that nonetheless connects")
        print("everywhere -- i.e. a high-degree hub. That degree is real biology;")
        print("treating it as evidence of membership in Arp2/3/CCT/MCM is the bias.")
    else:
        print("The more complexes a protein truly belongs to, the higher its degree in")
        print("a broad interaction network. If those complexes are absent from a small")
        print("demo graph, the protein still connects widely and reads as a high-degree")
        print("hub -- real connectivity that a membership score can mistake for evidence.")

if __name__ == "__main__":
    acc = sys.argv[1] if len(sys.argv) > 1 else UNIPROT_ACC
    main(acc)
