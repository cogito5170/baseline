import sys
import time
import subprocess
import json
import os
import shutil
import re
from pathlib import Path
from datetime import datetime, timezone

# Configuration
REPO_URL = "https://github.com/cogito5170/baseline.git"
BRANCH = "ga-mailbox"
CHECKOUT_DIR = Path("/tmp/ga-mailbox-checkout")
HANDLED_RECORD_FILE = Path.home() / "handled_record.json"
NOTES_FILE = Path.home() / "local_notes.md"
MAX_CONCURRENT_RUNS = 2
TIME_LIMIT = 1800 # 30 minutes

LOCAL_FORMAT_MD = Path(__file__).parent / "LOCAL_FORMAT.md"

def load_handled_record():
    if HANDLED_RECORD_FILE.exists():
        with open(HANDLED_RECORD_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_handled_record(record):
    with open(HANDLED_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=2)

def fetch_and_checkout():
    if not CHECKOUT_DIR.exists():
        subprocess.run(["git", "clone", "-b", BRANCH, REPO_URL, str(CHECKOUT_DIR)], check=True)
    else:
        subprocess.run(["git", "fetch", "origin", BRANCH], cwd=CHECKOUT_DIR, check=True)
        subprocess.run(["git", "reset", "--hard", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR, check=True)

def parse_mail_file(mail_file: Path):
    content = mail_file.read_text()
    id_match = re.search(r'Directive ID:\s*(\S+)', content)
    rev_match = re.search(r'Rev:\s*(\d+)', content)
    
    # Fallback parsing if we rely on filename like <ts>-baseline-<ID>.md
    d_id = id_match.group(1) if id_match else "UNKNOWN"
    rev = int(rev_match.group(1)) if rev_match else 1
    
    if d_id == "UNKNOWN":
        fname = mail_file.name
        if "baseline-" in fname:
            d_id = fname.split("baseline-")[-1].replace(".md", "")
    
    return d_id, rev, content

def find_new_work(handled_record):
    work_dir = CHECKOUT_DIR / "to" / "LOCAL"
    new_work = []
    if not work_dir.exists():
        return new_work
    
    # Sort files by modification time (oldest first)
    files = sorted(work_dir.glob("*.md"), key=os.path.getmtime)
    
    for mail_file in files:
        d_id, rev, content = parse_mail_file(mail_file)
        if d_id == "UNKNOWN": continue
        key = f"{d_id}_{rev}"
        
        record = handled_record.get(key)
        if not record:
            new_work.append((mail_file, d_id, rev, key))
        elif record.get("status") == "running":
            # Handled record says it was running, it means a restart cut it off
            # We restart once, then answer as declined
            restarts = record.get("restarts", 0)
            if restarts < 1:
                new_work.append((mail_file, d_id, rev, key))
            else:
                write_fallback_reply(d_id, rev, "declined", "cut off by restart more than once")
                record["status"] = "declined"
                save_handled_record(handled_record)
    
    return new_work

def is_read_only(content):
    # Determine if directive is read-only
    # The prompt says: Pro for a directive that changes files, branches or the VM. Flash for read-only.
    # We do a basic heuristic or if it has explicitly write commands. 
    # Just returning True as default flash, unless it specifies write actions.
    if re.search(r'(change|write|modify|create|delete|update|commit|push|git|install|apt|systemctl)', content.lower()):
        return False
    return True

def agy_invoke(d_id, rev, mail_file, is_ro):
    # Context
    instruction_text = LOCAL_FORMAT_MD.read_text() if LOCAL_FORMAT_MD.exists() else ""
    notes_text = NOTES_FILE.read_text() if NOTES_FILE.exists() else ""
    mail_content = mail_file.read_text()
    
    context = f"{instruction_text}\n\n---\n\n{notes_text}\n\n---\n\n{mail_content}"
    
    model = "Flash" if is_ro else "Pro"
    # Provide the context to agy. agy non-interactive: `agy -p`?
    # Or just `echo context | agy -p`. Since I don't know agy exact flags:
    # "non-interactive agy -p process"
    
    cmd = ["agy", "-p"]
    # We will run this via subprocess
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        stdout, _ = process.communicate(input=context, timeout=TIME_LIMIT)
        return stdout, process.returncode, model
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, _ = process.communicate()
        return stdout + "\nTimeout exceeded.", 124, model

def write_fallback_reply(d_id, rev, status, reason, stdout=""):
    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    reply_path = CHECKOUT_DIR / "to" / "baseline" / reply_filename
    
    content = f"""```ga
{{"schema": "report/2", "from": "LOCAL",
 "handled": [{{"id": "{d_id}", "rev_seen": {rev}, "status": "{status}"}}],
 "items": [],
 "results": [],
 "blockers": [{{"kind": "other", "what": "{reason}"}}]}}
```
## Details
{reason}
```
{stdout[-2000:] if stdout else ""}
```
"""
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    reply_path.write_text(content)
    commit_and_push(reply_path, d_id)

def write_reply(d_id, rev, stdout):
    # Does stdout contain a ga block?
    if "```ga" not in stdout:
        write_fallback_reply(d_id, rev, "declined", "agy printed no valid report/2", stdout)
        return

    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    reply_path = CHECKOUT_DIR / "to" / "baseline" / reply_filename
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    reply_path.write_text(stdout)
    
    # Validation
    val_cmd = ["python3", "ops/flow/mailcheck.py", "--report", str(reply_path)]
    val_res = subprocess.run(val_cmd, cwd=CHECKOUT_DIR, capture_output=True, text=True)
    if val_res.returncode != 0:
        write_fallback_reply(d_id, rev, "declined", f"mailcheck failed: {val_res.stdout}", stdout)
        return
        
    commit_and_push(reply_path, d_id)

def commit_and_push(file_path, d_id):
    subprocess.run(["git", "add", str(file_path)], cwd=CHECKOUT_DIR, check=True)
    subprocess.run(["git", "commit", "-m", f"LOCAL reply to {d_id}"], cwd=CHECKOUT_DIR, check=True)
    
    # push with conflict handling
    for _ in range(3):
        res = subprocess.run(["git", "push", "origin", BRANCH], cwd=CHECKOUT_DIR)
        if res.returncode == 0:
            return
        # fetch and rebase
        subprocess.run(["git", "fetch", "origin", BRANCH], cwd=CHECKOUT_DIR, check=True)
        subprocess.run(["git", "rebase", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR, check=True)

def main():
    while True:
        try:
            fetch_and_checkout()
            record = load_handled_record()
            work = find_new_work(record)
            
            for mail_file, d_id, rev, key in work[:MAX_CONCURRENT_RUNS]:
                # Mark as running
                restarts = record.get(key, {}).get("restarts", 0)
                if key in record and record[key]["status"] == "running":
                    restarts += 1
                
                record[key] = {
                    "mail_file": str(mail_file),
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "status": "running",
                    "restarts": restarts
                }
                save_handled_record(record)
                
                is_ro = is_read_only(mail_file.read_text())
                stdout, retcode, model = agy_invoke(d_id, rev, mail_file, is_ro)
                
                record[key]["end_time"] = datetime.now(timezone.utc).isoformat()
                record[key]["exit_status"] = retcode
                record[key]["model"] = model
                
                if retcode != 0 and retcode != 124:
                    write_fallback_reply(d_id, rev, "declined", f"crashed with exit code {retcode}", stdout)
                    record[key]["status"] = "declined"
                elif retcode == 124:
                    write_fallback_reply(d_id, rev, "declined", "timed out", stdout)
                    record[key]["status"] = "declined"
                else:
                    write_reply(d_id, rev, stdout)
                    record[key]["status"] = "done"
                    
                save_handled_record(record)
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        time.sleep(30)

if __name__ == "__main__":
    main()
