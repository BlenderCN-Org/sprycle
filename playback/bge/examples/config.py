import sys

# Every .blend in this directory calls this function first, via the Camera object.

def init(cont):
    """
    Adds parent directory to path, so that the sprycle module can be found when referenced by a Python controller.

    If sprycle.py resides in the same directory, or if it is included in the .blend, this will not be necessary.

    """
    sys.path.append("..")
