import random
from queue import Queue
import urllib3
from progress.bar import IncrementalBar
import threading
from pyuseragents import random as random_useragent
import requests

urllib3.disable_warnings()

def load_proxies(fp: str = "prx.txt"):
    if fp == "": fp = "prx.txt"
    """
    Простая загрузка прокси в список

    :param fp:
    :return: Список с прокси
    """
    proxies = []
    with open(file=fp, mode="r", encoding="utf-8") as File:
        lines = File.read().split("\n")
    for line in lines:
        try:
            proxies.append(f"http://{line}")
        except ValueError:
            pass

    if proxies.__len__() < 1:
        raise Exception(f"can't load empty proxies file ({fp})!")

    print("{} proxies loaded successfully!".format(proxies.__len__()))

    return proxies

class PrintThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def printfiles(self, addr):
        with open(f'ondo_found.txt', "a", encoding="utf-8") as ff:
            ff.write(addr)

    def run(self):
        while True:
            addr = self.queue.get()
            self.printfiles(addr)
            self.queue.task_done()

class ProcessThread(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            addr = self.in_queue.get()
            addr = self.func(addr)
            if addr != "": self.out_queue.put(addr)
            self.in_queue.task_done()

    def func(self, addr):
        while True:
            try:
                sess = requests.session()
                proxie = random.choice(proxies)
                if proxie == "": continue
                sess.proxies = {'all': proxie}
                sess.headers = {
                    'user-agent': random_useragent(),
                    'accept': 'application/json, text/plain, */*',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                }
                sess.verify = False
                response = sess.get(f'https://v1.ondo.finance/api/proofs?address={addr}')
                if response.status_code == 200 or response.status_code == 304:
                    bar.next()
                    if "amount" in response.text:
                        return f'''{addr}\n'''
                    return ""
            except:
                pass
            
proxies = load_proxies(input('Path to proxies: '))
# proxies = load_proxies('prx.txt')

threads = int(input('Max threads: '))
# threads = 1

filename = "mnemonics.txt"
with open(filename, encoding="utf-8") as f:
    mnemonics = f.read().splitlines()
    
print(f'Loaded {len(mnemonics)} address')
bar = IncrementalBar('Countdown', max=len(mnemonics))

pathqueue = Queue()
resultqueue = Queue()

# spawn threads to process
for i in range(0, threads):
    t = ProcessThread(pathqueue, resultqueue)
    t.daemon = True
    t.start()

# spawn threads to print
t = PrintThread(resultqueue)
t.daemon = True
t.start()

# add paths to queue
for path in mnemonics:
    pathqueue.put(path)

# wait for queue to get empty
pathqueue.join()
resultqueue.join()