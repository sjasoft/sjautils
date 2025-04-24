import datetime, time, pytz

timestamp = lambda: int(time.time())
epoch_seconds = lambda d: d.timestamp()

perDay = 24 * 60 * 60
perYear = perDay * 365.25

def _scaledEpoch(scale, e = None):
    e = e or time.time()
    return e / scale

def dayNum(e = None):
    return _scaledEpoch(perDay, e)

def yearNum(e = None):
    return _scaledEpoch(perYear, e)

def epoch_iso_day(epoch):
    ts = time.gmtime(epoch)
    dt = datetime.datetime(ts.tm_year, ts.tm_mon, ts.tm_mday, ts.tm_hour, ts.tm_min, ts.tm_sec)
    return dt.isoformat()[:10]


def epoch_beginning_of_day(year, month, day):
    d = datetime.datetime(year, month, day, 0, 0, 1)
    return epoch_seconds(d)


def iso_day_parts(iso_day):
    return [int(p) for p in iso_day[:10].split('-')[:3]]


def epoch_end_of_day(year, month, day):
    d = datetime.datetime(year, month, day, 23, 59, 59)
    return epoch_seconds(d)


def ensure_datetime(epoch_or_dt, set_tzinfo=False):
    if epoch_or_dt is not None:
        if not isinstance(epoch_or_dt, datetime.datetime):
            d = epoch_to_datetime(epoch_or_dt)
            if set_tzinfo and not d.tzinfo:
                d = d.replace(tzinfo=pytz.UTC)
            return d
        return epoch_or_dt
    return None


def epoch_to_datetime(epoch):
    return datetime.datetime.utcfromtimestamp(epoch)


def epoch_to_iso_day(epoch):
    d = datetime.datetime.utcfromtimestamp(epoch)
    return d.isoformat()[:10]


def epoch_to_iso_datetime(epoch):
    d = datetime.datetime.utcfromtimestamp(epoch)
    return d.isoformat()[:19]


def datetime_to_epoch(dtime):
    return dtime.timestamp()
