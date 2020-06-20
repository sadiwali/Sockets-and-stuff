from machine import Pin
try:
    import ujson as json
    import urequests as requests
    import utime as time
    import usocket as socket
except:
    import json
    import requests
    import time
    import socket

import network
import _thread as thread
import sys

LOW = 0
MED = 1
CRIT = 3


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
        if severity == LOW:
            # continue if unable to fix
            print("Can't fix error, passing errorreturn")
            return errorreturn
        elif severity == MED and _attempt <= num_attempts:
            # try to fix again after waiting a bit
            print("Waiting for " + str(waittime +
                                       " seconds before trying again..."))
            time.sleep(waittime)
            return fix_error(e, severity, errorreturn, num_attempts, _attempt + 1, waittime)
        elif severity == CRIT:
            # if can't fix, then exit
            print("Could not fix the error, attempted " +
                  str(_attempt + " times, severity: " + str(severity)))
            sys.exit()
        else:
            print("Could not fix error after attempt " + str(_attempt))
            return errorreturn


class ConfigHandler:
    ''' Handle a storage config file with the ability to read, and save instantly to storage. '''

    def __init__(self, CONFIG_NAME):
        self._config_name = CONFIG_NAME
        self._config = self._load_config(CONFIG_NAME)

    def get_val(self, key):
        if key in self.config:
            return self.config[key]
        else:
            return None

    def set_val(self, key, value):
        self._config[key] = value
        self._save_config

    def get_keys(self):
        return self._config.keys()

    def _save_config(self):
        try:
            print("writing config file...")
            with open(self._config_name, 'w') as f:
                json.dump(self._config, f)
            print("wrote config to file.")
        except:
            print("Could not save config")

    def _load_config(self):
        data = {}
        try:
            with open(self._config_name, 'r') as f:
                data = json.load(f)
            print("opened config " + str(data))
            return data
        except Exception as e:
            return ErrorHandler.fix_error(e, CRIT)


class ThreadStack:
    def __init__(self, stack_size=None):
        self._max_stack_size = 5
        if not stack_size or stack_size > self._max_stack_size:
            stack_size = self._max_stack_size

        self.paused = True # don't start any additional threads if paused

        self.threads = [] # threads in queue not yet run
        self.free_locks = [i for i in range(stack_size)] # a queue of free thread locks
        self.locks = [ThreadObject.new_lock() for i in range(stack_size)]  # reusing these locks

    def add_thread(self, t_obj):
        self.threads.append(t_obj)  # store the thread
        return self

    def start_all(self):
        self.paused = False
        for i in range(len(self.free_locks)):
            # start a thread for each free slot
            self._start_thread_on_lock()

    def pause_all(self):
        self.paused = True

    

    def _start_thread_on_lock(self):
        if self.paused:
            return
        # if there exists threads not yet run
        if len(self.threads) != 0:
            # if there is a free lock
            if len(self.free_locks) != 0:
                # take the thread out to start
                thread_to_run = self.threads.pop()
                # take out a free lock
                free_lock_num = self.free_locks.pop()
                # set the exit verification, give it the lock's number to return, the actual lock, and the callback fcn
                thread_to_run.set_exit_verify(free_lock_num, self.locks[free_lock_num], self._thread_exits)
                thread_to_run.start() # finally start the thread
            else:
                # this shouldn't happen. _start_thread_on_lock is only called when a free lock is available
                print("Tried to start a thread when no locks were available!")
        else:
            # no more threads to run
            print("No more threads to run.")
            pass
                
            

    def _thread_exits(self, lock_num):
        # perform the callback
        self.free_locks.append(lock_num)  # place the returned lock back in rotation
        self._start_thread_on_lock() # try to start a new thread


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
            raise Exception("Could not set exit verify because thread already running.")
        

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
        lock.release() # release the lock first
        if self.exit_verify: # call the exit verification callback if exists
            self.verify_callback(self.lock_id)

    def is_running(self):
        if not self.lock:
            return False
        else:
            return self.lock.locked()

    @staticmethod
    def new_lock():
        return thread.allocate_lock()


# class Device:
#     def __init__(self, id, config):
#         self.id = id
#         self.config = config
