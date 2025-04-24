from sjautils.dicts import DictObject
import json, os
import yaml
from dotenv import find_dotenv, load_dotenv
from pathlib import Path


def homedir():
    return str(Path.home())


def home_path(path):
    return os.path.join(homedir(), path)


def load_env():
    return load_dotenv(find_dotenv())


class Environment(DictObject):
    def __init__(self):
        defaults = dict()

        super().__init__(**defaults)

    def find_env(self):
        start = os.path.dirname(__file__)

        while os.path.basename(start) != 'python_common':
            start = os.path.dirname(start)
        path = os.path.join('')

    def read_env(self, env_path='', env='dev'):
        if not env_path:
            env_path = os.path.join(os.path.dirname(__file__), 'aws_env.yml')
        if env_path:
            if os.path.exists(env_path):
                with open(env_path) as f:
                    data = yaml.load(f, Loader=yaml.FullLoader)
                    for k, v in data.get(env, {}).items():
                        self[k] = v


our_env = Environment()


def read_env(env_path='', env='dev'):
    our_env.read_env(env_path, env)


def set_current_env(env=None, aws_profile=None, **kwargs):
    if aws_profile:
        set_env('aws_profile', aws_profile)
    if env:
        read_env(env=env)
    for k, v in kwargs:
        set_env(k, v)


def get_env(key, default=None, translate=True):
    '''
    Returns the value of key in the current environment.
    Let the os.environ value if any overrule what is stored and store it if present.
    Else return the stored value if present.  Else store and return the default
    if provided.
    :param: key - environment variable name
    :param: default - default value if not present
    :returns: the value associated with key or None
    '''

    val = os.environ.get(key)
    if val:
        our_env[key] = val
    elif key not in our_env:
        if default is not None:
            our_env[key] = default
    raw = our_env.get(key)
    if raw and translate:
        try:
            return json.loads(raw)
        except:
            pass
    return raw


def set_env(key, val):
    if isinstance(val, dict):
        val = json.dumps(val)
    elif isinstance(val, bool):
        val = json.dumps(val)
    elif isinstance(val, str):
        val = json.dumps(val)
    else:
        val = str(val)
    os.environ[key] = val
