# how to use
1. install requirements
2. create proxies.txt and put proxies to that<br>
   (format)<br>
    no auth : http://localhost:1111<br>
    auth : http://user:pass@localhost:1111<br><br>
   
    http -> http://<br>
    socks4 -> socks4://<br>
    socks5 -> socks5h://<br>
3. replace website url in crawler.py with which you want to clone
4. replace target folder in crawler.py with where you want to save
5. run crawler.py<br>
   linux : python3 crawler.py<br>
   windows : py crawler.py   

# requirements
pip : requests, bs4, pysocks (only if you use socks proxy)
other : torproxy (if you want to clone file server which on tor network
