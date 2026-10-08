import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import subprocess
import json
import os
import re
import threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

REPO = "cogito5170/baseline"
NOTES_FILE = Path.home() / "local_notes.md"
MAX_CONCURRENT_RUNS = 2
TIME_LIMIT = 1800 # 30 minutes
VM_LOCAL_PROMPT_MD = Path(__file__).parent / "VM_LOCAL_PROMPT.md"
DRY_RUN = "--dry-run" in sys.argv

record_lock = threading.Lock()
HANDLED_RECORD_FILE = Path.home() / "handled_record.json"

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
        def flush(self): pass

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

def load_handled_record():
    if HANDLED_RECORD_FILE.exists():
        with open(HANDLED_RECORD_FILE, 'r') as f:
            try: return json.load(f)
            except: pass
    return {}

def save_handled_record(record):
    if DRY_RUN: return
    with open(HANDLED_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=2)

def update_record(key, data_update):
    if DRY_RUN: return
    with record_lock:
        record = load_handled_record()
        if key not in record: record[key] = {}
        record[key].update(data_update)
        save_handled_record(record)

def gh_api(endpoint, method="GET", body=None):
    cmd = ["gh", "api", endpoint, "-X", method]
    if body:
        cmd.extend(["-f", f"body={body}"])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return json.loads(res.stdout) if res.stdout else None
    return None

def gh_issue_edit(number, add_labels=None, remove_labels=None):
    if DRY_RUN: return
    cmd = ["gh", "issue", "edit", str(number), "-R", REPO]
    if add_labels: cmd.extend(["--add-label", ",".join(add_labels)])
    if remove_labels: cmd.extend(["--remove-label", ",".join(remove_labels)])
    subprocess.run(cmd, capture_output=True)

def gh_issue_comment(number, body):
    if DRY_RUN: return
    cmd = ["gh", "issue", "comment", str(number), "-R", REPO, "-b", body]
    subprocess.run(cmd, capture_output=True)

