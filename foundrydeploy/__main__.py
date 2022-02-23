from .parser import parse
import os, sys

if len(sys.argv) == 1:
    print("error: requires a script file")
    exit(1)

with open(sys.argv[1], "r") as f:
    try:
        parse(f.read())
    except ValueError as e:
        print(e)
        raise e
