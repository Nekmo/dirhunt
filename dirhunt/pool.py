import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from dirhunt.exceptions import reraise_with_stack


class Pool(ThreadPoolExecutor):
    def __init__(self, max_workers=None, **kwargs):
        self.threads_running = 0
        max_workers = max_workers or ((multiprocessing.cpu_count() or 1) * 5)
        super(Pool, self).__init__(max_workers=max_workers, **kwargs)

    def callback(self, *args, **kwargs):
        raise NotImplementedError

    def submit(self, *args, **kwargs):
        self.threads_running += 1

        def execute(*args, **kwargs):
            try:
                return reraise_with_stack(self.callback)(*args, **kwargs)
            except Exception:
                raise
            finally:
                self.threads_running -= 1

        return super(Pool, self).submit(execute, *args, **kwargs)

    def is_running(self):
        return bool(self.threads_running)
