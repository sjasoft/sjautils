__author__ = 'samantha'

def immediate_superclasses(cls):
    sups = []
    last = None
    for candidate in cls.__mro__[1:]:
        if not sups:
            sups.append(candidate)
        else:
            super_sub = [x for x in sups if issubclass(x, candidate)]
            if super_sub:
                break
            else:
                sups.append(candidate)
    return sups
