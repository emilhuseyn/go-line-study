"""Row 45, step 1b: re-fetch versions whose .info or .mod failed with a network error (status -1).
404/410 answers are genuine (listed tag no longer served) and are kept as failures.

    py scripts/01b_retry.py
"""
import glob
import importlib.util
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c1", os.path.join(HERE, "01_collect.py"))
c1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c1)

fixed = still = 0
for path in sorted(glob.glob(os.path.join(os.path.dirname(HERE), "data", "modules", "*.json"))):
    rec = json.load(open(path, encoding="utf-8"))
    changed = False
    for i, v in enumerate(rec["versions"]):
        if v["info_status"] == -1 or v["mod_status"] == -1:
            nv = c1.one_version(rec["module"], v["version"])
            if nv["info_status"] == 200 and nv["mod_status"] == 200:
                fixed += 1
            else:
                still += 1
            rec["versions"][i] = nv
            changed = True
    if changed:
        json.dump(rec, open(path + ".tmp", "w", encoding="utf-8"))
        os.replace(path + ".tmp", path)
print("retried: fixed", fixed, "still failing", still)
