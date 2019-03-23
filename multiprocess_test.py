from multiprocessing import Process, Pool, Manager
from threading import Thread
import time
from functools import wraps


def foo(ls):
    while 1:
        try:
            i = ls.pop()
            for j in range(5000000):
                i = i + 1
            print(i)
        except IndexError:
            break


def my_thread(ls):
    threads = []
    while threads or ls:
        for th in threads:
            if not th.is_alive():
                threads.remove(th)
        while len(threads) < 5 and ls:
            thread = Thread(target=foo, args=(ls,))
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        time.sleep(1)


if __name__ == "__main__":
    # compare_compute()
    # my_thread()
    m = Manager()
    # ls = m.list(range(1000))
    # t = time.time()
    # foo(ls)
    # print('单进程、单线程:', time.time() - t)  # 677

    # ls = m.list(range(1000))
    # t = time.time()
    # my_thread(ls)
    # print('多线程：', time.time() - t)  # 778

    # ls = m.list(range(1000))
    # t = time.time()
    # processes = []
    # for num in range(4):
    #     process = Process(target=foo, args=(ls,))
    #     process.start()
    #     processes.append(process)
    # for process in processes:
    #     process.join()
    # print('多进程：', time.time() - t)  # 189

    ls = m.list(range(1000))
    t = time.time()
    processes = []
    for num in range(4):
        process = Process(target=my_thread, args=(ls,))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()
    print('多进程,多线程：', time.time() - t)  # 200




