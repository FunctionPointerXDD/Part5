## codyssey part5 - 1 ##
## Mariner_정찬수 ##

import zipfile
import zlib
import itertools
import string
import time
import datetime

ZIPFILE = "emergency_storage_key.zip"
LENGTH = 6

def unlock_zip():
    chars = string.ascii_lowercase + string.digits
    if not zipfile.is_zipfile(ZIPFILE):
        print("The file is not a zip file.")
        return

    with zipfile.ZipFile(ZIPFILE, "r") as zf:
        file_list = zf.namelist()
        if not file_list:
            print("No files found in the zip.")
            return

        cnt = 0
        target_file = file_list[0] ## password.txt
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start = time.time()
        for candidate in itertools.product(chars, repeat=LENGTH):
            cur = time.time()
            lapsed = round((cur - start), 2)
            cnt += 1

            # password = "m" + "".join(candidate)
            # password = password.encode('utf-8')
            password = "".join(candidate).encode('utf-8')   
            try:
                ret = zf.read(target_file, pwd=password)
                if ret:
                    zf.extract(target_file, pwd=password)
                    end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"\nSuccess! The password is: {password.decode()} Ended at: {end} Lapsed: {lapsed} seconds")
                    return

            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                print(f"Tried: {password} Count: {cnt} Start: {now} Lapsed: {lapsed}", end='\r')
                continue
            except Exception:
                return
    print("Password not found.")
    return

def main():
    try:
        unlock_zip()
    except Exception:
        print("Unlock failed")
    except KeyboardInterrupt:
        print("\nCtrl + C interrupted")


if __name__ == "__main__":
    main()
