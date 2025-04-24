def split_string(s, split_by=None, eat_empty=True, convert=None):
    parts = [p.strip() for p in s.split(split_by)]
    if eat_empty:
        parts = [p for p in parts if len(p)]
    if convert:
        parts = [convert(p) for p in parts]

    return parts


def split_once(s, split_by):
    return [before(s, split_by), after(s, split_by)]


def after(s, sub):
    if not sub in s:
        return s
    return s[s.index(sub) + len(sub):].strip()

def before_last(s, split_f=None):
    if (split_f is None) or (split_f in s):
        last = s.split(split_f)[-1]
        return before(s, last)
    else:
        return s

def before(s, sub):
    if not sub in s:
        return s
    return s[: s.index(sub)].strip()

def paren_split(s, splitter, convert=None):
    open = s.index('(')
    close = s.index(')')
    content = s[open + 1: close]
    rest = s[close + 1:]
    parts = split_string(content, splitter, convert=convert)
    return parts, rest

def between(s, first, last, widest=True):
    if (first in s) and (last in s):
        start = s.index(first)
        end = s.rindex(last) if widest else s.index(last)
        return s[start+1: end].strip()
    return None

