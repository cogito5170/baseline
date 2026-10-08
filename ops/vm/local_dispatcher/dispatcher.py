import logging
from logging.handlers import RotatingFileHandler
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
DRY_RUN = "--dry-run" in sys.argv

git_lock = threading.Lock()
record_lock = threading.Lock()

def setup_logging():
    log_file = Path.home() / "ga-local.log"
    needs_header = not log_file.exists() or log_file.stat().st_size == 0
    
    if needs_header:
        with open(log_file, "a") as f:
            f.write("To stop: systemctl --user stop ga-local.service\n")
            
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
    if DRY_RUN:
        return
    with open(HANDLED_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=2)

def update_record(key, data_update):
    if DRY_RUN:
        return
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
        
        subprocess.run("git show origin/claude/gracious-meitner-vp49xe:ops/flow/mailcheck.py > /tmp/mailcheck.py", cwd=CHECKOUT_DIR, shell=True, check=True)
        subprocess.run("git show origin/claude/gracious-meitner-vp49xe:ops/flow/nocode.py > /tmp/nocode.py || true", cwd=CHECKOUT_DIR, shell=True)

def parse_mail_file(mail_file: Path):
    content = mail_file.read_text()
    d_id = "UNKNOWN"
    rev = 1
    after = []
    scope = ""
    done_whens = []
    match = re.search(r'```ga\s*(\{.*?\})\s*```', content, re.DOTALL)
    if match:
        try:
            ga_data = json.loads(match.group(1))
            d_id = ga_data.get('id', d_id)
            rev = ga_data.get('rev', 1)
            after = ga_data.get('after', [])
            scope = ga_data.get('scope', "")
            for item in ga_data.get('done_when', []):
                if 'id' in item:
                    done_whens.append(item['id'])
        except json.JSONDecodeError:
            pass
            
    if d_id == "UNKNOWN":
        fname = mail_file.name
        if "baseline-" in fname:
            d_id = fname.split("baseline-")[-1].replace(".md", "")
            
    return d_id, rev, content, after, scope, done_whens

def find_new_work(handled_record, active_keys):
    work_dir = CHECKOUT_DIR / "to" / "LOCAL"
    new_work = []
    if not work_dir.exists():
        return new_work
    
    files = sorted(work_dir.glob("*.md"), key=os.path.getmtime)
    
    for mail_file in files:
        d_id, rev, content, after, scope, done_whens = parse_mail_file(mail_file)
        if d_id == "UNKNOWN": continue
        
        if DRY_RUN and d_id != "CMD-LOC9":
            continue
            
        key = f"{d_id}_{rev}"
        
        record = handled_record.get(key)
        if not record or DRY_RUN:
            new_work.append((mail_file, d_id, rev, key, scope, after, done_whens))
        elif record.get("status") == "running":
            if key in active_keys:
                continue
            restarts = record.get("restarts", 0)
            if restarts < 1:
                new_work.append((mail_file, d_id, rev, key, scope, after, done_whens))
            else:
                write_fallback_reply(d_id, rev, "declined", "cut off by restart more than once", done_whens, "cut off by restart")
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
    if isinstance(scope, list) and len(scope) > 0 and isinstance(scope[0], dict):
        text = scope[0].get("text", "")
        return text.lower().startswith("read only")
    if isinstance(scope, str):
        return scope.lower().startswith("read only")
    return False

