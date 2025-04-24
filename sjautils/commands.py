from sjautils.subprocess_utils import command_out_err
from sjautils.string import after, before
import os, shutil

def unrar(path, remove_after=True):
    if ' ' in path:
        path = '"' + path + '"'
    cmd = f'unrar x {path}'
    out,err = command_out_err(cmd)
    if err and not out:
        raise Exception(f'{cmd}: {err}')
    elif remove_after:
        os.remove(path)

def transcribe(path, delete_download=False, json_out=None):
    pass

sample_dlp = """
 yt-dlp "https://odysee.com/@MarkMoss:7/why-aren't-the-markets-crashing:b"
[lbry] Extracting URL: https://odysee.com/@MarkMoss:7/why-aren't-the-markets-crashing:b
[lbry] @MarkMoss#7/why-aren't-the-markets-crashing#b: Downloading stream JSON metadata
[lbry] b598f8b414784a79bdb7ee412bb20f6377a5d9d2: Downloading streaming url JSON metadata
[lbry] @MarkMoss#7/why-aren't-the-markets-crashing#b: Checking for original quality
[lbry] @MarkMoss#7/why-aren't-the-markets-crashing#b: Downloading streaming redirect url info
[lbry] @MarkMoss#7/why-aren't-the-markets-crashing#b: Downloading m3u8 information
[info] b598f8b414784a79bdb7ee412bb20f6377a5d9d2: Downloading 1 format(s): original
[download] Destination: Why Aren't the Markets Crashing - Quarterly Report [b598f8b414784a79bdb7ee412bb20f6377a5d9d2].mp4
[download] 100% of  543.61MiB in 00:00:17 at 30.66MiB/s

"""
def dir_mov_files(path=None):
    vid_ends = ['.mov', '.mp4', '.webm']
    return {f for f in os.listdir(path) if os.path.splitext(f)[1] in vid_ends}

def download_video(vurl):

    cmd = f'yt-dlp {vurl}'
    old = dir_mov_files()
    already = 'has already been downloaded'
    out, err = command_out_err(cmd)
    print(out)
    if not err:
        new_files = dir_mov_files() - old
        if new_files:
            return list(new_files)[0]
        else:
            for o in out:
                if already in o:
                    fn = after(before(o, already), ']')
                    return fn
    else:
        raise Exception(f'problem downloading {err}')
