__author__ = 'samantha'
import os, logging, sys, time

#TODO change to app or subsystem logfile and product log dir
Default_Log_Dir = '/tmp/cw_logs'
Default_Log_File = 'uop.log'
Default_Log_Mode = logging.DEBUG

def set_logging_defaults(default_file=None, default_dir = None, default_mode = None):
    global Default_Log_Dir, Default_Log_File, Default_Log_Mode
    if default_file: Default_Log_File = default_file
    if default_dir: Default_Log_Dir = default_dir
    if default_mode: Default_Log_Mode = default_mode

class GMTFormatter(logging.Formatter):
    converter = time.gmtime


def getLogger(logname, filename = None, directory = None, debug_level=None):
    return getlog(logname, filename=filename, directory=directory, debug_level=debug_level)

def getlog(logname, filename = None, directory = None, debug_level=None):
    '''returns a logger with logname that will print to filename and directoryname.'''
    if directory is None:
        directory = Default_Log_Dir
    if filename is None:
        filename = Default_Log_File

    fullpath = os.path.join(directory, filename)
    starting = not os.path.exists(fullpath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    level = debug_level if debug_level else logging.DEBUG

    mylog = logging.getLogger(logname)
    hdlr = logging.FileHandler(fullpath)

    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s <%(threadName)s> %(message)s')
    hdlr.setFormatter(formatter)
    mylog.addHandler(hdlr)
    mylog.setLevel(level)
    if starting:
        if not os.path.exists(directory):
            os.mkdir(directory)
        mylog.info('NEW LOGGER STARTED')
    return mylog
