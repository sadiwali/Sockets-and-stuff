import time
import _thread as thread

var = True

def counter (id, count):
    global var
    print("Thread name is " + id)
    while True:
        time.sleep(2)
        var = not var
        print(str(var))

print("starting threads")
thread.start_new_thread(counter, ("t1", 10))
thread.start_new_thread(counter, ("tt", 10))

while True:
    time.sleep(1)
    print("running" + str(var))

