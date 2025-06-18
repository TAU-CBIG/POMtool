VERBOSE = False
INFO = True

def print_verbose(*args):
    if VERBOSE:
        print(*args)

def print_info(*args):
    if INFO:
        print(*args)
