import time


class Stopwatch:
    def __init__(self, print_func=print):
        self.print_func = print_func
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time:
            diff = time.time() - self.start_time
            self.print_func(f'Elapsed time: {diff:.5f} seconds')
        else:
            self.print_func('Stopwatch error: start() method needs to be called first')
