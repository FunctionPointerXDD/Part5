## codyssey part5 - 1 ##
## Mariner_정찬수 ##

import os
import zipfile
import zlib
import string
import time
import datetime
from multiprocessing import Process
import multiprocessing as mp

ZIPFILE = "emergency_storage_key.zip"
ALPHABET_DIGIT = string.ascii_lowercase + string.digits # 자리수 36개
LENGTH = 6
N = 36 ** LENGTH
PROCS = 6
STOP = mp.Event()

def gen_code(x: int):
    base = len(ALPHABET_DIGIT)
    code = []

    for _ in range(LENGTH):
        x, r = divmod(x, base) # ALPHABET_DIGIT을 36진법으로 해석
        code.append(ALPHABET_DIGIT[r])

    return reversed(code)

def unlock_zip(pid: int):
    if not zipfile.is_zipfile(ZIPFILE):
        print("The file is not a zip file.")
        os._exit(1)

    with zipfile.ZipFile(ZIPFILE, "r") as zf:
        file_list = zf.namelist()
        if not file_list:
            print("No files found in the zip.")
            os._exit(1)

        cnt = 0
        target_file = file_list[0] ## password.txt
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start = time.time()
        idx = int(N / PROCS * pid)
        for i in range(idx, N):
            if STOP.is_set():
                os._exit(0)
            candidate = gen_code(i)
            cur = time.time()
            lapsed = round((cur - start), 2)
            cnt += 1

            password = "".join(candidate).encode('utf-8')   
            try:
                ret = zf.read(target_file, pwd=password)
                if ret:
                    zf.extract(target_file, pwd=password)
                    end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"\nSuccess! The password is: {password.decode()} Ended at: {end} Lapsed: {lapsed} seconds")
                    STOP.set()
                    os._exit(0)

            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                print(f"pid: {pid} Tried: {password} Count: {cnt} Start: {now} Lapsed: {lapsed}", end='\r')
                continue
            except (KeyboardInterrupt, Exception):
                STOP.set()
                os._exit(1)
    print("Password not found.")
    os._exit(0)

def unlock_zip_main():
    try:
        proc_list = []    
        for rank in range(PROCS):
            p = Process(target=unlock_zip, args=(rank,))
            p.start()
            proc_list.append(p)
        for p in proc_list:
            p.join()

    except KeyboardInterrupt:
        for p in proc_list:
            p.join()
    except Exception:
        for p in proc_list:
            p.join()

# 카이사르 암호는 영문자를 특정 숫자 만큼 모두 양의 값만큼 옮겨서(shift) 만드는 암호다.
# 따라서 반대로 옮겨진 값만큼 이동시켜서 의미있는 문장인지 확인하면 된다.
def caesar_cipher_decode(target_text: str):
    alphabet = string.ascii_uppercase

    for shift in range(len(alphabet)):  # 0 ~ 25
        decoded = ""
        for char in target_text:
            if char.isalpha():
                is_upper = char.isupper()
                base = ord('A') if is_upper else ord('a')
                decoded += chr((ord(char) - base - shift) % 26 + base) # 파이썬에서는 모드연산이 음수도 가능(자동으로 양수로 바꿔줌)
            else:
                decoded += char
        print(f"[Shift {shift}] {decoded}")

def caesar_cipher_main():
    try:
        with open("password.txt", "r", encoding="utf-8") as f:
            encrypted_text = f.read().strip()

        print("암호화된 문자열:", encrypted_text)
        caesar_cipher_decode(encrypted_text)

        shift_num = int(input("\n정답이라고 생각되는 Shift 번호를 입력하세요: "))

        final_result = ""
        for char in encrypted_text:
            if char.isalpha():
                is_upper = char.isupper()
                base = ord('A') if is_upper else ord('a')
                final_result += chr((ord(char) - base - shift_num) % 26 + base)
            else:
                final_result += char

        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_result)

        print("\n최종 해독 결과가 result.txt에 저장되었습니다.")

    except Exception as e:
        print(f"[caesar] Error: {e}")

def main():
    unlock_zip_main()
    caesar_cipher_main()

if __name__ == "__main__":
    main()
