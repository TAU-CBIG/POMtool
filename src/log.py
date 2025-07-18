VERBOSE = False
INFO = True

def print_verbose(*args):
    if VERBOSE:
        print(*args)

def print_info(*args):
    if INFO:
        print(*args)

already_printed = set()
def print_once(*args):
    if not (args in already_printed):
        already_printed.add(args)
        print(*args)

def print_once_verbose(*args):
    if VERBOSE:
        print_once(*args)

def print_once_info(*args):
    if INFO:
        print_once(*args)
