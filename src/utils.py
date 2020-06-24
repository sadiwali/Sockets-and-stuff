try:
    import ujson as json
    import utime
    import network
    import usocket as socket
except:
    import json as json
    import time
    import socket
import sys
import _thread as thread


class Constants:
    LOW = 0
    MED = 1
    CRIT = 3


class ConfigHandler:

    ''' Handle a storage config file with the ability to read, and save instantly to storage. '''

    _config_name = "wifi_config.json"
    _config = {}

    @staticmethod
    def set_config_name(name):
        ConfigHandler._config_name = name

    @staticmethod
    def get_val(key):
        if key in ConfigHandler._config:
            return ConfigHandler._config[key]
        else:
            return None

    @staticmethod
    def set_val(key, value):
        ConfigHandler._config[key] = value
        ConfigHandler._save()

    @staticmethod
    def get_keys():
        return ConfigHandler._config.keys()

    @staticmethod
    def _save():
        try:
            print("writing config file...")
            with open(ConfigHandler._config_name, 'w') as f:
                json.dump(ConfigHandler._config, f)
            print("wrote config to file.")
        except:
            print("Could not save config")

    @staticmethod
    def load():
        data = {}
        print("Trying to open " + ConfigHandler._config_name)
        try:
            with open(ConfigHandler._config_name, 'r') as f:
                data = json.load(f)
            print("opened config " + str(data))
            ConfigHandler._config = data
        except Exception as e:
            raise
            #ConfigHandler._config = ErrorHandler.fix_error(e, CRIT)


class ErrorHandler(object):
    ''' Attempt the fix the given error and return the correct response '''
    @staticmethod
    def fix_error(e, severity, errorreturn, num_attempts=1, _attempt=1, waittime=5):
        '''
        Try to fix the error and return the right thing, otherwise quit or return the next best thing
        '''
        print("This error needs fixing: <" + str(e) +
              "> at attempt #" + str(_attempt) + "/" + str(num_attempts))

        # coming here means error was not fixed and returned earlier
        if severity == Constants.LOW:
            # continue if unable to fix
            print("Can't fix error, passing errorreturn")
            return errorreturn
        elif severity == Constants.MED and _attempt <= num_attempts:
            # try to fix again after waiting a bit
            print("Waiting for " + str(waittime +
                                       " seconds before trying again..."))
            time.sleep(waittime)
            return fix_error(e, severity, errorreturn, num_attempts, _attempt + 1, waittime)
        elif severity == Constants.CRIT:
            # if can't fix, then exit
            print("Could not fix the error, attempted " +
                  str(_attempt + " times, severity: " + str(severity)))
            sys.exit()
        else:
            print("Could not fix error after attempt " + str(_attempt))
            return errorreturn


class ThreadStack:

    def __init__(self, stack_size=None):
        ''' A threadstack stores some number of not-yet-running threads, and runs them 
        within a stack sized by the user. Once the stack is started, it continually
        pops from the thread stack and automatically starts the next thread once a thread is completed.

        Args:
            stack_size (int): How many threads can be run at the same time.

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
            t_obj (ThreadObject): The thread object.

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
            lock_num (int): The lock number to mark as available.

        '''
        # perform the callback
        # place the returned lock back in rotation
        self._free_locks.append(lock_num)
        if len(self._threads) != 0:
            # try to start a new thread if there are threads to be run
            self._start_thread_on_lock()


class NetworkHandler:

    sta_if = None

    @staticmethod
    def connect():
        NetworkHandler.sta_if = network.WLAN(network.STA_IF)
        if not NetworkHandler.sta_if.isconnected():
            print("connecting to wifi...")
            NetworkHandler.sta_if.active(True)
            NetworkHandler.sta_if.connect(ConfigHandler.get_val(
                'ssid'), ConfigHandler.get_val('password'))
            while not NetworkHandler.sta_if.isconnected():
                pass
            print("Wifi connected for 1st time.")
        else:
            print("Wifi connected using saved state.")

    @staticmethod
    def get_ip():
        return NetworkHandler.sta_if.ifconfig()[0]

    @staticmethod
    def is_connected():
        if not NetworkHandler.sta_if:
            return False
        else:
            return NetworkHandler.sta_if.isconnected()


