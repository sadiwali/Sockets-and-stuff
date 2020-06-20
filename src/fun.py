import time
import _thread as thread


class ThreadObject:
    def __init__(self, t_func, tuple_args, callback, lock=None):
        self.lock = lock
        self.thread = None
        if not self.lock:
            self.lock = ThreadObject.new_lock()
        self.thread = thread.start_new_thread(
            self._thread_helper, (t_func, tuple_args, callback, self.lock))

    def _thread_helper(self, t_func, tuple_args, callback, lock):
        lock.acquire()
        res = t_func(*tuple_args)  # call the threading function
        callback(res)  # call the callback function
        lock.release()

    def is_running(self):
        return self.lock.locked()

    @staticmethod
    def new_lock():
        return thread.allocate_lock()


class CounterMan:
    def __init__(self):
        self.secret = "I LIKE BERRIES"

    def counter(self, count):
        time.sleep(count)
        return "AND COKE"

    def callback(self, res):
        self.secret += " " + res
        print(self.secret + "\n")


print("Starting program")
cm = CounterMan()
print(cm.secret)