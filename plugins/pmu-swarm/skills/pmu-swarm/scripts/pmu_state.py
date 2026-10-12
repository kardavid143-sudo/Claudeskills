#!/usr/bin/env python3
"""Local coordination ledger; no model/API calls. Python 3.9+ standard library."""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value),
            "IDs must contain 1-80 letters, digits, underscores or hyphens")
    return value


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def artifact_ok(task):
    path = task["artifact"]
    require(path and Path(path).is_file(), "Artifact is missing")
    require(digest(Path(path).read_bytes()) == task["artifact_hash"],
            "Artifact changed after submission")


class Ledger:
    def __init__(self, db):
        self.db = Path(db).resolve()
        require(self.db.is_file(), "Initialize a new ledger first")
        self.c = sqlite3.connect(str(self.db), timeout=15, isolation_level=None)
        self.c.row_factory = sqlite3.Row
        self.c.execute("PRAGMA foreign_keys=ON")
        self.c.execute("BEGIN IMMEDIATE")

    def run(self):
        return self.c.execute("SELECT * FROM run").fetchone()

    def active(self):
        require(self.run()["state"] == "active", "Run is not active")

    def task(self, task_id):
        row = self.c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        require(row is not None, "Unknown task")
        return row

    def event(self, action, actor, task_id=None, details=None):
        self.c.execute("INSERT INTO events(at,action,actor,task_id,details) VALUES(?,?,?,?,?)",
                       (time.time(), action, actor, task_id, encode(details or {})))

    def add(self, payload):
        self.active()
        task_id = identifier(payload["id"])
        pmu = identifier(payload["pmu"])
        require(payload.get("role") and payload.get("title") and payload.get("acceptance"),
                "role, title and acceptance are required")
        kind = payload.get("kind", "work")
        require(kind in ("plan", "work", "review", "final"), "Invalid task kind")
        deps = payload.get("dependencies", [])
        require(isinstance(deps, list) and len(deps) == len(set(deps)), "Invalid dependencies")
        for dep in deps:
            identifier(dep)
            require(dep != task_id, "Self-dependency")
            self.task(dep)  # Existing-only edges prevent cycles.
        attempts = payload.get("max_attempts", 3)
        require(type(attempts) is int and 1 <= attempts <= 10, "max_attempts must be 1-10")
        required = payload.get("required", True)
        require(type(required) is bool, "required must be boolean")
        scope = Path(self.run()["root"]) / "tasks" / task_id
        self.c.execute("""INSERT INTO tasks
            (id,pmu,role,title,acceptance,kind,deps,required,state,attempts,max_attempts,scope)
            VALUES(?,?,?,?,?,?,?,?,'pending',0,?,?)""",
                       (task_id, pmu, payload["role"], payload["title"], encode(payload["acceptance"]),
                        kind, encode(deps), int(required), attempts, str(scope)))
        scope.mkdir(parents=True, exist_ok=True)
        self.event("add", "director", task_id, payload)
        return {"task": task_id, "scope": str(scope)}

    def expire(self):
        for row in self.c.execute("SELECT * FROM tasks WHERE state='running' AND lease<=?",
                                  (time.time(),)).fetchall():
            state = "blocked" if row["attempts"] >= row["max_attempts"] else "pending"
            self.c.execute("UPDATE tasks SET state=?,token=NULL,lease=NULL WHERE id=?",
                           (state, row["id"]))
            self.event("lease_expired", "director", row["id"], {"state": state})

    def claim(self, task_id, worker, ttl, model):
        self.active()
        identifier(worker)
        require(1 <= ttl <= 3600, "Lease seconds must be 1-3600")
        task = self.task(task_id)
        require(task["state"] == "pending", "Task is not claimable")
        require(task["attempts"] < task["max_attempts"], "Attempt ceiling exhausted")
        inputs = {}
        for dep in json.loads(task["deps"]):
            source = self.task(dep)
            allowed = ("submitted", "accepted") if task["kind"] == "review" else ("accepted",)
            require(source["state"] in allowed, "Dependency is not ready: " + dep)
            artifact_ok(source)
            require(task["kind"] != "review" or source["owner"] != worker,
                    "Reviewer cannot review own work")
            inputs[dep] = {"artifact": source["artifact"], "hash": source["artifact_hash"]}
        run = self.run()
        require(run["calls"] < run["call_limit"], "Call ceiling exhausted")
        token = uuid.uuid4().hex
        expiry = time.time() + ttl
        self.c.execute("UPDATE run SET calls=calls+1")
        self.c.execute("""UPDATE tasks SET state='running',owner=?,token=?,lease=?,
            attempts=attempts+1,model=?,input_hashes=? WHERE id=?""",
                       (worker, token, expiry, model, encode(inputs), task_id))
        # Do not log lease tokens. Include only bounded, useful coordination facts.
        self.event("claim", worker, task_id, {"model": model, "expires": expiry, "inputs": inputs})
        return {"task": task_id, "token": token, "lease": expiry, "scope": task["scope"],
                "brief": str(Path(run["root"]) / "brief.json"), "brief_hash": run["brief_hash"],
                "dependencies": inputs, "calls": run["calls"] + 1, "call_limit": run["call_limit"]}

    def held(self, task_id, worker, token):
        self.active()
        task = self.task(task_id)
        require(task["state"] == "running" and task["owner"] == worker and task["token"] == token,
                "Invalid or obsolete claim token")
        require(task["lease"] > time.time(), "Lease expired; late result rejected")
        return task

    def heartbeat(self, task_id, worker, token, ttl):
        self.held(task_id, worker, token)
        require(1 <= ttl <= 3600, "Lease seconds must be 1-3600")
        expiry = time.time() + ttl
        self.c.execute("UPDATE tasks SET lease=? WHERE id=?", (expiry, task_id))
        self.event("heartbeat", worker, task_id, {"expires": expiry})
        return {"task": task_id, "lease": expiry}

    def submit(self, task_id, worker, token, source):
        task = self.held(task_id, worker, token)
        path = Path(source).resolve()
        scope = Path(task["scope"]).resolve()
        require(scope in path.parents and path.is_file(), "Artifact must be inside assigned task scope")
        require(path.stat().st_size <= 50 * 1024 * 1024, "Artifact exceeds 50 MiB limit")
        data = path.read_bytes()
        require(bool(data), "Empty artifact")
        target = Path(self.run()["root"]) / "submissions" / task_id
        target.mkdir(parents=True, exist_ok=True)
        snapshot = target / (uuid.uuid4().hex + path.suffix)
        # Exclusive file name plus transaction ensures one accepted submission per claim.
        with snapshot.open("xb") as handle:
            handle.write(data)
        sha = digest(data)
        self.c.execute("""UPDATE tasks SET state='submitted',artifact=?,artifact_hash=?,
            token=NULL,lease=NULL WHERE id=?""", (str(snapshot), sha, task_id))
        self.event("submit", worker, task_id, {"artifact": str(snapshot), "hash": sha})
        return {"task": task_id, "artifact": str(snapshot), "hash": sha, "status": "submitted"}

    def fail(self, task_id, worker, token, reason):
        task = self.held(task_id, worker, token)
        require(reason.strip(), "Failure reason is required")
        state = "blocked" if task["attempts"] >= task["max_attempts"] else "pending"
        self.c.execute("UPDATE tasks SET state=?,token=NULL,lease=NULL WHERE id=?", (state, task_id))
        self.event("failed", worker, task_id, {"reason": reason, "state": state})
        return {"task": task_id, "state": state}

    def review(self, task_id, reviewer, decision, report_id, payload):
        self.active()
        identifier(reviewer)
        task = self.task(task_id)
        require(task["state"] == "submitted", "Only submitted tasks can be reviewed")
        require(reviewer != task["owner"], "Author cannot accept own work")
        artifact_ok(task)
        require(payload.get("note"), "Review note is required")
        findings = payload.get("unresolved", [])
        require(isinstance(findings, list), "unresolved must be a list")
        for finding in findings:
            require(isinstance(finding, dict) and finding.get("severity") in ("critical", "major", "minor")
                    and finding.get("description"), "Each finding needs severity and description")
        if task["kind"] != "review":
            require(report_id is not None, "An independent review task report is required")
            report = self.task(report_id)
            require(report["kind"] == "review" and report["state"] == "accepted",
                    "Director must accept the review report before accepting its target")
            require(report["owner"] == reviewer, "Reviewer must own the report")
            captured = json.loads(report["input_hashes"] or "{}").get(task_id)
            require(captured and captured["hash"] == task["artifact_hash"],
                    "Review report does not cover current task artifact")
            artifact_ok(report)
            payload = dict(payload, report_snapshot={"artifact": report["artifact"],
                                                    "hash": report["artifact_hash"]})
        else:
            require(reviewer == "director", "Director must adjudicate review reports")
        if decision == "accept":
            require(not any(f["severity"] in ("critical", "major") for f in findings),
                    "Unresolved critical/major findings block acceptance")
            state = "accepted"
        elif decision == "revise":
            state = "pending" if task["attempts"] < task["max_attempts"] else "blocked"
        else:
            state = "blocked"
        self.c.execute("UPDATE tasks SET state=? WHERE id=?", (state, task_id))
        self.c.execute("INSERT INTO reviews(task_id,reviewer,decision,report_id,artifact_hash,payload,at) "
                       "VALUES(?,?,?,?,?,?,?)", (task_id, reviewer, decision, report_id,
                                                 task["artifact_hash"], encode(payload), time.time()))
        self.event("review", reviewer, task_id, {"decision": decision, "report": report_id,
                                                "hash": task["artifact_hash"], "findings": findings})
        return {"task": task_id, "state": state}

    def control(self, action, payload):
        run = self.run()
        require(run["state"] not in ("cancelled", "completed"), "Run is terminal")
        if action == "resume":
            require(run["state"] == "paused", "Only a paused run can resume")
            state = "active"
        elif action in ("pause", "cancel"):
            state = "paused" if action == "pause" else "cancelled"
            for task in self.c.execute("SELECT * FROM tasks WHERE state='running'").fetchall():
                target = "pending" if task["attempts"] < task["max_attempts"] else "blocked"
                self.c.execute("UPDATE tasks SET state=?,token=NULL,lease=NULL WHERE id=?",
                               (target, task["id"]))
        else:
            self.active()
            require(payload.get("passed") is True and payload.get("note"), "Acceptance checklist required")
            require(not payload.get("unresolved"), "Unresolved issues prevent completion")
            tasks = self.c.execute("SELECT * FROM tasks WHERE required=1").fetchall()
            require(bool(tasks) and all(t["state"] == "accepted" for t in tasks),
                    "Every required task must be accepted")
            require(not self.c.execute("SELECT 1 FROM tasks WHERE state='running'").fetchone(),
                    "Stop live optional workers before completing")
            for task in self.c.execute("SELECT * FROM tasks WHERE state='accepted'").fetchall():
                artifact_ok(task)
                for source in json.loads(task["input_hashes"] or "{}").values():
                    path = Path(source["artifact"])
                    require(path.is_file() and digest(path.read_bytes()) == source["hash"],
                            "Accepted task dependency snapshot is missing or changed")
            state = "completed"
        self.c.execute("UPDATE run SET state=?", (state,))
        self.event(action, "director", details=payload)
        return {"state": state}

    def status(self):
        run = dict(self.run())
        run.pop("brief_json")
        tasks = [dict(r) for r in self.c.execute("SELECT * FROM tasks ORDER BY rowid")]
        for task in tasks:
            task.pop("token")
            task["dependencies"] = json.loads(task.pop("deps"))
            task["expired"] = task["state"] == "running" and task["lease"] <= time.time()
        return {"run": run, "tasks": tasks}

    def events(self):
        return [dict(r) for r in self.c.execute("SELECT * FROM events ORDER BY seq")]


