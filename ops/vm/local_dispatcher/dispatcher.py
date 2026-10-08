import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

def setup_logging():
    log_file = Path.home() / "ga-local.log"
    needs_header = not log_file.exists() or log_file.stat().st_size == 0
    
    if needs_header:
        with open(log_file, "a") as f:
            f.write("To stop: systemctl --user stop ga-local.service\n")
            
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    
    class HeaderRotatingFileHandler(RotatingFileHandler):
        def doRollover(self):
            super().doRollover()
            with open(self.baseFilename, 'a') as f:
                f.write("To stop: systemctl --user stop ga-local.service\n")
                
    handler = HeaderRotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    class StreamToLogger:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
        def write(self, buf):
            for line in buf.rstrip().splitlines():
                if line:
                    self.logger.log(self.level, line.rstrip())
        def flush(self):
            pass

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)
import sys
import time
import subprocess
import json
import os
import shutil
import re
import threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

# Configuration
REPO_URL = "https://github.com/cogito5170/baseline.git"
BRANCH = "ga-mailbox"
CHECKOUT_DIR = Path("/tmp/ga-mailbox-checkout")
HANDLED_RECORD_FILE = Path.home() / "handled_record.json"
NOTES_FILE = Path.home() / "local_notes.md"
MAX_CONCURRENT_RUNS = 2
TIME_LIMIT = 1800 # 30 minutes

LOCAL_FORMAT_MD = Path(__file__).parent / "LOCAL_FORMAT.md"

git_lock = threading.Lock()
record_lock = threading.Lock()

def load_handled_record():
    record = {}
    if HANDLED_RECORD_FILE.exists():
        with open(HANDLED_RECORD_FILE, 'r') as f:
            try:
                record = json.load(f)
            except json.JSONDecodeError:
                pass
    
    # Initialize from baseline replies
    baseline_dir = CHECKOUT_DIR / "to" / "baseline"
    if baseline_dir.exists():
        for file_path in baseline_dir.glob("*-LOCAL-*.md"):
            try:
                content = file_path.read_text()
                match = re.search(r'```ga\s*(\{.*?\})\s*```', content, re.DOTALL)
                if match:
                    ga_data = json.loads(match.group(1))
                    for handled in ga_data.get('handled', []):
                        h_id = handled.get('id')
                        h_rev = handled.get('rev_seen')
                        if h_id and h_rev:
                            k = f"{h_id}_{h_rev}"
                            if k not in record:
                                record[k] = {"status": handled.get('status', 'done')}
            except Exception:
                pass
    return record

def save_handled_record(record):
    with open(HANDLED_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=2)

def update_record(key, data_update):
    with record_lock:
        record = load_handled_record()
        if key not in record:
            record[key] = {}
        record[key].update(data_update)
        save_handled_record(record)

