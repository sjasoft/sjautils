from fastapi.requests import Request
from sjautils.web.exceptions import GenericWebException

def split_special(orig_args, remainder='json'):
    response_only = orig_args.pop('response_only', False)
    headers = orig_args.pop('headers', None)
    data = None
    if len(orig_args) == 1: # possible json, data, params= case
        key = list(orig_args.keys())[0]
        if key in ('params', 'json', 'data'):
            orig_args = orig_args.get(key)
            remainder = key
    kwargs = {}
    if orig_args:
        kwargs[remainder] = orig_args
    if headers:
        kwargs['headers'] = headers
    return response_only, kwargs


def url_based_on_request(request: Request, *components):
    return str(request.url) + '/'.join(list(components))

def url_based_on_url(an_url, *components):
    return str(an_url) + '/'.join(list(components))

def json_or_error(response, special_processing=None):
    """
    Returns json if possible else an exception that includes the response
    """
    is_ok = getattr(response, 'ok', 200 <= response.status_code < 300)
    if not is_ok:
        raise GenericWebException(response=response, special_processing=special_processing)
    try:
        return response.json()
    except Exception as e:
        raise GenericWebException(response=response, original_exception=e)