SCHEMA = """
CREATE TABLE run(id TEXT PRIMARY KEY,root TEXT NOT NULL,brief_json TEXT NOT NULL,
 brief_hash TEXT NOT NULL,state TEXT NOT NULL,call_limit INTEGER NOT NULL,calls INTEGER NOT NULL DEFAULT 0);
CREATE TABLE tasks(id TEXT PRIMARY KEY,pmu TEXT NOT NULL,role TEXT NOT NULL,title TEXT NOT NULL,
 acceptance TEXT NOT NULL,kind TEXT NOT NULL,deps TEXT NOT NULL,required INTEGER NOT NULL,
 state TEXT NOT NULL,attempts INTEGER NOT NULL,max_attempts INTEGER NOT NULL,scope TEXT NOT NULL,
 owner TEXT,token TEXT,lease REAL,model TEXT,input_hashes TEXT,artifact TEXT,artifact_hash TEXT);
CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT,at REAL NOT NULL,action TEXT NOT NULL,
 actor TEXT NOT NULL,task_id TEXT,details TEXT NOT NULL);
CREATE TABLE reviews(seq INTEGER PRIMARY KEY AUTOINCREMENT,task_id TEXT NOT NULL,
 reviewer TEXT NOT NULL,decision TEXT NOT NULL,report_id TEXT,artifact_hash TEXT NOT NULL,
 payload TEXT NOT NULL,at REAL NOT NULL);
CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
"""


