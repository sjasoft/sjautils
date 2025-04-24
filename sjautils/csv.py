import csv, io
from sjautils import utils


def homogenize_fields(data):
    '''
    Ensure values for all fields have consistent data by substituting defaults
    in case of missing value. In order words produce list of dicts that have
    the same keys and default values for missing keys but some but not all rows
    have.
    :param data: list of dictionaries
    :return: modifies data in place as necessary
    '''

    def default_for_type(a_type):
        if issubclass(a_type, int):
            return 0
        elif issubclass(a_type, float):
            return 0.0
        elif issubclass(a_type, str):
            return ''
        else:
            raise Exception('unhandled missing type %s' % a_type)

    key_type = {}
    for item in data:
        for k, v in item.items():
            if k not in key_type:
                key_type[k] = type(v)
    all_types = set(key_type.values())
    for item in data:
        for k, k_type in key_type.items():
            if not k in item:
                item[k] = default_for_type(k_type)


def dict_to_csv(dict_list, first_keys=None, postprocess_fn=None):
    '''
    convert a list of dicts with same keys to a CSV in a buffer
    :param dict_list: list of dicts
    :param first_keys: keys that should be in first columns if we require it
    :param postprocess_fn: optional transformation te perform on each dict before generating csv output
    :return: io.StringIO() csv outputp
    '''
    if isinstance(dict_list, dict):
        dict_list = [dict_list]
    if postprocess_fn:
        dict_list = [postprocess_fn(d) for d in dict_list]
    homogenize_fields(dict_list)
    csv_columns = list(dict_list[0].keys())
    if first_keys:  # then we may have to reorder
        if not all([((k in csv_columns) for k in first_keys)]):
            raise Exception('report configuration error, sort keys %s not in columns %s' % (first_keys, csv_columns))
        if csv_columns[:len(first_keys)] != first_keys:  # then reorder
            rest = [k for k in csv_columns if k not in first_keys]
            csv_columns = list(first_keys) + rest

    try:
        with io.StringIO() as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in dict_list:
                writer.writerow(data)
            return csvfile.getvalue()
    except IOError:
        print("I/O error")


def csv_to_dicts(raw_contents):
    as_str = utils.bytesToString(raw_contents)
    reader = csv.DictReader(as_str.split())
    return [dict(r) for r in reader]


def csv_to_arrays(raw_contents):
    as_str = utils.bytesToString(raw_contents)
    reader = csv.reader(as_str.split())
    return list(reader)
