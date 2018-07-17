from concurrent.futures import ThreadPoolExecutor

import os

from dirhunt.exceptions import reraise_with_stack


class Pool(ThreadPoolExecutor):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        max_workers = max_workers or ((os.cpu_count() or 1) * 5)
        super(Pool, self).__init__(max_workers=max_workers, thread_name_prefix=thread_name_prefix)

    def callback(self, *args, **kwargs):
        raise NotImplementedError

    def submit(self, *args, **kwargs):
        return super(Pool, self).submit(reraise_with_stack(self.callback), *args, **kwargs)
