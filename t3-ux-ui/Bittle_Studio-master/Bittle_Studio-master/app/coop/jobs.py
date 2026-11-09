"""Background jobs: long simulations (traverse tests, batch experiments) in separate processes, with progress.

Each job is a list of independent runs. They go to a pool of worker processes, so several runs use several CPU cores
at once and the running simulation and the dashboard stay responsive. A job keeps every run's result as it comes in;
when the last run is in, the job's finish function turns them into the job result.
"""
import multiprocessing
import os
import threading
import time
import traceback
import uuid
from concurrent.futures import CancelledError, ProcessPoolExecutor

MAX_JOBS = 20            # finished jobs kept for the dashboard
WORKERS = max(1, min(8, (os.cpu_count() or 2) - 1))


class Jobs:
    def __init__(self, workers=WORKERS):
        self.workers = workers
        self.lock = threading.Lock()
        self.jobs = {}
        self._pool = None

    def pool(self):
        if self._pool is None:
            # spawn: a fresh interpreter per worker, as on Windows; nothing of the server's Bullet world is copied
            self._pool = ProcessPoolExecutor(self.workers, mp_context=multiprocessing.get_context('spawn'))
        return self._pool

    def submit(self, kind, title, runs, finish=None, info=None):
        """runs: list of (label, function, args) with a picklable top-level function; returns the job id."""
        job_id = uuid.uuid4().hex[:12]
        job = {'id': job_id, 'kind': kind, 'title': title, 'status': 'running', 'total': len(runs), 'done': 0,
               'failed': 0, 'started': time.time(), 'finished': None, 'info': info or {},
               'runs': [{'label': label, 'status': 'queued'} for label, _, _ in runs], 'result': None, 'error': None}
        with self.lock:
            self.jobs[job_id] = job
            self._trim()
        futures = []
        for index, (label, function, args) in enumerate(runs):
            future = self.pool().submit(function, *args)
            future.add_done_callback(lambda f, i=index: self._done(job_id, i, f, finish))
            futures.append(future)
        job['_futures'] = futures
        return job_id

    def _done(self, job_id, index, future, finish):
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                return
            run = job['runs'][index]
            try:
                run.update(status='done', result=future.result())
            except CancelledError:
                run.update(status='cancelled')
            except Exception as error:  # a failing run is reported with the others, never fatal for the job
                run.update(status='error', error=f'{type(error).__name__}: {error}')
                job['failed'] += 1
            job['done'] += 1
            if job['done'] < job['total']:
                return
            job['finished'] = time.time()
            if job['status'] == 'running':
                job['status'] = 'done'
            results = [r.get('result') for r in job['runs']]
        if finish:
            try:
                outcome = finish(job, results)
            except Exception:
                outcome, error = None, traceback.format_exc(limit=3)
            else:
                error = None
            with self.lock:
                job['result'], job['error'] = outcome, error
                if error:
                    job['status'] = 'error'

    def cancel(self, job_id):
        job = self.get_raw(job_id)
        with self.lock:  # first: cancelling a future runs its callback at once, which would mark the job done
            if job['status'] == 'running':
                job['status'] = 'cancelled'
        for future in job.get('_futures', []):
            future.cancel()  # queued runs are dropped; runs already going finish

    def get_raw(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise ValueError('No such job: ' + str(job_id))
            return self.jobs[job_id]

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise ValueError('No such job: ' + str(job_id))
            return self._public(job)

    def list(self):
        with self.lock:
            return [{k: v for k, v in self._public(job).items() if k not in ('runs', 'result')}
                    for job in sorted(self.jobs.values(), key=lambda j: -j['started'])]

    @staticmethod
    def _public(job):
        public = {k: v for k, v in job.items() if not k.startswith('_')}
        public['progress'] = round(job['done'] / job['total'], 3) if job['total'] else 1.
        public['elapsed'] = round((job['finished'] or time.time()) - job['started'], 1)
        return public

    def _trim(self):
        finished = sorted((j for j in self.jobs.values() if j['status'] != 'running'), key=lambda j: j['started'])
        for job in finished[:max(0, len(self.jobs) - MAX_JOBS)]:
            del self.jobs[job['id']]

    def close(self):
        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
            self._pool = None
