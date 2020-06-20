import time
import _thread as thread


class ThreadStack:
    def __init__(self, stack_size=None):
        self._max_stack_size = 5
        if not stack_size or stack_size > self._max_stack_size:
            stack_size = self._max_stack_size

        self._paused = True  # don't start any additional threads if paused

        self._threads = []  # threads in queue not yet run
        # a queue of free thread locks
        self._free_locks = [i for i in range(stack_size)]
        self._locks = [ThreadObject.new_lock()
                      for i in range(stack_size)]  # reusing these locks

    def add_thread(self, t_obj):
        self._threads.append(t_obj)  # store the thread

    def start_all(self):
        self._paused = False
        for i in range(len(self._free_locks) if len(self._threads) >= len(self._free_locks) else len(self._threads)):
            # start a thread for each free slot
            self._start_thread_on_lock()

    def pause_all(self):
        self._paused = True

    def _start_thread_on_lock(self):
        if self._paused:
            return
        # if there exists threads not yet run
        if len(self._threads) != 0:
            # if there is a free lock
            if len(self._free_locks) != 0:
                # take the thread out to start
                thread_to_run = self._threads.pop()
                # take out a free lock
                free_lock_num = self._free_locks.pop()
                # set the exit verification, give it the lock's number to return, the actual lock, and the callback fcn
                thread_to_run.set_exit_verify(
                    free_lock_num, self._locks[free_lock_num], self._thread_exits)
                thread_to_run.start()  # finally start the thread
            else:
                # this shouldn't happen. _start_thread_on_lock is only called when a free lock is available
                print("Tried to start a thread when no locks were available!")
        else:
            # no more threads to run
            print("No more threads to run.")
            pass

    def _thread_exits(self, lock_num):
        # perform the callback
        # place the returned lock back in rotation
        self._free_locks.append(lock_num)
        if len(self._threads) != 0:
            # try to start a new thread if there are threads to be run
            self._start_thread_on_lock()


class ThreadObject:
    def __init__(self, t_func, tuple_args, callback, lock=None):
        self.t_func = t_func
        self.tuple_args = tuple_args
        self.callback = callback

        self.lock = lock
        self.verify_callback = None
        self.lock_id = None  # set by second callback

    def set_exit_verify(self, lock_id, lock, callback):
        if not self.is_running():
            self.verify_callback = callback
            self.lock_id = lock_id
            self.lock = lock
            return lock_id
        else:
            raise Exception(
                "Could not set exit verify because thread already running.")

    def start(self):
        self._start_thread()

    def _start_thread(self):
        if not self.lock:
            self.lock = ThreadObject.new_lock()
        thread.start_new_thread(
            self._thread_helper, (self.t_func, self.tuple_args, self.callback, self.lock))

    def _thread_helper(self, t_func, tuple_args, callback, lock):
        lock.acquire()
        res = t_func(*tuple_args)  # call the threading function
        callback(res)  # call the callback function
        lock.release()  # release the lock first
        if self.verify_callback:  # call the exit verification callback if exists
            self.verify_callback(self.lock_id)

    def is_running(self):
        if not self.lock:
            return False
        else:
            return self.lock.locked()

    @staticmethod
    def new_lock():
        return thread.allocate_lock()
        return thread.allocate_lock()


class CounterMan:
    def __init__(self):
        self.secret = "I LIKE BERRIES"

    def counter(self, count):
        time.sleep(count)
        return "AND COKE"

    def callback(self, res):
        self.secret += " " + res + " "
        print(self.secret + "\n")


print("Starting program")
cm = CounterMan()
print(cm.secret + "\n")

ts = ThreadStack(5)
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add_thread(ThreadObject(cm.counter, (2, ), cm.callback))
