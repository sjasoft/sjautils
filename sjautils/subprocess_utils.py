import subprocess as sub
import os
from sjautils.utils import bytesToString, get_logger

logger = get_logger()


def sub_pipes(*pipes):
    return {p: sub.PIPE for p in pipes}


standard_pipes = sub_pipes('stdin', 'stdout', 'stderr')


def without_output(cmd):
    with open(os.devnull, 'a') as out:
        sub.Popen(cmd, shell=True, stdout=out, stderr=out)


def with_output_to(path, cmd):
    with open(path, 'a') as out:
        sub.Popen(cmd, shell=True, stdout=out, stderr=out)

def clean_output(s):
    get_output = lambda stuff: [l.strip() for l in stuff.split('\n') if l]
    if isinstance(s, bytes):
        s = bytesToString(s)
    a_s = get_output(s)
    return a_s[0] if (len(a_s) == 1) else a_s

def command_output(command):
    get_output = lambda stuff: [l.strip() for l in stuff.split('\n') if l]
    p = sub.Popen(command, shell=True, **standard_pipes)
    out, err = p.communicate()

    return clean_output(out) or clean_output(err)


def command_out_err(command):
    get_output = lambda stuff: [l.strip() for l in stuff.split('\n') if l]
    shorten = lambda stuff: stuff[0] if (len(stuff) == 1) else stuff
    p = sub.Popen(command, shell=True, **standard_pipes)
    out, err = p.communicate()
    return clean_output(out), clean_output(err)

def shell_out(command, wait=True, log_it=True):
    if wait:
        res = command_output(command)
        if log_it:
            logger.info('SHELL OUT cmd: %s\nresult:\n%s', command, res)
        return res
    else:
        if log_it:
            logger.info('not waiting: SHELL_OUT cmd: Ys', command)
        return without_output(cmd)