def fetch_and_checkout():
    with git_lock:
        if not CHECKOUT_DIR.exists():
            subprocess.run(["git", "clone", "-b", BRANCH, REPO_URL, str(CHECKOUT_DIR)], check=True)
        else:
            subprocess.run(["git", "fetch", "origin", BRANCH], cwd=CHECKOUT_DIR, check=True)
            subprocess.run(["git", "reset", "--hard", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR, check=True)
        
        # Get mailcheck.py from claude/gracious-meitner-vp49xe
        subprocess.run(["git", "fetch", "origin", "claude/gracious-meitner-vp49xe"], cwd=CHECKOUT_DIR, check=True)
        subprocess.run(["git", "checkout", "origin/claude/gracious-meitner-vp49xe", "--", "ops/flow/mailcheck.py"], cwd=CHECKOUT_DIR, check=True)
        subprocess.run("git checkout origin/claude/gracious-meitner-vp49xe -- ops/flow/nocode.py || true", cwd=CHECKOUT_DIR, shell=True)

def parse_mail_file(mail_file: Path):
    content = mail_file.read_text()
    d_id = "UNKNOWN"
    rev = 1
    after = []
    scope = ""
    match = re.search(r'```ga\s*(\{.*?\})\s*```', content, re.DOTALL)
    if match:
        try:
            ga_data = json.loads(match.group(1))
            d_id = ga_data.get('id', d_id)
            rev = ga_data.get('rev', 1)
            after = ga_data.get('after', [])
            scope = ga_data.get('scope', "")
        except json.JSONDecodeError:
            pass
            
    if d_id == "UNKNOWN":
        fname = mail_file.name
        if "baseline-" in fname:
            d_id = fname.split("baseline-")[-1].replace(".md", "")
            
    return d_id, rev, content, after, scope

def find_new_work(handled_record):
    work_dir = CHECKOUT_DIR / "to" / "LOCAL"
    new_work = []
    if not work_dir.exists():
        return new_work
    
    files = sorted(work_dir.glob("*.md"), key=os.path.getmtime)
    
    for mail_file in files:
        d_id, rev, content, after, scope = parse_mail_file(mail_file)
        if d_id == "UNKNOWN": continue
        key = f"{d_id}_{rev}"
        
        record = handled_record.get(key)
        if not record:
            new_work.append((mail_file, d_id, rev, key, scope, after))
        elif record.get("status") == "running":
            restarts = record.get("restarts", 0)
            if restarts < 1:
                new_work.append((mail_file, d_id, rev, key, scope, after))
            else:
                write_fallback_reply(d_id, rev, "declined", "cut off by restart more than once")
                update_record(key, {"status": "declined"})
        elif record.get("status") == "unpushed":
            # retry pushing
            reply_file = record.get("reply_file")
            if reply_file and Path(reply_file).exists():
                success = commit_and_push(Path(reply_file), d_id)
                if success:
                    update_record(key, {"status": "done"})
                
    return new_work

def is_read_only(scope):
    return scope.lower().startswith("read only")

def extract_ga_block_and_details(response_text):
    match = re.search(r'(```ga\n.*?```.*)', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()

def agy_invoke(d_id, rev, mail_file, is_ro, after):
    instruction_text = LOCAL_FORMAT_MD.read_text() if LOCAL_FORMAT_MD.exists() else ""
    notes_text = NOTES_FILE.read_text() if NOTES_FILE.exists() else ""
    mail_content = mail_file.read_text()
    
    after_text = ""
    if after or rev > 1:
        baseline_dir = CHECKOUT_DIR / "to" / "baseline"
        if baseline_dir.exists():
            for f in baseline_dir.glob("*-LOCAL-*.md"):
                # basic check if it's related
                if any(a in f.name for a in after) or (rev > 1 and d_id in f.name):
                    after_text += f"\n---\nPrevious reply: {f.name}\n{f.read_text()}\n"
    
    context = f"{instruction_text}\n\n---\n\n{notes_text}\n{after_text}\n---\n\n{mail_content}"
    model = "gemini-3.8-flash-high" if is_ro else "gemini-3.1-pro-high"
    
    cmd = ["agy", "-p", context, "--model", model, "--output-format", "json"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        stdout_text, _ = process.communicate(timeout=TIME_LIMIT)
        response_text = ""
        tokens_in, tokens_out, turns, seconds = None, None, None, None
        
        try:
            lines = stdout_text.strip().split('\n')
            data = json.loads(lines[-1])
            response_text = data.get("response", "")
            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens")
            tokens_out = usage.get("output_tokens")
            turns = data.get("num_turns")
            seconds = data.get("duration_seconds")
        except Exception:
            response_text = stdout_text
            print("Checked agy JSON output for token counts. None found or parsing failed.")
            
        return extract_ga_block_and_details(response_text), process.returncode, model, tokens_in, tokens_out, turns, seconds
    except subprocess.TimeoutExpired:
        process.kill()
        stdout_text, _ = process.communicate()
        return extract_ga_block_and_details(stdout_text) + "\nTimeout exceeded.", 124, model, None, None, None, None

def write_fallback_reply(d_id, rev, status, reason, stdout=""):
    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    reply_path = CHECKOUT_DIR / "to" / "baseline" / reply_filename
    
    ga_block = {
        "schema": "report/2",
        "from": "LOCAL",
        "handled": [{"id": d_id, "rev_seen": rev, "status": status}],
        "items": [{"id": d_id, "state": "na"}],
        "results": [{
            "model": "None",
            "tokens_in": None, "tokens_out": None, "turns": None, "seconds": None
        }],
        "blockers": [{"kind": "other", "what": reason}]
    }
    
    content = f"```ga\n{json.dumps(ga_block, indent=2)}\n```\n## Details\n{reason}\n```\n{stdout[-2000:] if stdout else ''}\n```\n"
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    reply_path.write_text(content)
    
    subprocess.run(["python3", "ops/flow/mailcheck.py", "--report", str(reply_path)], cwd=CHECKOUT_DIR)
    
    success = commit_and_push(reply_path, d_id)
    return reply_path, success

def write_reply(d_id, rev, stdout, model, tokens_in, tokens_out, turns, seconds):
    match = re.search(r'```ga\s*(\{.*?\})\s*```', stdout, re.DOTALL)
    if not match:
        return write_fallback_reply(d_id, rev, "declined", "agy printed no valid report/2", stdout)

    try:
        ga_data = json.loads(match.group(1))
        results = ga_data.get("results", [])
        if not results:
            results = [{}]
            ga_data["results"] = results
        for res in results:
            res["model"] = model
            res["tokens_in"] = tokens_in
            res["tokens_out"] = tokens_out
            res["turns"] = turns
            res["seconds"] = seconds
        
        new_json = json.dumps(ga_data, indent=2)
        stdout = stdout.replace(match.group(1), f"\n{new_json}\n")
    except json.JSONDecodeError:
        pass
        
    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    reply_path = CHECKOUT_DIR / "to" / "baseline" / reply_filename
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    reply_path.write_text(stdout)
    
    val_cmd = ["python3", "ops/flow/mailcheck.py", "--report", str(reply_path)]
    val_res = subprocess.run(val_cmd, cwd=CHECKOUT_DIR, capture_output=True, text=True)
    if val_res.returncode != 0:
        return write_fallback_reply(d_id, rev, "declined", f"mailcheck failed: {val_res.stdout}", stdout)
        
    success = commit_and_push(reply_path, d_id)
    return reply_path, success

def commit_and_push(file_path, d_id):
    with git_lock:
        subprocess.run(["git", "add", str(file_path)], cwd=CHECKOUT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"LOCAL reply to {d_id}"], cwd=CHECKOUT_DIR, check=True)
        for _ in range(3):
            res = subprocess.run(["git", "push", "origin", BRANCH], cwd=CHECKOUT_DIR)
            if res.returncode == 0:
                return True
            subprocess.run(["git", "fetch", "origin", BRANCH], cwd=CHECKOUT_DIR, check=True)
            subprocess.run(["git", "rebase", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR, check=True)
        return False

def worker_task(mail_file, d_id, rev, key, scope, after):
    with record_lock:
        record = load_handled_record()
        restarts = record.get(key, {}).get("restarts", 0)
        if key in record and record[key].get("status") == "running":
            restarts += 1
            
    update_record(key, {
        "mail_file": str(mail_file),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "restarts": restarts
    })
    
    is_ro = is_read_only(scope)
    stdout, retcode, model, tk_in, tk_out, turns, secs = agy_invoke(d_id, rev, mail_file, is_ro, after)
    
    update_record(key, {
        "end_time": datetime.now(timezone.utc).isoformat(),
        "exit_status": retcode,
        "model": model,
        "session_id": "none" # per M6, lacks agy session id, agy -p doesn't expose one in CLI without interactive
    })
    
    if retcode != 0 and retcode != 124:
        reply_path, success = write_fallback_reply(d_id, rev, "declined", f"crashed with exit code {retcode}", stdout)
    elif retcode == 124:
        reply_path, success = write_fallback_reply(d_id, rev, "declined", "timed out", stdout)
    else:
        reply_path, success = write_reply(d_id, rev, stdout, model, tk_in, tk_out, turns, secs)
        
    status = "done" if success else "unpushed"
    update_record(key, {
        "status": status,
        "reply_file": str(reply_path)
    })

def main():
    setup_logging()
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_RUNS)
    active_futures = {}
    
    while True:
        try:
            fetch_and_checkout()
            with record_lock:
                record = load_handled_record()
            
            # Clean up active futures
            done_keys = [k for k, fut in active_futures.items() if fut.done()]
            for k in done_keys:
                del active_futures[k]
                
            work = find_new_work(record)
            
            for mail_file, d_id, rev, key, scope, after in work:
                if key not in active_futures and len(active_futures) < MAX_CONCURRENT_RUNS:
                    fut = executor.submit(worker_task, mail_file, d_id, rev, key, scope, after)
                    active_futures[key] = fut
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        time.sleep(30)

if __name__ == "__main__":
    main()
