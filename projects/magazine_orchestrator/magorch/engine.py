import concurrent.futures
import copy
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from magorch import contracts
from magorch.store import ArtifactStore
from magorch.graph import PlanError, topological_order, descendants

class Engine:
    def __init__(self, project_dir, agents, *, max_concurrent=4, validators=None, project_id=None):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.agents = agents
        self.max_concurrent = max_concurrent
        self.validators = validators or {}
        self.project_id = project_id
        
        self.store = ArtifactStore(self.project_dir / "artifacts")
        self.state_dir = self.project_dir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.project_dir / "events.jsonl"
        
        self.tasks = {}
        self.results = {}
        self.unrouted = []
        self._lock = threading.Lock()
        
        self._load_state()
        
    def _load_state(self):
        for path in self.state_dir.glob("task_*.json"):
            task = json.loads(path.read_text(encoding="utf-8"))
            if task.get("status") == "running":
                task["status"] = "ready"
            self.tasks[task["task_id"]] = task
            
        for path in self.state_dir.glob("result_*.json"):
            res = json.loads(path.read_text(encoding="utf-8"))
            tid = path.name[len("result_"):-5]
            self.results[tid] = res
            
    def _save_task(self, task):
        path = self.state_dir / f"task_{task['task_id']}.json"
        path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
        
    def _save_result(self, task_id, result):
        path = self.state_dir / f"result_{task_id}.json"
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        
    def _log_event(self, event_name, **kwargs):
        ev = {"ts": datetime.now(timezone.utc).isoformat(), "event": event_name}
        ev.update(kwargs)
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev) + "\n")
            
    def events(self):
        if not self.events_file.exists():
            return []
        res = []
        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    res.append(json.loads(line))
        return res

    def add_task(self, task):
        contracts.validate(task, "agent_task/1")
        tid = task["task_id"]
        
        with self._lock:
            if tid in self.tasks:
                t1 = {k:v for k,v in self.tasks[tid].items() if k not in ("status", "attempt", "repair_context", "revision_notes")}
                t2 = {k:v for k,v in task.items() if k not in ("status", "attempt", "repair_context", "revision_notes")}
                if t1 != t2:
                    raise contracts.ContractError(f"Task {tid} already exists with different content")
                return tid
            
            # Check cycles
            edges = {t: self.tasks[t].get("dependencies", []) for t in self.tasks}
            edges[tid] = task.get("dependencies", [])
            topological_order(edges, allow_missing=True)
            
            self.tasks[tid] = copy.deepcopy(task)
            self._save_task(self.tasks[tid])
            
        self._log_event("task_added", task_id=tid)
        return tid
        
    def cancel(self, task_id):
        with self._lock:
            t = self.tasks.get(task_id)
            if not t:
                return
            if t["status"] in ("pending", "ready"):
                t["status"] = "cancelled"
                self._save_task(t)
                self._log_event("task_cancelled", task_id=task_id)

    def status(self, task_id):
        with self._lock:
            return self.tasks.get(task_id, {}).get("status")
            
    def result(self, task_id):
        with self._lock:
            return copy.deepcopy(self.results.get(task_id))
            
    def _get_idempotency_key(self, task, bound_inputs):
        h = hashlib.sha256()
        h.update(task.get("agent_role", "").encode("utf-8"))
        h.update((task.get("objective") or "").encode("utf-8"))
        h.update(json.dumps(task.get("output_contract", {}), sort_keys=True).encode("utf-8"))
        # Sort bound inputs
        for inp in sorted(bound_inputs, key=lambda x: x["artifact_id"]):
            h.update(f"{inp['artifact_id']}:{inp['version']}".encode("utf-8"))
        h.update(json.dumps(task.get("revision_notes", []), sort_keys=True).encode("utf-8"))
        return h.hexdigest()

    def _bind_inputs(self, task):
        bound = []
        for inp in task.get("inputs", []):
            aid = inp["artifact_id"]
            ver = inp.get("version")
            if ver is None:
                ver = self.store.latest_version(aid)
            if ver is None:
                return None # missing
            bound.append({"artifact_id": aid, "version": ver})
        return bound
        
    def _execute_task(self, tid):
        with self._lock:
            task = self.tasks[tid]
            task["status"] = "running"
            task["attempt"] = task.get("attempt", 0) + 1
            self._save_task(task)
            self._log_event("task_dispatched", task_id=tid)
            
            bound_inputs = self._bind_inputs(task)
            
        if bound_inputs is None:
            with self._lock:
                task["status"] = "failed"
                self._save_task(task)
                res = {
                    "schema": "agent_result/1",
                    "task_id": tid,
                    "status": "failed",
                    "outputs": [],
                    "issues": [],
                    "unresolved_questions": [],
                    "provenance": {"attempts": task["attempt"], "input_versions": [], "agent_role": task["agent_role"], "model_provider": None, "model_id": None},
                    "failure_reason": "missing_input"
                }
                self.results[tid] = res
                self._save_result(tid, res)
                self._log_event("task_failed", task_id=tid)
            return
            
        inputs = {}
        for b in bound_inputs:
            inputs[b["artifact_id"]] = self.store.get(b["artifact_id"], b["version"])
            
        agent_role = task["agent_role"]
        agent = self.agents.get(agent_role)
        if not agent:
            with self._lock:
                task["status"] = "failed"
                self._save_task(task)
                res = {
                    "schema": "agent_result/1",
                    "task_id": tid,
                    "status": "failed",
                    "outputs": [],
                    "issues": [],
                    "unresolved_questions": [],
                    "provenance": {"attempts": task["attempt"], "input_versions": bound_inputs, "agent_role": task["agent_role"], "model_provider": None, "model_id": None},
                    "failure_reason": f"missing agent role {agent_role}"
                }
                self.results[tid] = res
                self._save_result(tid, res)
                self._log_event("task_failed", task_id=tid)
            return

        timeout = task.get("constraints", {}).get("timeout_seconds", 3600)
        max_attempts = task.get("constraints", {}).get("max_attempts", 1)
        
        # We need to run agent(task, inputs) but catch exceptions and handle timeouts.
        # However, to discard late results properly, we run it and wait up to timeout.
        result_container = {}
        def _run_agent():
            try:
                task_for_agent = copy.deepcopy(task)
                if bound_inputs is not None:
                    task_for_agent["inputs"] = bound_inputs
                result_container["result"] = agent(task_for_agent, copy.deepcopy(inputs))
            except Exception as e:
                result_container["error"] = e
                
        t = threading.Thread(target=_run_agent)
        t.start()
        t.join(timeout)
        
        with self._lock:
            # check if cancelled
            if self.tasks[tid]["status"] == "cancelled":
                return
                
            is_timeout = False
            failed = False
            failure_reason = ""
            outputs = []
            
            if t.is_alive():
                is_timeout = True
                failed = True
                failure_reason = "timeout"
            elif "error" in result_container:
                failed = True
                failure_reason = str(type(result_container["error"]).__name__) + ": " + str(result_container["error"])
            else:
                agent_res = result_container["result"]
                # Validate output
                out_contract = task.get("output_contract", {})
                expected_ids = out_contract.get("artifact_ids")
                out_schema = out_contract.get("schema")
                
                got_ids = []
                for art in agent_res.get("artifacts", []):
                    aid = art["artifact_id"]
                    payload = art["payload"]
                    try:
                        # Before checking schema, make sure it has one
                        if "schema" not in payload and out_schema:
                            payload["schema"] = out_schema
                        contracts.validate(payload, out_schema)
                        got_ids.append(aid)
                    except contracts.ContractError as e:
                        failed = True
                        failure_reason = "invalid_output"
                        if "repair_context" not in task:
                            task["repair_context"] = {}
                        task["repair_context"]["errors"] = e.errors
                        break
                        
                if not failed and expected_ids is not None:
                    if sorted(expected_ids) != sorted(got_ids):
                        failed = True
                        failure_reason = "invalid_output: artifact_ids mismatch"
                        if "repair_context" not in task:
                            task["repair_context"] = {}
                        task["repair_context"]["errors"] = ["artifact_ids mismatch"]
                        
                if not failed:
                    # store artifacts
                    for art in agent_res.get("artifacts", []):
                        aid = art["artifact_id"]
                        stored_res = self.store.put(aid, art["artifact_type"], art["payload"], produced_by=tid, inputs=bound_inputs)
                        self._log_event("artifact_stored", artifact_id=aid)
                        
                        # Mark stale consumers
                        for c_tid, c_task in self.tasks.items():
                            if c_task["status"] == "succeeded":
                                c_res = self.results.get(c_tid, {})
                                c_iv = c_res.get("provenance", {}).get("input_versions", [])
                                for civ in c_iv:
                                    if civ["artifact_id"] == aid and civ["version"] < stored_res["version"]:
                                        c_task["status"] = "stale"
                                        self._save_task(c_task)
                                        self._log_event("task_stale", task_id=c_tid)
                        
                        out_info = {
                            "artifact_id": aid,
                            "schema": payload.get("schema", "unknown/1"),
                            "version": self.store.latest_version(aid),
                            "validation_status": "passed"
                        }
                        outputs.append(out_info)

            if failed:
                if task["attempt"] >= max_attempts:
                    task["status"] = "timed_out" if is_timeout else "failed"
                    self._save_task(task)
                    res = {
                        "schema": "agent_result/1",
                        "task_id": tid,
                        "status": "failed",
                        "outputs": [],
                        "issues": [],
                        "unresolved_questions": [],
                        "provenance": {"attempts": task["attempt"], "input_versions": bound_inputs, "agent_role": task["agent_role"], "model_provider": None, "model_id": None},
                        "failure_reason": failure_reason
                    }
                    if failure_reason == "invalid_output" and "repair_context" in task:
                        res["validation_errors"] = task["repair_context"]["errors"]
                    elif "invalid_output" in failure_reason and "repair_context" in task:
                        res["validation_errors"] = task["repair_context"]["errors"]
                    if not is_timeout and "agent_res" in locals():
                        res["provenance"].update(agent_res.get("provenance", {}))
                    self.results[tid] = res
                    self._save_result(tid, res)
                    self._log_event("task_timed_out" if is_timeout else "task_failed", task_id=tid)
                else:
                    # retry
                    task["status"] = "ready"
                    self._save_task(task)
                    self._log_event("task_retry", task_id=tid)
            else:
                task["status"] = "succeeded"
                self._save_task(task)
                res = {
                    "schema": "agent_result/1",
                    "task_id": tid,
                    "status": "completed",
                    "outputs": outputs,
                    "issues": agent_res.get("issues", []),
                    "unresolved_questions": agent_res.get("unresolved_questions", []),
                    "provenance": {"attempts": task["attempt"], "input_versions": bound_inputs, "agent_role": task["agent_role"], "model_provider": None, "model_id": None}
                }
                res["provenance"].update(agent_res.get("provenance", {}))
                self.results[tid] = res
                self._save_result(tid, res)
                self._log_event("task_succeeded", task_id=tid)

    def run(self):
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent)
        futures = {}
        
        while True:
            runnable = []
            with self._lock:
                edges = {t: self.tasks[t].get("dependencies", []) for t in self.tasks}
                try:
                    for d in edges.values():
                        for dep in d:
                            if dep not in edges:
                                raise PlanError(f"Unknown dependency {dep}")
                    order = topological_order(edges)
                except PlanError:
                    # Mark all as blocked/failed? Tests expect PlanError to be raised
                    raise
                    
                for tid in order:
                    task = self.tasks[tid]
                    if task["status"] in ("succeeded", "failed", "timed_out", "cancelled", "running"):
                        continue
                        
                    # Check dependencies
                    deps = task.get("dependencies", [])
                    dep_statuses = [self.tasks.get(d, {}).get("status") for d in deps]
                    
                    if any(s in ("failed", "timed_out", "cancelled", "blocked") for s in dep_statuses):
                        task["status"] = "blocked"
                        self._save_task(task)
                        self._log_event("task_blocked", task_id=tid)
                        continue
                        
                    if all(s == "succeeded" for s in dep_statuses):
                        if task["status"] in ("pending", "ready", "stale"):
                            runnable.append(tid)

            if not runnable and not futures:
                break
                
            for tid in runnable:
                with self._lock:
                    if self.tasks[tid]["status"] == "stale":
                        # handle revalidate
                        on_change = self.tasks[tid].get("constraints", {}).get("on_upstream_change", "rerun")
                        if on_change == "revalidate" and self.tasks[tid]["agent_role"] in self.validators:
                            # Revalidate
                            bound_inputs = self._bind_inputs(self.tasks[tid])
                            inputs = {}
                            for b in bound_inputs:
                                inputs[b["artifact_id"]] = self.store.get(b["artifact_id"], b["version"])
                            task_for_val = copy.deepcopy(self.tasks[tid])
                            task_for_val["inputs"] = bound_inputs
                            errs = self.validators[self.tasks[tid]["agent_role"]](
                                task_for_val,
                                inputs,
                                copy.deepcopy(self.results.get(tid))
                            )
                            if errs:
                                if "repair_context" not in self.tasks[tid]:
                                    self.tasks[tid]["repair_context"] = {}
                                self.tasks[tid]["repair_context"]["errors"] = errs
                                self.tasks[tid]["status"] = "ready"
                                self._save_task(self.tasks[tid])
                            else:
                                self.tasks[tid]["status"] = "succeeded"
                                self._save_task(self.tasks[tid])
                                self._log_event("task_revalidated", task_id=tid)
                                # update input versions in result
                                if tid in self.results:
                                    self.results[tid]["provenance"]["input_versions"] = bound_inputs
                                    self._save_result(tid, self.results[tid])
                                continue
                                
                    if self.tasks[tid]["status"] in ("succeeded", "running"):
                        continue
                        
                    self.tasks[tid]["status"] = "running"
                    self.tasks[tid]["attempt"] = self.tasks[tid].get("attempt", 0) # clear or keep attempt? keep for retries
                    self._save_task(self.tasks[tid])
                
                futures[tid] = pool.submit(self._execute_task, tid)
                
            if futures:
                done, _ = concurrent.futures.wait(futures.values(), return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    # Find which tid it was
                    for k, v in list(futures.items()):
                        if v == f:
                            del futures[k]
        
        pool.shutdown()
        with self._lock:
            return {tid: self.tasks[tid]["status"] for tid in self.tasks}

    def revise_artifact(self, artifact_id, payload, *, artifact_type, reason, inputs=()):
        res = self.store.put(artifact_id, artifact_type, payload, produced_by="orchestrator:revision", inputs=inputs)
        self._log_event("artifact_revised", artifact_id=artifact_id)
        
        # Mark stale
        with self._lock:
            edges = {t: self.tasks[t].get("dependencies", []) for t in self.tasks}
            rev = {}
            for n, deps in edges.items():
                for d in deps:
                    rev.setdefault(d, []).append(n)
                    
            for tid, t in self.tasks.items():
                if t["status"] == "succeeded":
                    res_info = self.results.get(tid, {})
                    iv = res_info.get("provenance", {}).get("input_versions", [])
                    for i in iv:
                        if i["artifact_id"] == artifact_id and i["version"] < res["version"]:
                            t["status"] = "stale"
                            self._save_task(t)
                            self._log_event("task_stale", task_id=tid)
        return res

    def route_findings(self, qa_report):
        contracts.validate(qa_report, "qa_report/1")
        routed = []
        
        with self._lock:
            for check in qa_report.get("checks", []):
                if check.get("severity") == "blocking" and check.get("status") == "failed":
                    aid = check.get("affected_artifact_id")
                    if not aid:
                        continue
                        
                    # Find producing task
                    producer_tid = None
                    for tid, res in self.results.items():
                        if res.get("status") == "completed":
                            for out in res.get("outputs", []):
                                if out["artifact_id"] == aid:
                                    producer_tid = tid
                                    break
                        if producer_tid:
                            break
                            
                    if not producer_tid:
                        self.unrouted.append(check.get("check_id"))
                        continue
                        
                    task = self.tasks[producer_tid]
                    rev_limit = task.get("constraints", {}).get("revision_limit", 1)
                    
                    notes = task.get("revision_notes", [])
                    if len(notes) >= rev_limit:
                        task["status"] = "failed"
                        self._save_task(task)
                        if producer_tid in self.results:
                            self.results[producer_tid]["status"] = "failed"
                            self.results[producer_tid]["failure_reason"] = f"revision_limit exceeded"
                            self._save_result(producer_tid, self.results[producer_tid])
                        self._log_event("escalated", task_id=producer_tid)
                    else:
                        notes.append({
                            "finding_id": check.get("check_id"),
                            "message": check.get("message", ""),
                            "recommended_action": check.get("recommended_action", ""),
                            "report_id": qa_report.get("report_id")
                        })
                        task["revision_notes"] = notes
                        task["status"] = "stale"
                        task["attempt"] = 0
                        if "repair_context" in task:
                            del task["repair_context"]
                        self._save_task(task)
                        self._log_event("finding_routed", task_id=producer_tid)
                        routed.append(producer_tid)
                        
        return list(set(routed))
