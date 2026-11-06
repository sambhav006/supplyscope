"""Public mirror acquisition; existing raw files are preserved. --local imports CSVs."""
import argparse, hashlib, json, shutil, urllib.request
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
TABLES = ["orders","order_items","customers","sellers","products","order_payments","order_reviews"]
REPO = "anggid/Brazilian-E-Commerce-Public-Dataset-by-Olist"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--local",type=Path); args=ap.parse_args()
    manifest_path=ROOT/"data/raw/manifest.json"
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    commit=previous.get("mirror_commit")
    if not args.local and not commit:
        commit=json.load(urllib.request.urlopen(f"https://api.github.com/repos/{REPO}/commits/main"))["sha"]
    entries=[]
    for table in TABLES:
        name=f"olist_{table}_dataset.csv"; dest=ROOT/"data/raw"/name
        url=f"https://raw.githubusercontent.com/{REPO}/{commit}/{name}" if not args.local else None
        if not dest.exists():
            if args.local: shutil.copy2(args.local/name,dest)
            else:
                with urllib.request.urlopen(url,timeout=120) as response: dest.write_bytes(response.read())
        digest=hashlib.sha256(dest.read_bytes()).hexdigest()
        old=next((x for x in previous.get("files",[]) if x["name"]==name),None)
        if old and old["sha256"] != digest: raise ValueError(f"Checksum changed: {name}; investigate before replacing manifest")
        entries.append({"name":name,"url":old["url"] if old else url,"sha256":digest,"bytes":dest.stat().st_size})
        print(name,dest.stat().st_size)
    data={"source":"https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce","attribution":"Olist and collaborators","license":"CC BY-NC-SA 4.0","license_url":"https://creativecommons.org/licenses/by-nc-sa/4.0/","mirror_commit":commit,"acquired_utc":previous.get("acquired_utc",datetime.now(timezone.utc).isoformat()),"files":entries,"local_import":str(args.local) if args.local else None}
    manifest_path.write_text(json.dumps(data,indent=2))
if __name__=="__main__": main()