class ThreadObject:
    def __init__(self, t_func, t_args, callback, lock=None):
        ''' This is a thread but with the ability to be given a callback function, and another
        exit verifying callback function which is meant to signal the end of the thread to the
        class managing this thread. 

        Args:
            t_func (function): The threading function to run in the thread.
            t_args (tuple): Arguments to pass to the threading function above.
            callback (function): The function to call once the thread has completed.
            lock (thread lock): (optional) pass in a lock to use.

        '''
        self.t_func = t_func
        self.t_args = t_args
        self.callback = callback
        self.lock = lock
        self.release_lock = None
        self.lock_id = None  # used by release_lock fcn if supplied

    def set_releaser(self, lock_id, lock, callback):
        ''' Set the exit verification function with the lock id, and lock to use, along with the
        exit verification callback function. This is meant to help the class managing this thread
        verify it has closed, and mark the lock as available (useful for ThreadStack).

        Args:
            lock_id (int): The lock number (index) to mark as available by passing to callback.
            lock (thread lock): The lock to be used by the thread.
            callback (function): The function to send the exit notification along with the lock number to.

        Raises:
            Exception: If thread is already running.

        '''
        if not self.is_running():
            self.release_lock = callback
            self.lock_id = lock_id
            self.lock = lock
        else:
            raise Exception(
                "Could not set exit verify callback because thread already running.")

    def start(self):
        ''' Start the thread by using the helper function. '''
        self._start_thread()

    def _start_thread(self):
        ''' Start the thread by usign another helper function. '''
        if not self.lock:
            self.lock = ThreadObject.new_lock()
        thread.start_new_thread(
            self._thread_helper, (self.t_func, self.t_args, self.callback, self.lock))

    def _thread_helper(self, t_func, t_args, callback, lock):
        ''' This function is run in the thread. Acquire the lock, and call the given
        threading function, then return the result via the callback function, and release the lock.

        Args:
            t_func (function): The threading function.
            t_args (tuple): Arguments for the threading function.
            callback (function): The callback function.
            lock (threading lock): The lock to use.

        '''
        lock.acquire()
        res = t_func(*t_args)  # call the threading function
        if self.callback:
            callback(res)  # call the callback function
        lock.release()  # release the lock first
        if self.release_lock:  # call the exit verification callback if exists
            self.release_lock(self.lock_id)

    def is_running(self):
        ''' For checking if the thread is running. Normally a lock isn't provided when the 
        ThreadObject is just initialized so if it doesn't exist, the thread isn't running.
        If the lock exists, it being locked means thread is running.

        Returns:
            bool: True if running, False otherwise.z

        '''
        if not self.lock:
            return False
        else:
            return self.lock.locked()

    @staticmethod
    def new_lock():
        ''' Get a new lock 

        Returns:
            threading lock: a new lock

        '''
        return thread.allocate_lock()


class ConnectionHandler:
    server_ip = None
    server_port = 4000
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @staticmethod
    def send_str(msg, addr):
        try:
            print("Trying to send " + msg + " to " + str(addr))
            bytes_sent = ConnectionHandler.s.sendto(msg.encode(), addr)
            print("Sent msg'" + msg + "' (" + str(bytes_sent) + ") bytes")

        except Exception as e:
            print(str(e))
            print("Could not connect to socket with address " + str(addr))

    @staticmethod
    def get_addr(ip, port):
        return socket.getaddrinfo(ip, port)[0][-1]

    @staticmethod
    def get_server_addr():
        return (ConnectionHandler.server_ip, ConnectionHandler.server_port)

    @staticmethod
    def find_server_ip():
        ip = NetworkHandler.get_ip()
        for i in range(10, 25):
            ip_to_try = ip[0:ip.rfind('.')+1]+str(i)
            if ip_to_try == ip:
                continue
            ConnectionHandler.send_str("HANDSHAKE", ConnectionHandler.get_addr(
                ip_to_try, ConnectionHandler.server_port))
        while True:
            data, sender_addr = ConnectionHandler.s.recvfrom(1024)
            data = data.decode()
            print(data + "\n")
            if data == "200 OK":
                # server has been found, return ip
                ConnectionHandler.server_ip = sender_addr[0]
                return sender_addr

    @staticmethod
    def listen(addr, callback):
        while True:
            data, sender_addr = ConnectionHandler.s.recvfrom(1024)
            if sender_addr[0] == ConnectionHandler.server_ip:
                callback(data)

