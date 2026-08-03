import multiprocessing
import time

start = time.perf_counter()


def do_something(seconds):
    print(f'Sleeping {seconds} second(s)...')
    time.sleep(seconds)
    print('Done Sleeping...')


#do_something()
''' ***Note-- if using parenthesis, instead:
    
    Ex: p1 = multiprocessing.Process(target=do_something())

the return value will be "called back" from the function 
instead of just running the function as below,
which is simply a "function call".'''

# to get both processes start simultaneously (SS) => half the time(duration):
p1 = multiprocessing.Process(target=do_something)
p2 = multiprocessing.Process(target=do_something)

"""
### if more than two processes, just use a loop instead of typing out eah one.
##=> This entire section is deprecated due to size constraints, but still functions:

# start both processes
p1.start()
p2.start()

# to pause both processes, before moving on, use join():
p1.join()
p2.join()

''' execution is paused here unil both processes are completed,
=> they have joined the current process(i.e. this script's) execution loop.'''

## End of deprecated section
"""
# Note: the finish times of p1 and p2 can be different(usually are?)

#do_something_different()

# create an empty list of processes
processes = []

#loop through 10 processes
for _ in range(10):
# the underscore above is an unused/temporary/throw away int() variable
    # the args called in the multiprocessing.Process(target,args) method
    # must be a list of the correct vartype(single item lists are ok).
    # Lookup: Why is "pyckle format" required by multiprocessing.Process()?
    p = multiprocessing.Process(target=do_something, args=[1.5])
    p.start()
    processes.append(p)

# join the list of SS processes to this position(queue) in current execution loop
for process in processes:
    process.join()

finish = time.perf_counter()

print(f'Finished in {round(finish - start, 2)} seconds(s)')

