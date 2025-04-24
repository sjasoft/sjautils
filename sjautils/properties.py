__author__ = 'samantha'
from sjautils.tools import gensym

class reader(property):
    """
    property with only reader specified
    ex.
      foo = reader('foo')
    """
    def __init__(self, varname, default=None):
        def _reader(obj):
            if not hasattr(obj, varname):
                setattr(obj, varname, default)
            return getattr(obj, varname)
        property.__init__(self, _reader)

def read_only(var_name):
    def varname(object):
        return var_name if var_name else gensym(object)
    def reader(self):
        name = varname(self)
        if not hasattr(self, name):
            setattr(self, name, None)
        return getattr(self, name)

    return property(reader)

def accessor(var_name=None):
    def varname(object):
        return var_name if var_name else gensym(object)
    def reader(self):
        name = varname(self)
        if not hasattr(self, name):
            setattr(self, name, None)
        return getattr(self, name)

    def writer(self, value):
        setattr(self, varname(self), value)


    return property(reader, writer)

read_write_var = accessor

