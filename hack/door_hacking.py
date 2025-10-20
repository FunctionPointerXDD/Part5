## codyssey part5 - 1 ##
## Mariner_정찬수 ##

import os
import zipfile
import zlib
import string
import time
import datetime
from multiprocessing import Process, Lock
import multiprocessing as mp

ZIPFILE = "emergency_storage_key.zip"
ALPHABET_DIGIT = (string.ascii_lowercase + string.digits).encode('utf-8') # 자리수 36개
LENGTH = 6
N = 36 ** LENGTH
PROCS = 6
STOP = mp.Event()

_cnt = 0

def gen_code(x: int) -> bytes:
    base = len(ALPHABET_DIGIT)
    code = bytearray(LENGTH)

    for pos in range(LENGTH - 1, -1, -1): # 뒤에서부터 채우기 (LENGTH-1, LENGTH-2, ..., 0)
        x, r = divmod(x, base) # ALPHABET_DIGIT을 36진법으로 해석
        code[pos] = ALPHABET_DIGIT[r]

    return bytes(code)

def unlock_zip(pid, lock):
    global _cnt

    try:
        if not zipfile.is_zipfile(ZIPFILE):
            with lock:
                print("The file is not a zip file.")
            os._exit(1)

        with zipfile.ZipFile(ZIPFILE, "r") as zf:
            file_list = zf.namelist()
            if not file_list:
                with lock:
                    print("No files found in the zip.")
                os._exit(1)

            target_file = file_list[0] ## password.txt
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            start = time.time()
            idx = int(N / PROCS * pid)
            end = int(N /PROCS * (pid + 1))
            for i in range(idx, end):
                if STOP.is_set():
                    os._exit(1)
                cur = time.time()
                lapsed = round((cur - start), 2)

                with lock:
                    _cnt += 1

                password = gen_code(i)
                try:
                    ret = zf.read(target_file, pwd=password)
                    if ret:
                        STOP.set()
                        zf.extract(target_file, pwd=password)
                        end = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        msg = f"\nSuccess! The password is: {password.decode()} pid: {pid} Ended at: {end} Lapsed: {lapsed} seconds".encode('utf-8')
                        with lock:
                            os.write(1, msg)
                        os._exit(0)

                except (RuntimeError, zipfile.BadZipFile, zlib.error):
                    msg = f"pid: {pid} Tried: {password} Count: {_cnt} Start: {now} Lapsed: {lapsed}\r".encode('utf-8')
                    with lock:
                        os.write(1, msg)
                    continue
        with lock:
            print("Password not found.")

    except (RuntimeError, KeyboardInterrupt):
        zf.close()
        os._exit(1)

def unlock_zip_main():
    lock = Lock()
    try:
        proc_list = []    
        for rank in range(PROCS):
            p = Process(target=unlock_zip, args=(rank, lock))
            p.start()
            proc_list.append(p)
        for p in proc_list:
            p.join()

    except KeyboardInterrupt:
        print("\r\nMain process stopped by Ctrl-C...")
        STOP.set()
        for p in proc_list:
            p.join()
        for p in proc_list:
            if p.is_alive():
                p.terminate()
    except Exception:
        STOP.set()
        for p in proc_list:
            p.join()
        for p in proc_list:
            if p.is_alive():
                p.terminate()

# 카이사르 암호는 영문자를 특정 숫자 만큼 모두 양의 값만큼 옮겨서(shift) 만드는 암호다.
# 따라서 반대로 옮겨진 값만큼 이동시켜서 의미있는 문장인지 확인하면 된다.
alphabet = string.ascii_uppercase

def caesar_cipher_decode(target_text: str) -> list:
    code_list = []
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
        code_list.append(decoded)
    
    return code_list

def caesar_cipher_main():
    try:
        with open("password.txt", "r", encoding="utf-8") as f:
            encrypted_text = f.read().strip()

        print("암호화된 문자열:", encrypted_text)
        candidated = caesar_cipher_decode(encrypted_text)

        shift_num = int(input("\n정답이라고 생각되는 Shift 번호를 입력하세요: "))
        final_result = candidated[shift_num]

        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_result)

        print("\n최종 해독 결과가 result.txt에 저장되었습니다.")

    except Exception as e:
        print(f"[caesar] Error: {e}")

def main():
    #unlock_zip_main()
    caesar_cipher_main()

if __name__ == "__main__":
    main()
