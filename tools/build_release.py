#!/usr/bin/env python3
"""Build the Foundry release zip: module.json at the zip root, runtime files only.
Usage: tools/build_release.py <outdir>   -> <outdir>/module.zip and <outdir>/module.json
Checks that module.json's download URL names the same version as module.json."""
import json, os, sys, zipfile, shutil
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
m = json.load(open(os.path.join(root, "module.json")))
v = m["version"]
assert f"/download/v{v}/module.zip" in m["download"], f"download URL does not match version {v}: {m['download']}"
assert m["manifest"].endswith("/releases/latest/download/module.json"), m["manifest"]
FILES = ["module.json", "README.md", "LICENSE", "CHANGELOG.md"]
DIRS = ["scripts", "templates", "lang", "icons"]
zp = os.path.join(out, "module.zip")
n = 0
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in FILES:
        z.write(os.path.join(root, f), f); n += 1
    # Explicit directory entries: Foundry's package installer fails without them
    # ("The file scripts/settings.js ... does not exist"), even though every file is present.
    for d in DIRS:
        for r, dirs, fs in os.walk(os.path.join(root, d)):
            dirs.sort()
            z.writestr(zipfile.ZipInfo(os.path.relpath(r, root) + "/"), ""); n += 1
            for f in sorted(fs):
                if f.endswith((".pyc",)) or f.startswith("."): continue
                p = os.path.join(r, f); z.write(p, os.path.relpath(p, root)); n += 1
shutil.copy(os.path.join(root, "module.json"), os.path.join(out, "module.json"))
print(f"{zp}: {n} files, {os.path.getsize(zp)} bytes, version {v}")
