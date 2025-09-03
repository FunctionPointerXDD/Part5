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

def main():
    try:
        #unlock_zip()
        caesar_cipher_main()
    except Exception:
        print("Unlock failed")
    except KeyboardInterrupt:
        print("\nCtrl + C interrupted")


if __name__ == "__main__":
    main()
