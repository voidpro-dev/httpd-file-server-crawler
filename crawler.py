import requests
import urllib3
import datetime
import random
import json
import os
import time
import traceback
import sys
import subprocess
import threading
import urllib.parse
from bs4 import BeautifulSoup

url = "http://ng2gzceugc2df6hp6s7wtg7hpupw37vqkvamaydhagv2qbrswdqlq6ad.onion/dwango/"
target = "/root/dwango"
thread_limit = 100 # too high value = killing proxy and your server

class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
        del kwargs["timeout"]
        super().__init__(*args, **kwargs)
    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None and hasattr(self, 'timeout'):
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

sessions = []
proxies = open("proxies.txt", "r", encoding="utf_8").read().split("\n")

for proxy in proxies:
    _session = requests.Session()
    _session.mount("http://", TimeoutHTTPAdapter(max_retries=2, timeout=(5.0, 10.0), pool_connections=100))
    _session.proxies.update({"http": proxy})
    sessions.append(_session)

files = []
folders = [url+"/"]

if target.endswith("/"):
    target = target[:-1]
if not os.path.isdir(target):
    print("unknown target folder")
    exit()

while folders:
    new_folders = []
    threads = []
    for folder in folders:
        print(f"Getting {urllib.parse.unquote(folder.replace(url, ''))}")
        def worker(_folder):
            while True:
                try:
                    session = random.choice(sessions)
                    response = session.get(_folder).text
                    break
                except:
                    print(session.proxies.get("http"), "dead")
                    #traceback.print_exc()
                    time.sleep(3)
            for a in BeautifulSoup(response, "html.parser").find_all("a"):
                if not a.get("href") == "../":
                    if a.get("href").endswith("/"):
                        new_folders.append(_folder+a.get("href"))
                    else:
                        files.append(_folder+a.get("href"))
        thread = threading.Thread(target=worker, args=[folder], daemon=True)
        thread.start()
        threads.append(thread)
        while threading.active_count() > thread_limit:
            time.sleep(0.1)
    for thread in threads:
        thread.join()
    folders = new_folders

print(len(files), "in this file server")

def parser(value):
    tb = (value/1024/1024/1024/1024)
    gb = (value/1024/1024/1024)
    mb = (value/1024/1024)
    kb = (value/1024)
    if tb > 2:
        return f"{tb:.2f}TB"
    if gb > 2:
        return f"{gb:.2f}GB"
    if mb > 2:
        return f"{mb:.2f}MB"
    return f"{int(kb)}KB"

threads = []
count = 0
total = len(files)
dl_total = 0
dl_start = time.time()
sk_total = 0
logs = []

def printer():
    before_total = 0
    before_time = time.time()
    while True:
        elapsed = time.time()-dl_start
        if before_total:
            speed = (dl_total-before_total)/(time.time()-before_time)
        else:
            speed = 0
        before_total = dl_total
        before_time = time.time()
        for _ in range(5):
            while logs:
                print(f"\r{logs.pop(0)}")
            print("\r{}/{} | {}/s | Avg {}/s | Total {} | {} elapsed".format(
                count,
                total,
                parser(speed),
                parser(dl_total / elapsed if dl_total else 0),
                parser(dl_total+sk_total),
                datetime.timedelta(seconds=int(elapsed))
            ), end="."*4)
            time.sleep(0.2)
threading.Thread(target=printer, daemon=True).start()

def _len(_name):
    if not type(_name) == str:
        raise TypeError
    return sum([(1 if a in "1234567890-^\\qwertyuiop@[asdfghjkl;:]zxcvbnm,./!\"#$%&'()=~|QWERTYUIOP`{ASDFGHJKL+*}ZXCVBNM<>?_ " else 2) for a in _name])

def _print(_log, _name, _size):
    _name = urllib.parse.unquote(_name.replace(url, ''), encoding="utf_8")
    changed = False
    while _len(_name) > 70:
        changed = True
        _name = _name[1:]
    if changed:
        _name = "..." + _name
    spacing = " "*(75-_len(_name))
    logs.append(f"\r{_log} {_name}{spacing}({parser(_size)})")

for file in files:
    #print(f"Saving {urllib.parse.unquote(file.replace(url, ''))} ({count}/{total})")
    def worker(_count, _file):
        global dl_total, sk_total, count
        filepath = urllib.parse.unquote(_file.replace(url, ""), encoding="utf_8")
        folder = filepath.split("/")
        for n in range(len(folder)-1):
            check_folder = target+"/".join(folder[0:n+1])
            if not os.path.isdir(check_folder):
                try:
                    os.mkdir(check_folder)
                except:
                    pass
        retry = False
        while True:
            try:
                session = random.choice(sessions)
                #print(_file)
                response = session.head(_file)
                if response.status_code == 404:
                    return
                size = int(response.headers.get("Content-Length", 0))
                if not size:
                    return
                last_modified = response.headers.get("Last-Modified")
                if os.path.isfile(target+filepath):
                    filesize = os.path.getsize(target+filepath)
                    if filesize == size:
                        sk_total += filesize
                        count += 1
                        if last_modified:
                            last_modified_time = datetime.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z').timestamp()
                            os.utime(target+filepath, (last_modified_time, last_modified_time))
                        #_print("Skipped", _file, size)
                        return
                    elif filesize > size:
                        try:
                            os.remove(target+filepath)
                        except:
                            pass
                        start_pos = 0
                    else:
                        start_pos = filesize
                else:
                    filesize = 0
                    start_pos = 0
                headers = {"Range": f"bytes={start_pos}-"}
                if not retry:
                    retry = True
                    sk_total += filesize
                    _print("Saving", _file, size)
                response = session.get(_file, stream=True, headers=headers)
                fp = open(target+filepath, "ab")
                for aaa in response.iter_content(chunk_size=1024):
                    dl_total += len(aaa)
                    fp.write(aaa)
                fp.close()
                if last_modified:
                    last_modified_time = datetime.datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z').timestamp()
                    os.utime(target+filepath, (last_modified_time, last_modified_time))
                count += 1
                break
            except urllib3.exceptions.MaxRetryError:
                pass
            except ConnectionRefusedError:
                pass
            except requests.exceptions.ConnectionError:
                pass
            except:
                time.sleep(1)
    thread = threading.Thread(target=worker, args=[count, file], daemon=True)
    thread.start()
    threads.append(thread)
    while threading.active_count() > thread_limit:
        time.sleep(0.1)
    for thread in list(threads):
        if not thread.is_alive():
            thread.join(timeout=0.5)
            threads.remove(thread)

for thread in threads:
    thread.join()

print("Done! <3")
