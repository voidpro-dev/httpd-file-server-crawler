import requests
import os
import time
import threading
import urllib.parse
from bs4 import BeautifulSoup

session = requests.Session()
session.proxies.update({"http": "socks5h://localhost:9050"})

url = "http://ro4h37fieb6oyfrwoi5u5wpvaalnegsxzxnwzwzw43anxqmv6hjcsfyd.onion/dwango"
target = "/root/cdn/dwango"

files = []
folders = [url+"/"]

while folders:
    new_folders = []
    threads = []
    for folder in folders:
        print(f"Getting {urllib.parse.unquote(folder.replace(url, ''))}")
        def worker(_folder):
            for a in BeautifulSoup(session.get(_folder).text, "html.parser").find_all("a"):
                if not a.get("href") == "../":
                    if a.get("href").endswith("/"):
                        new_folders.append(_folder+a.get("href"))
                    else:
                        files.append(_folder+a.get("href"))
        thread = threading.Thread(target=worker, args=[folder], daemon=True)
        thread.start()
        threads.append(thread)
        while threading.active_count() > 50:
            time.sleep(1)
    for thread in threads:
        thread.join()
    folders = new_folders

print(len(files), "in this file server")

if target.endswith("/"):
    target = target[:-1]
if not os.path.isdir(target):
    print("unknown target folder")
    exit()

threads = []
for file in files:
    print(f"Saving {urllib.parse.unquote(file.replace(url, ''))}")
    def worker(_file):
        filepath = urllib.parse.unquote(_file.replace(url, ""))
        folder = filepath.split("/")
        for n in range(len(folder)-1):
            check_folder = target+"/".join(folder[0:n+1])
            if not os.path.isdir(check_folder):
                try:
                    os.mkdir(check_folder)
                except:
                    pass
        open(target+filepath, "wb").write(session.get(_file).content)
    thread = threading.Thread(target=worker, args=[file], daemon=True)
    thread.start()
    threads.append(thread)
    while threading.active_count() > 50:
        time.sleep(1)

for thread in threads:
    thread.join()

print("Done! <3")