def extract_ga_blocks(text, author_association):
    blocks = []
    for match in re.finditer(r'```ga\s*(\{.*?\})\s*```', text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            blocks.append({"data": data, "author_association": author_association})
        except: pass
    return blocks

def find_new_work(handled_record, active_keys):
    new_work = []
    cmd = ["gh", "issue", "list", "-R", REPO, "-l", "VM", "--state", "open", "--json", "number,labels,updatedAt"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0: return new_work
    
    issues = json.loads(res.stdout)
    for iss in issues:
        number = iss["number"]
        labels = [l["name"] for l in iss["labels"]]
        if "qa:todo" not in labels and "qa:doing" not in labels: continue
        
        issue_data = gh_api(f"repos/{REPO}/issues/{number}")
        if not issue_data: continue
        comments_data = gh_api(f"repos/{REPO}/issues/{number}/comments") or []
        
        blocks = extract_ga_blocks(issue_data.get("body", ""), issue_data.get("author_association", ""))
        for c in comments_data:
            blocks.extend(extract_ga_blocks(c.get("body", ""), c.get("author_association", "")))
            
        # Filter blocks by trust
        trusted_directives = []
        for b in blocks:
            data = b["data"]
            if b["author_association"] == "OWNER" and data.get("from") == "baseline" and data.get("schema") == "directive/2" and data.get("to") == "VM_LOCAL":
                trusted_directives.append(data)
            elif data.get("schema") == "directive/2":
                logging.info(f"event: ignored untrusted item in issue #{number}: author_association={b['author_association']}, from={data.get('from')}")
                
        if not trusted_directives: continue
        
        # highest-rev directive
        latest_dir = max(trusted_directives, key=lambda x: x.get("rev", 1))
        d_id = latest_dir.get("id")
        rev = latest_dir.get("rev", 1)
        key = f"{d_id}_{rev}"
        
        if key in active_keys:
            continue
            
        record = handled_record.get(key)
        
        if "qa:todo" in labels:
            if not record or record.get("status") not in ["running", "done", "declined"]:
                new_work.append((number, latest_dir, key))
        elif "qa:doing" in labels:
            should_resume = False
            if record and record.get("status") == "running":
                start_time_str = record.get("start_time")
                if start_time_str:
                    try:
                        start = datetime.fromisoformat(start_time_str)
                        if (datetime.now(timezone.utc) - start).total_seconds() > 1800:
                            should_resume = True
                    except: pass
                else:
                    should_resume = True
            elif not record:
                updated_at_str = iss.get("updatedAt")
                if updated_at_str:
                    try:
                        updated_at = datetime.strptime(updated_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        if (datetime.now(timezone.utc) - updated_at).total_seconds() > 1800:
                            should_resume = True
                    except: pass
            if should_resume or DRY_RUN:
                new_work.append((number, latest_dir, key))
                
    return new_work

def is_read_only(scope):
    if isinstance(scope, list) and len(scope) > 0 and isinstance(scope[0], dict):
        text = scope[0].get("text", "")
        return text.lower().startswith("read only")
    if isinstance(scope, str):
        return scope.lower().startswith("read only")
    return False

def write_fallback_reply(d_id, rev, reply_status, reason, done_whens, details, model=None, tokens_in=None, tokens_out=None, cached_tokens=None, turns=None, seconds=None):
    ga_block = {
        "schema": "report/2",
        "from": "VM_LOCAL",
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
    return content

def prepare_reply(d_id, rev, stdout, done_whens, model, tokens_in, tokens_out, cached_tokens, turns, seconds, raw_stdout):
    match = re.search(r'```ga\s*(\{.*?\})\s*```', stdout, re.DOTALL)
    if not match:
        details_content = f"agy printed no valid report/2\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
        return write_fallback_reply(d_id, rev, "declined", "agy printed no valid report/2", done_whens, details_content, model, tokens_in, tokens_out, cached_tokens, turns, seconds)

    try:
        ga_data = json.loads(match.group(1))
        # Ensure it's from VM_LOCAL
        ga_data["from"] = "VM_LOCAL"
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
    except Exception: pass
    
    return stdout

def worker_task(number, directive, key):
    d_id = directive.get("id")
    rev = directive.get("rev", 1)
    done_whens = [dw.get("id") for dw in directive.get("done_when", []) if "id" in dw]
    try:
        prev_session_id = None
        with record_lock:
            record = load_handled_record()
            if rev > 1:
                prev_key = f"{d_id}_{rev-1}"
                prev_session_id = record.get(prev_key, {}).get("session_id")
        
        if not DRY_RUN:
            ack = {"schema":"ack/1", "id":d_id, "rev":rev, "from":"VM_LOCAL", "started_at":datetime.now(timezone.utc).isoformat()}
            gh_issue_comment(number, f"```ga\n{json.dumps(ack)}\n```")
            logging.info(f"event: ack posted for {d_id} rev {rev}")
            gh_issue_edit(number, add_labels=["qa:doing"], remove_labels=["qa:todo"])
            logging.info(f"event: label change for #{number} to qa:doing")
            
        update_record(key, {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running"
        })
        
        # Build prompt
        instruction_text = VM_LOCAL_PROMPT_MD.read_text() if VM_LOCAL_PROMPT_MD.exists() else ""
        notes_text = NOTES_FILE.read_text() if NOTES_FILE.exists() else ""
        
        is_ro = is_read_only(directive.get("scope", ""))
        if is_ro:
            context = f"role VM_LOCAL. report/2 rules only.\n{json.dumps(directive)}"
        else:
            context = f"{instruction_text}\n\n---\n\n{notes_text}\n---\n\n```ga\n{json.dumps(directive, indent=2)}\n```"
            
        model = "gemini-3.8-flash-high" if is_ro else "gemini-3.1-pro-high"
        
        cmd = ["/home/ubuntu/auto-agy-p.exp", "-p", context, "--model", model, "--output-format", "json", "--dangerously-skip-permissions"]
        if prev_session_id: cmd.extend(["--conversation", prev_session_id])
        
        prompt_bytes = len(context.encode("utf-8"))
        logging.info(f"event: agy start (model={model}, prompt_bytes={prompt_bytes})")
        
        if DRY_RUN:
            print(f"DRY RUN: chosen model: {model}")
            print(f"DRY RUN: command line: {' '.join(cmd)}")
            
        work_dir = Path.home() / "agy_work"
        work_dir.mkdir(exist_ok=True)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(work_dir))
        try:
            stdout_text, _ = process.communicate(timeout=TIME_LIMIT)
            retcode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout_text, _ = process.communicate()
            retcode = 124
                
        tokens_in, tokens_out, cached_tokens, turns, secs = None, None, None, None, None
        conv_id = "none"
        status = "UNKNOWN"
        raw_stdout = stdout_text
        denied_actions = []
        
        try:
            lines = stdout_text.strip().split('\n')
            data = json.loads(lines[-1])
            stdout_text = data.get("response", stdout_text)
            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens")
            tokens_out = usage.get("output_tokens")
            cached_tokens = usage.get("cache_read_tokens")
            turns = data.get("num_turns")
            secs = data.get("duration_seconds")
            status = data.get("status", "UNKNOWN")
            conv_id = data.get("conversation_id", "none")
            denied_actions = data.get("denied_actions", [])
            logging.info(f"event: agy exit (status={status}, seconds={secs}, tokens_in={tokens_in}, tokens_out={tokens_out})")
            
            if DRY_RUN:
                print(f"DRY RUN: agy JSON output:")
                print(json.dumps(data))
        except: pass
        
        update_record(key, {
            "end_time": datetime.now(timezone.utc).isoformat(),
            "exit_status": retcode,
            "model": model,
            "session_id": conv_id
        })
        
        if status != "SUCCESS" or not stdout_text.strip() or denied_actions:
            reason = "agy printed no valid report/2"
            if not stdout_text.strip(): reason = "agy response was empty"
            if status != "SUCCESS": reason = f"agy failed with status {status}"
            if denied_actions: reason = f"agy denied actions: {denied_actions}"
                
            details_content = f"status: {status}\nexit code: {retcode}\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_content = write_fallback_reply(d_id, rev, "declined", reason, done_whens, details_content, model, tokens_in, tokens_out, cached_tokens, turns, secs)
        elif retcode != 0 and retcode != 124:
            details_content = f"crashed with exit code {retcode}\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_content = write_fallback_reply(d_id, rev, "declined", "crashed", done_whens, details_content, model, tokens_in, tokens_out, cached_tokens, turns, secs)
        elif retcode == 124:
            details_content = f"timed out\nRaw stdout (last 2000 chars):\n{raw_stdout[-2000:]}"
            reply_content = write_fallback_reply(d_id, rev, "declined", "timed out", done_whens, details_content, model, tokens_in, tokens_out, cached_tokens, turns, secs)
        else:
            if DRY_RUN: print(f"DEBUG: stdout_text is {repr(stdout_text)}")
            reply_content = prepare_reply(d_id, rev, stdout_text, done_whens, model, tokens_in, tokens_out, cached_tokens, turns, secs, raw_stdout)
            
        # check mailcheck
        tmp_reply = f"/tmp/reply_{d_id}.md"
        with open(tmp_reply, "w") as f: f.write(reply_content)
        val_res = subprocess.run(["python3", "/tmp/mailcheck.py", "--report", tmp_reply], capture_output=True, text=True)
        if val_res.returncode != 0 and not DRY_RUN:
            details = f"mailcheck failed: {val_res.stdout}\nRaw reply:\n{reply_content}"
            reply_content = write_fallback_reply(d_id, rev, "declined", "mailcheck failed", done_whens, details, model, tokens_in, tokens_out, cached_tokens, turns, secs)
            with open(tmp_reply, "w") as f: f.write(reply_content)
            
        if DRY_RUN:
            print(f"DRY RUN: Reply content:\n{reply_content}")
            print(f"DRY RUN: Mailcheck output:\n{val_res.stdout}\n{val_res.stderr}")
            update_record(key, {"status": "done"})
        else:
            gh_issue_comment(number, reply_content)
            logging.info(f"event: report posted for {d_id} rev {rev}")
            
            # check blockers to determine label
            new_label = "qa:review"
            try:
                match = re.search(r'```ga\s*(\{.*?\})\s*```', reply_content, re.DOTALL)
                if match:
                    ga_data = json.loads(match.group(1))
                    for blk in ga_data.get("blockers", []):
                        if blk.get("kind") == "question":
                            new_label = "qa:blocked"
                            break
            except: pass
            
            gh_issue_edit(number, add_labels=[new_label], remove_labels=["qa:doing"])
            logging.info(f"event: label change for #{number} to {new_label}")
            update_record(key, {"status": "done"})

            # post usage comment
            if DRY_RUN is False:
                usage_comment = {"schema": "usage/1", "id": d_id, "rev": rev, "from": "VM_LOCAL", "conversation_id": conv_id, "input_tokens": tokens_in, "output_tokens": tokens_out, "cached_tokens": cached_tokens, "turns": turns, "seconds": secs}
                gh_issue_comment(number, f"```ga\n{json.dumps(usage_comment)}\n```")

    except Exception as e:
        import traceback
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(f"Worker exception for {key}:\n{tb}")
        if not DRY_RUN:
            gh_issue_comment(number, f"Exception in dispatcher worker:\n```\n{tb}\n```")
            gh_issue_edit(number, add_labels=["qa:review"], remove_labels=["qa:doing"])
        update_record(key, {"status": "declined"})

def fetch_and_checkout():
    if not Path("/tmp/mailcheck.py").exists() or not DRY_RUN:
        subprocess.run("cp /home/ubuntu/local_dispatcher/ops/flow/mailcheck.py /tmp/mailcheck.py", shell=True)

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
            
            if not work and not active_futures and not DRY_RUN:
                logging.info(f"event: poll result - 0 items")
            elif work:
                logging.info(f"event: poll result - {len(work)} pending items")
                
            for number, directive, key in work:
                if key not in active_futures and len(active_futures) < MAX_CONCURRENT_RUNS:
                    fut = executor.submit(worker_task, number, directive, key)
                    active_futures[key] = fut
                    
            if DRY_RUN:
                for fut in active_futures.values(): fut.result()
                break
                    
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
        if DRY_RUN: break
        
        time.sleep(60)

if __name__ == "__main__":
    main()
