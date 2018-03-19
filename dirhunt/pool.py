from concurrent.futures import ThreadPoolExecutor

from dirhunt.exceptions import reraise_with_stack


class Pool(ThreadPoolExecutor):
    def callback(self, *args, **kwargs):
        raise NotImplementedError

    def submit(self, *args, **kwargs):
        return super(Pool, self).submit(reraise_with_stack(self.callback), *args, **kwargs)