def initialize(db, brief, call_limit):
    require(isinstance(brief, dict), "Brief must be an object")
    for key in ("goal", "intent", "inputs", "sources", "constraints", "acceptance", "assumptions"):
        require(key in brief, "Missing brief field: " + key)
    require(isinstance(brief["goal"], str) and brief["goal"].strip(), "Goal is required")
    require(isinstance(brief["intent"], str) and brief["intent"].strip(), "Intent is required")
    require(bool(brief["acceptance"]), "Acceptance criteria are required")
    require(call_limit > 0, "Call limit must be positive")
    db = Path(db).absolute()
    require(not db.exists() and not db.parent.exists(), "Use a new, unique run directory")
    db.parent.mkdir(parents=True)
    encoded = encode(brief)
    sha = digest(encoded.encode("utf-8"))
    c = sqlite3.connect(str(db), isolation_level=None)
    try:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(SCHEMA)
        c.execute("BEGIN IMMEDIATE")
        c.execute("INSERT INTO run(id,root,brief_json,brief_hash,state,call_limit) VALUES(?,?,?,?,?,?)",
                  (uuid.uuid4().hex, str(db.parent.resolve()), encoded, sha, "active", call_limit))
        c.execute("INSERT INTO events(at,action,actor,details) VALUES(?,?,?,?)",
                  (time.time(), "init", "director", encode({"brief_hash": sha, "call_limit": call_limit})))
        (db.parent / "brief.json").write_text(encoded, encoding="utf-8")
        c.commit()
    finally:
        c.close()
    return {"db": str(db), "brief_hash": sha, "call_limit": call_limit}


