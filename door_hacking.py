## codyssey part5 - 1 ##
## Mariner_정찬수 ##

import zipfile
import itertools
from multiprocessing import Process
import multiprocessing as mp


ZIPFILE = "emergency_storage_key.zip"
TARGET  = "password.txt"
STOP = mp.Event()


def unlock_zip():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    with zipfile.ZipFile(ZIPFILE, "r") as zf:
        for candidate in itertools.product(chars, repeat=6):
            if STOP.is_set():
                break
            password = "".join(candidate).encode("utf-8")
            try:
                ans = zf.read(TARGET, pwd=password)
                if ans:
                    zf.extract(TARGET, path="./unzipped", pwd=password)
                    print("✅ Unlock success:", password.decode())
                    STOP.set()
                    break
            except Exception:
                continue

def main():
    try:
        procs = []
        for _ in range(12):
            procs.append(Process(target=unlock_zip))
        for p in procs:
            p.start()
        for p in procs:
            p.join()

    except KeyboardInterrupt:
        print('\nMain procs stoped by Ctrl + C')
        STOP.set()
        for p in procs:
            p.join()
    except Exception as e:
        print(f"Error: {e}")
        STOP.set()
        for p in procs:
            p.join()

if __name__ == "__main__":
    main()


        

