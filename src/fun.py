import time
import _thread as thread


class ThreadStack:

    def __init__(self, stack_size=None):
        ''' A threadstack stores some number of not-yet-running threads, and runs them 
        within a stack sized by the user. Once the stack is started, it continually
        pops from the thread stack and automatically starts the next thread once a thread is completed.

        Args:
            stack_size (int): How many threads can be run at the same time

        '''
        self._max_stack_size = 5
        if not stack_size or stack_size > self._max_stack_size:
            stack_size = self._max_stack_size

        self._paused = True  # don't start any additional threads if paused

        self._threads = []  # threads in queue not yet run
        # a queue of free thread locks
        self._free_locks = [i for i in range(stack_size)]
        self._locks = [ThreadObject.new_lock()
                       for i in range(stack_size)]  # reusing these locks

    def add(self, t_obj):
        ''' Add to the thread stack, a thread to be run.

        Args:
            t_obj (ThreadObject): The thread object

        '''
        self._threads.append(t_obj)  # store the thread

    def start(self):
        ''' Start as many threads will fit into the thread stack size, as defined earlier by
        stack_size in the class constructor. If there are fewer threads in the to-be-run stack,
        than the maximum stack size, then just run those.

        '''
        self._paused = False
        for i in range(len(self._free_locks) if len(self._threads) >= len(self._free_locks) else len(self._threads)):
            # start a thread for each free slot
            self._start_thread_on_lock()

    def pause_all(self):
        ''' Pause the running of any new threads only. Threads already running will continue running.

        '''
        self._paused = True

    def _start_thread_on_lock(self):
        ''' If there are threads to-be-run, and if there is a lock available to use,
        use that lock to run that thread. This function is only called when there is at least
        1 to-be-run thread, and at least 1 avaiable lock.

        '''
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
                thread_to_run.set_releaser(
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
        ''' This is called before the thread exits, it simply marks the lock used by the thread as available
        so that a new thread can use it. Additionally, if there is at least 1 to-be-run thread, it tries to
        run that thread by calling _start_thread_on_lock().

        Args:
            lock_num (int): The lock number to mark as available

        '''
        # perform the callback
        # place the returned lock back in rotation
        self._free_locks.append(lock_num)
        if len(self._threads) != 0:
            # try to start a new thread if there are threads to be run
            self._start_thread_on_lock()


class ThreadObject:
    '''

    '''

    def __init__(self, t_func, t_args, callback, lock=None):
        self.t_func = t_func
        self.t_args = t_args
        self.callback = callback
        self.lock = lock
        self.release_lock = None
        self.lock_id = None  # used by release_lock fcn if supplied

    def set_releaser(self, lock_id, lock, callback):
        if not self.is_running():
            self.release_lock = callback
            self.lock_id = lock_id
            self.lock = lock
            return lock_id
        else:
            raise Exception(
                "Could not set exit verify callback because thread already running.")

    def start(self):
        self._start_thread()

    def _start_thread(self):
        if not self.lock:
            self.lock = ThreadObject.new_lock()
        thread.start_new_thread(
            self._thread_helper, (self.t_func, self.t_args, self.callback, self.lock))

    def _thread_helper(self, t_func, t_args, callback, lock):
        lock.acquire()
        res = t_func(*t_args)  # call the threading function
        callback(res)  # call the callback function
        lock.release()  # release the lock first
        if self.release_lock:  # call the exit verification callback if exists
            self.release_lock(self.lock_id)

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
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
ts.add(ThreadObject(cm.counter, (2, ), cm.callback))