def agy_invoke(d_id, rev, mail_file, is_ro, after, prev_session_id=None):
    instruction_text = LOCAL_FORMAT_MD.read_text() if LOCAL_FORMAT_MD.exists() else ""
    notes_text = NOTES_FILE.read_text() if NOTES_FILE.exists() else ""
    mail_content = mail_file.read_text()
    
    after_text = ""
    if after or (rev > 1 and not prev_session_id):
        baseline_dir = CHECKOUT_DIR / "to" / "baseline"
        if baseline_dir.exists():
            for f in baseline_dir.glob("*-LOCAL-*.md"):
                try:
                    content = f.read_text()
                    match = re.search(r'```ga\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if match:
                        ga_data = json.loads(match.group(1))
                        handled_ids = [h.get("id") for h in ga_data.get("handled", [])]
                        
                        is_after = any(a in handled_ids for a in after)
                        is_prev = False
                        if rev > 1 and not prev_session_id:
                            for h in ga_data.get("handled", []):
                                if h.get("id") == d_id and h.get("rev_seen", 1) < rev:
                                    is_prev = True
                                    break
                                    
                        if is_after or is_prev:
                            after_text += f"\n---\nPrevious reply: {f.name}\n{content}\n"
                except Exception:
                    pass
    
    context = f"{instruction_text}\n\n---\n\n{notes_text}\n{after_text}\n---\n\n{mail_content}"
    model = "gemini-3.8-flash-high" if is_ro else "gemini-3.1-pro-high"
    
    cmd = ["agy", "-p", context, "--model", model, "--output-format", "json", "--dangerously-skip-permissions"]
    if prev_session_id:
        cmd.extend(["--conversation", prev_session_id])
        
    if DRY_RUN:
        print(f"DRY RUN: chosen model: {model}")
        print(f"DRY RUN: command line: agy -p <prompt_elided> --model {model} --output-format json --dangerously-skip-permissions")
        
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        stdout_text, _ = process.communicate(timeout=TIME_LIMIT)
        response_text = ""
        tokens_in, tokens_out, cached_tokens, turns, seconds = None, None, None, None, None
        conv_id = "none"
        status = "UNKNOWN"
        raw_stdout = stdout_text
        
        try:
            lines = stdout_text.strip().split('\n')
            data = json.loads(lines[-1])
            response_text = data.get("response", "")
            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens")
            tokens_out = usage.get("output_tokens")
            cached_tokens = usage.get("cache_read_tokens")
            thinking_tokens = usage.get("thinking_tokens")
            if thinking_tokens is not None:
                print(f"Thinking tokens for {d_id}: {thinking_tokens}")
            turns = data.get("num_turns")
            seconds = data.get("duration_seconds")
            status = data.get("status", "UNKNOWN")
            conv_id = data.get("conversation_id", "none")
            
            if DRY_RUN:
                print(f"DRY RUN: raw agy JSON (response cut to 800 chars):")
                dry_data = data.copy()
                if "response" in dry_data and len(dry_data["response"]) > 800:
                    dry_data["response"] = dry_data["response"][:800] + "... [cut]"
                print(json.dumps(dry_data, indent=2))
        except Exception:
            response_text = stdout_text
            print("Checked agy JSON output for token counts. None found or parsing failed.")
            
        return response_text, process.returncode, model, tokens_in, tokens_out, cached_tokens, turns, seconds, conv_id, status, raw_stdout
    except subprocess.TimeoutExpired:
        process.kill()
        stdout_text, _ = process.communicate()
        return "", 124, model, None, None, None, None, None, "none", "TIMEOUT", stdout_text

def write_fallback_reply(d_id, rev, reply_status, reason, done_whens, details, model=None, tokens_in=None, tokens_out=None, cached_tokens=None, turns=None, seconds=None):
    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    persistent_reply_path = Path.home() / "saved_replies" / reply_filename
    persistent_reply_path.parent.mkdir(parents=True, exist_ok=True)
    
    ga_block = {
        "schema": "report/2",
        "from": "LOCAL",
        "handled": [{"id": d_id, "rev_seen": rev, "status": reply_status}],
        "items": [{"id": dw, "state": "na"} for dw in done_whens],
        "results": [
            {"name": "model", "value": model},
            {"name": "input_tokens", "value": tokens_in},
            {"name": "output_tokens", "value": tokens_out},
            {"name": "cached_tokens", "value": cached_tokens},
            {"name": "turns", "value": turns},
            {"name": "seconds", "value": seconds}
        ],
        "blockers": [{"kind": "other", "what": reason}]
    }
    
    content = f"```ga\n{json.dumps(ga_block, indent=2)}\n```\n## Details\n{details}\n"
    persistent_reply_path.write_text(content)
    
    val_cmd = ["python3", "/tmp/mailcheck.py", "--report", str(persistent_reply_path)]
    val_res = subprocess.run(val_cmd, capture_output=True, text=True)
    if DRY_RUN:
        print(f"DRY RUN: full reply text it would push:\n---\n{content}\n---")
        print(f"DRY RUN: mailcheck output:\n{val_res.stdout}\n{val_res.stderr}")
        
    success = commit_and_push(persistent_reply_path, d_id)
    return persistent_reply_path, success

def write_reply(d_id, rev, stdout, done_whens, model, tokens_in, tokens_out, cached_tokens, turns, seconds, raw_stdout):
    match = re.search(r'```ga\s*(\{.*?\})\s*```', stdout, re.DOTALL)
    if not match:
        details_content = f"agy printed no valid report/2\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
        return write_fallback_reply(d_id, rev, "declined", "agy printed no valid report/2", done_whens, details_content, model, tokens_in, tokens_out, cached_tokens, turns, seconds)

    try:
        ga_data = json.loads(match.group(1))
        results = ga_data.get("results", [])
        new_results = []
        for r in results:
            if r.get("name") not in ["model", "input_tokens", "output_tokens", "cached_tokens", "turns", "seconds"]:
                new_results.append(r)
        
        new_results.extend([
            {"name": "model", "value": model},
            {"name": "input_tokens", "value": tokens_in},
            {"name": "output_tokens", "value": tokens_out},
            {"name": "cached_tokens", "value": cached_tokens},
            {"name": "turns", "value": turns},
            {"name": "seconds", "value": seconds}
        ])
        ga_data["results"] = new_results
        
        new_json = json.dumps(ga_data, indent=2)
        stdout = stdout.replace(match.group(1), f"\n{new_json}\n")
    except json.JSONDecodeError:
        pass
        
    reply_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-LOCAL-{d_id}.md"
    persistent_reply_path = Path.home() / "saved_replies" / reply_filename
    persistent_reply_path.parent.mkdir(parents=True, exist_ok=True)
    persistent_reply_path.write_text(stdout)
    
    val_cmd = ["python3", "/tmp/mailcheck.py", "--report", str(persistent_reply_path)]
    val_res = subprocess.run(val_cmd, capture_output=True, text=True)
    
    if DRY_RUN:
        print(f"DRY RUN: full reply text it would push:\n---\n{stdout}\n---")
        print(f"DRY RUN: mailcheck output:\n{val_res.stdout}\n{val_res.stderr}")
        
    if val_res.returncode != 0:
        details = f"mailcheck failed: {val_res.stdout}\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
        return write_fallback_reply(d_id, rev, "declined", f"mailcheck failed", done_whens, details, model, tokens_in, tokens_out, cached_tokens, turns, seconds)
        
    success = commit_and_push(persistent_reply_path, d_id)
    return persistent_reply_path, success

def commit_and_push(persistent_reply_path, d_id):
    if DRY_RUN:
        return True
        
    reply_filename = persistent_reply_path.name
    target_path = CHECKOUT_DIR / "to" / "baseline" / reply_filename
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with git_lock:
        shutil.copy(str(persistent_reply_path), str(target_path))
        subprocess.run(["git", "add", str(target_path)], cwd=CHECKOUT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"LOCAL reply to {d_id}"], cwd=CHECKOUT_DIR, check=True)
        for _ in range(3):
            res = subprocess.run(["git", "push", "origin", BRANCH], cwd=CHECKOUT_DIR)
            if res.returncode == 0:
                return True
            subprocess.run(["git", "fetch", "origin", BRANCH], cwd=CHECKOUT_DIR, check=True)
            rebase_res = subprocess.run(["git", "rebase", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR)
            if rebase_res.returncode != 0:
                subprocess.run(["git", "rebase", "--abort"], cwd=CHECKOUT_DIR)
                subprocess.run(["git", "reset", "--hard", f"origin/{BRANCH}"], cwd=CHECKOUT_DIR)
                shutil.copy(str(persistent_reply_path), str(target_path))
                subprocess.run(["git", "add", str(target_path)], cwd=CHECKOUT_DIR, check=True)
                subprocess.run(["git", "commit", "-m", f"LOCAL reply to {d_id}"], cwd=CHECKOUT_DIR, check=True)
        return False

def worker_task(mail_file, d_id, rev, key, scope, after, done_whens):
    try:
        prev_session_id = None
        with record_lock:
            record = load_handled_record()
            restarts = record.get(key, {}).get("restarts", 0)
            if key in record and record[key].get("status") == "running":
                restarts += 1
            if rev > 1:
                prev_key = f"{d_id}_{rev-1}"
                prev_session_id = record.get(prev_key, {}).get("session_id")
                if prev_session_id == "none":
                    prev_session_id = None
                
        update_record(key, {
            "mail_file": str(mail_file),
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "restarts": restarts
        })
        
        is_ro = is_read_only(scope)
        stdout, retcode, model, tk_in, tk_out, tk_cache, turns, secs, conv_id, status, raw_stdout = agy_invoke(
            d_id, rev, mail_file, is_ro, after, prev_session_id
        )
        
        update_record(key, {
            "end_time": datetime.now(timezone.utc).isoformat(),
            "exit_status": retcode,
            "model": model,
            "session_id": conv_id
        })
        
        if status != "SUCCESS" or not stdout.strip():
            reason = "agy printed no valid report/2"
            if not stdout.strip():
                reason = "agy response was empty"
            if status != "SUCCESS":
                reason = f"agy failed with status {status}"
                
            details_content = f"status: {status}\nexit code: {retcode}\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_path, success = write_fallback_reply(
                d_id, rev, "declined", reason, done_whens, details_content, 
                model, tk_in, tk_out, tk_cache, turns, secs
            )
        elif retcode != 0 and retcode != 124:
            details_content = f"crashed with exit code {retcode}\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_path, success = write_fallback_reply(d_id, rev, "declined", "crashed", done_whens, details_content, model, tk_in, tk_out, tk_cache, turns, secs)
        elif retcode == 124:
            details_content = f"timed out\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_path, success = write_fallback_reply(d_id, rev, "declined", "timed out", done_whens, details_content, model, tk_in, tk_out, tk_cache, turns, secs)
        else:
            reply_path, success = write_reply(d_id, rev, stdout, done_whens, model, tk_in, tk_out, tk_cache, turns, secs, raw_stdout)
            
        record_status = "done" if success else "unpushed"
        update_record(key, {
            "status": record_status,
            "reply_file": str(reply_path)
        })
    except Exception as e:
        import traceback
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(f"Worker exception for {key}:\n{tb}")
        write_fallback_reply(d_id, rev, "declined", "worker crashed", done_whens, tb)
        update_record(key, {"status": "declined"})

def main():
    if not DRY_RUN:
        setup_logging()
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_RUNS)
    active_futures = {}
    
    while True:
        try:
            fetch_and_checkout()
            with record_lock:
                record = load_handled_record()
            
            done_keys = [k for k, fut in active_futures.items() if fut.done()]
            for k in done_keys:
                del active_futures[k]
                
            work = find_new_work(record, list(active_futures.keys()))
            
            for mail_file, d_id, rev, key, scope, after, done_whens in work:
                if key not in active_futures and len(active_futures) < MAX_CONCURRENT_RUNS:
                    fut = executor.submit(worker_task, mail_file, d_id, rev, key, scope, after, done_whens)
                    active_futures[key] = fut
                    
            if DRY_RUN:
                for fut in active_futures.values():
                    fut.result()
                break
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
        if DRY_RUN:
            break
            
        time.sleep(30)

if __name__ == "__main__":
    main()
