import multiprocessing
from concurrent.futures import ThreadPoolExecutor

from dirhunt.exceptions import reraise_with_stack


class Pool(ThreadPoolExecutor):
    def __init__(self, max_workers=None, **kwargs):
        max_workers = max_workers or ((multiprocessing.cpu_count() or 1) * 5)
        super(Pool, self).__init__(max_workers=max_workers, **kwargs)

    def callback(self, *args, **kwargs):
        raise NotImplementedError

    def submit(self, *args, **kwargs):
        return super(Pool, self).submit(reraise_with_stack(self.callback), *args, **kwargs)
