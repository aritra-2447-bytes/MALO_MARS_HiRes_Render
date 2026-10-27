"""Asynchronous NASA PDS GDS job control.

Wraps the ODE Geosciences Data Services REST endpoint (`livegds`) with an
in-memory job registry.  The UI can submit a background MOLA PEDR query,
poll queue status, and request an abort.  When GDS answers synchronously the
job is marked complete immediately; when it returns a remote job id the
manager polls `query=status` and exposes the queue state.
"""

import json
import threading
import time
import urllib.parse
import urllib.request

GDS_BASE = "https://oderest.rsl.wustl.edu/livegds/"


class GDSJobManager:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()
        self._counter = 0

    def _new_id(self):
        with self._lock:
            self._counter += 1
            return f"gds-{int(time.time())}-{self._counter:03d}"

    def submit(self, params):
        job_id = self._new_id()
        job = {
            "id": job_id,
            "state": "queued",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "started_utc": None,
            "finished_utc": None,
            "params": {k: v for k, v in params.items() if k not in ("action",)},
            "remote_job_id": None,
            "status_note": "Queued for NASA PDS GDS.",
            "result": None,
            "error": None,
            "abort_requested": False,
            "attempts": 0,
        }
        with self._lock:
            self._jobs[job_id] = job
        thread = threading.Thread(target=self._run, args=(job_id, params), daemon=True)
        thread.start()
        return job

    def _url_for_submit(self, params):
        q = {
            "query": params.get("query", "molapedr"),
            "results": params.get("results", "v"),
            "output": params.get("output", "json"),
            "asynch": "t",
        }
        for k in ("minlat", "maxlat", "westernlon", "easternlon", "minlon", "maxlon", "product", "target"):
            if k in params:
                q[k] = params[k]
        return GDS_BASE + "?" + urllib.parse.urlencode(q)

    def _get_json(self, url, timeout=45):
        req = urllib.request.Request(url, headers={"User-Agent": "ARES-OS/1.0 (Mars Mission Control)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _run(self, job_id, params):
        job = self._jobs.get(job_id)
        if not job:
            return
        with self._lock:
            job["state"] = "running"
            job["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job["status_note"] = "Submitting query to NASA PDS GDS..."
        try:
            url = self._url_for_submit(params)
            data = self._get_json(url, timeout=60)
            job["attempts"] += 1
            gds = data.get("GDSResults", {})
            status = str(gds.get("Status", "")).lower()
            # Remote job handle, if GDS chose to queue the request.
            remote = (
                gds.get("JobId") or gds.get("JobID") or gds.get("jobid")
                or gds.get("Job", {}).get("JobId") if isinstance(gds.get("Job"), dict) else None
            )
            if remote:
                with self._lock:
                    job["remote_job_id"] = str(remote)
                    job["state"] = "queued"
                    job["status_note"] = f"NASA GDS remote job {remote} queued."
                self._poll_remote(job, str(remote))
                return
            if "error" in {k.lower() for k in gds.keys()} and not gds.get("ResultFiles"):
                raise RuntimeError(gds.get("Error", "GDS returned an error"))
            with self._lock:
                job["state"] = "completed"
                job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["status_note"] = (
                    gds.get("StateSummary", {}).get("StatusNote")
                    or "GDS query completed."
                )
                job["result"] = self._summarize(gds)
        except Exception as exc:
            with self._lock:
                job["state"] = "failed"
                job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["error"] = str(exc)
                job["status_note"] = f"GDS job failed: {exc}"

    def _poll_remote(self, job, remote_id):
        deadline = time.time() + 600
        while time.time() < deadline:
            if job.get("abort_requested"):
                self._abort_remote(job, remote_id)
                return
            time.sleep(3.0)
            try:
                url = GDS_BASE + "?" + urllib.parse.urlencode({
                    "query": "status", "jobid": remote_id, "output": "json",
                })
                data = self._get_json(url, timeout=20)
                gds = data.get("GDSResults", {})
                state = str(gds.get("StateSummary", {}).get("State", gds.get("Status", "")))
                note = gds.get("StateSummary", {}).get("StatusNote", "")
                with self._lock:
                    job["status_note"] = f"{state}: {note}".strip(": ")
                    job["state"] = "running" if state.lower() in ("running", "queued", "processing") else job["state"]
                    if state.lower() in ("finished", "complete", "completed", "success"):
                        job["state"] = "completed"
                        job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        job["result"] = self._summarize(gds)
                        return
            except Exception as exc:
                with self._lock:
                    job["status_note"] = f"Status poll warning: {exc}"
        with self._lock:
            if job["state"] not in ("completed", "aborted"):
                job["state"] = "timeout"
                job["status_note"] = "Remote GDS job did not finish within 10 minutes."

    def _summarize(self, gds):
        files = gds.get("ResultFiles", {}).get("ResultFile", [])
        if isinstance(files, dict):
            files = [files]
        state = gds.get("StateSummary", {})
        return {
            "count": gds.get("Count"),
            "state": state.get("State"),
            "status_note": state.get("StatusNote"),
            "valid_till": gds.get("ResultFiles", {}).get("ValidTill"),
            "files": [
                {"url": f.get("URL"), "size_kb": f.get("SizeKB")}
                for f in files if isinstance(f, dict)
            ],
            "query_summary": gds.get("QuerySummary", {}),
        }

    def _abort_remote(self, job, remote_id):
        try:
            url = GDS_BASE + "?" + urllib.parse.urlencode({
                "query": "status", "jobid": remote_id, "abort": "t", "output": "json",
            })
            data = self._get_json(url, timeout=20)
            with self._lock:
                job["state"] = "aborted"
                job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["status_note"] = f"Abort requested. {data.get('GDSResults', {}).get('StateSummary', {}).get('StatusNote', '')}".strip()
        except Exception as exc:
            with self._lock:
                job["state"] = "aborted"
                job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["status_note"] = f"Aborted locally; remote abort warning: {exc}"

    def abort(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job["abort_requested"] = True
            if job["state"] in ("queued", "running"):
                job["state"] = "aborting"
                job["status_note"] = "Abort requested by operator."
        if job.get("remote_job_id"):
            self._abort_remote(job, job["remote_job_id"])
        else:
            with self._lock:
                job["state"] = "aborted"
                job["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["status_note"] = "Job aborted by operator before GDS returned."
        return job

    def get(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list(self):
        with self._lock:
            return [dict(j) for j in sorted(self._jobs.values(), key=lambda x: x["created_utc"], reverse=True)]


MANAGER = GDSJobManager()
