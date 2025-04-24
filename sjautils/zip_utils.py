import glob, io, os, zipfile
from es_utils.utils import in_directory
from contextlib import contextmanager


def zip_dest(zip_file_path=None):
    return zip_file_path or io.BytesIO()


@contextmanager
def io_zipfile():
    dst = io.BytesIO()
    z = zipfile.ZipFile(dst, mode='w')
    yield dst, z
    z.close()


def zip_glob(glob_pattern, *additional_glob_patterns, zip_file_path=None):
    '''
    zips an absolute path glob pattern
    :param glob_pattern: pattern used to gather files, recursize assumed
    :param zip_file_path: path to write zipfile to. If None then use io.BytesIO.
    :return: zip_file_path if given else the io.BytesIO. Second is useful for s3.put_item
    '''
    files = glob.glob(glob_pattern, recursive=True)
    for pattern in additional_glob_patterns:
        more = glob.glob(pattern, recursive=True)
        if more:
            files.extend(more)
    dst = zip_dest(zip_file_path)
    with zipfile.ZipFile(dst, mode='w') as z:
        zip_files(files, z)
    return dst


def zip_contents(zip_dest):
    if isinstance(zip_dest, io.BytesIO):
        return zip_dest.getvalue()
    elif isinstance(zip_dest, str) and os.path.exists(zip_dest):
        with open(zip_dest) as f:
            return f.read()


def zip_file(zip_dest):
    '''
    file like object from zip_dest
    :param zip_dest: string path or io.BytesIO:
    :return: file like object
    '''
    if isinstance(zip_dest, io.BytesIO):
        return zip_dest
    elif isinstance(zip_dest, str) and os.path.exists(zip_dest):
        with open(zip_dest) as f:
            return f


def zip_dir(dir_path, zip_file_path=None, start_at_parent=False):
    '''
    zips all directory content
    :param dir_path: path from which to gather files and/or directories, recursize assumed
    :param zip_file_path: path to write zipfile to. If None then use io.BytesIO.
    :param start_at_parent: if True start from parent directory zipping only the directory at dir_path
    :return: zip_file_path if given else the io.BytesIO. Second is useful for s3.put_item
    '''
    target_dir = os.path.abspath(dir_path)
    glob_pattern = '**'
    if start_at_parent:
        target_dir = os.path.dirname(target_dir)
        glob_pattern = os.path.join(os.path.basename(dir_path), '**')
    dst = zip_dest(zip_file_path)
    with in_directory(target_dir):
        return zip_glob(glob_pattern, zip_file_path=zip_file_path)


def zip_files(files, zip_file):
    for f in files:
        if os.path.exists(f):
            zip_file.write(f)
        else:
            raise Exception('path path to write to zip')


def extract_to(zip_file, to_path):
    pass


@contextmanager
def zip_from_contents(contents):
    packaged = io.BytesIO(contents)
    z = zipfile.ZipFile(packaged)
    yield z
    z.close()