def payload():
    value = json.load(sys.stdin)
    require(isinstance(value, dict), "JSON input must be an object")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Absolute ledger path in a unique new run directory")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init"); p.add_argument("--call-limit", type=int, default=12)
    sub.add_parser("add")
    p = sub.add_parser("claim")
    p.add_argument("task"); p.add_argument("--worker", required=True)
    p.add_argument("--ttl", type=int, default=900); p.add_argument("--model", default="host-default")
    for name in ("heartbeat", "submit", "fail"):
        p = sub.add_parser(name); p.add_argument("task")
        p.add_argument("--worker", required=True); p.add_argument("--token", required=True)
        if name == "heartbeat": p.add_argument("--ttl", type=int, default=900)
        elif name == "submit": p.add_argument("--artifact", required=True)
        else: p.add_argument("--reason", required=True)
    p = sub.add_parser("review"); p.add_argument("task"); p.add_argument("--reviewer", required=True)
    p.add_argument("--decision", choices=("accept", "revise", "reject"), required=True)
    p.add_argument("--report")
    for name in ("status", "events", "pause", "resume", "cancel", "complete"):
        sub.add_parser(name)
    args = parser.parse_args()
    ledger = None
    try:
        if args.command == "init":
            result = initialize(args.db, payload(), args.call_limit)
        else:
            ledger = Ledger(args.db)
            # Detect tampered canonical brief before every resumed operation.
            run = ledger.run()
            require(digest((Path(run["root"]) / "brief.json").read_bytes()) == run["brief_hash"],
                    "Canonical brief changed; create a successor run")
            if args.command == "add": result = ledger.add(payload())
            elif args.command == "claim":
                ledger.active()
                ledger.expire()
                ledger.c.commit()  # Persist expiry even if the new claim is rejected.
                ledger.c.execute("BEGIN IMMEDIATE")
                result = ledger.claim(args.task, args.worker, args.ttl, args.model)
            elif args.command == "heartbeat": result = ledger.heartbeat(args.task, args.worker, args.token, args.ttl)
            elif args.command == "submit": result = ledger.submit(args.task, args.worker, args.token, args.artifact)
            elif args.command == "fail": result = ledger.fail(args.task, args.worker, args.token, args.reason)
            elif args.command == "review": result = ledger.review(args.task, args.reviewer, args.decision,
                                                                    args.report, payload())
            elif args.command == "status": result = ledger.status()
            elif args.command == "events": result = ledger.events()
            else: result = ledger.control(args.command, payload() if args.command == "complete" else {})
            ledger.c.commit()
        print(encode(result))
    except (ValueError, KeyError, OSError, sqlite3.Error, TypeError) as exc:
        if ledger: ledger.c.rollback()
        print(encode({"error": str(exc)}), file=sys.stderr)
        return 1
    finally:
        if ledger: ledger.c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
