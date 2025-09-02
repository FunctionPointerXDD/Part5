import zipfile
import multiprocessing as mp
from string import ascii_lowercase, digits

ZIPFILE = "emergency_storage_key.zip"
TARGET = "password.txt"
CHARSET = ascii_lowercase + digits
PASSWORD_LENGTH = 6

def check_password(password, zip_filename, target_file):
    """Check if a password is correct for the zip file."""
    try:
        with zipfile.ZipFile(zip_filename, "r") as zf:
            # Try to read the target file with the password
            zf.read(target_file, pwd=password.encode('utf-8'))
            return password
    except (RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile):
        # These are the expected exceptions for wrong passwords
        return None
    except Exception as e:
        # Catch zlib errors and other exceptions that indicate wrong password
        if "Bad password" in str(e) or "password" in str(e).lower():
            return None
        if "zlib.error" in str(type(e)):
            return None
        # Re-raise unexpected exceptions
        raise

def password_generator(charset, length, start_index, end_index):
    """Generate passwords from a specific range of the search space."""
    total_combinations = len(charset) ** length
    for i in range(start_index, end_index):
        if i >= total_combinations:
            break
        # Convert the index to a password
        password = []
        n = i
        for _ in range(length):
            password.append(charset[n % len(charset)])
            n //= len(charset)
        yield ''.join(password)

def worker_process(worker_id, total_workers, charset, length, zip_filename, target_file, result_queue):
    """Worker process that checks a portion of the password space."""
    total_combinations = len(charset) ** length
    chunk_size = total_combinations // total_workers
    start_index = worker_id * chunk_size
    end_index = start_index + chunk_size if worker_id < total_workers - 1 else total_combinations
    
    print(f"Worker {worker_id} checking range {start_index} to {end_index-1}")
    
    for password in password_generator(charset, length, start_index, end_index):
        # Check if we should stop (password found by another worker)
        if not result_queue.empty():
            return
            
        result = check_password(password, zip_filename, target_file)
        if result is not None:
            result_queue.put(result)
            return
    
    result_queue.put(None)

def main():
    num_workers = min(mp.cpu_count(), 8)  # Limit to 8 workers to avoid overhead
    result_queue = mp.Queue()
    
    workers = []
    for i in range(num_workers):
        worker = mp.Process(
            target=worker_process,
            args=(i, num_workers, CHARSET, PASSWORD_LENGTH, ZIPFILE, TARGET, result_queue)
        )
        workers.append(worker)
        worker.start()
    
    # Wait for results
    found_password = None
    completed_workers = 0
    while completed_workers < num_workers and found_password is None:
        try:
            result = result_queue.get(timeout=1)
            if result is not None:
                found_password = result
            completed_workers += 1
        except:
            # Timeout, check if any workers are still alive
            alive_workers = sum(1 for w in workers if w.is_alive())
            if alive_workers == 0:
                break
    
    # Terminate all workers if password found
    if found_password:
        print(f"✅ Password found: {found_password}")
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
    else:
        print("❌ Password not found")
    
    for worker in workers:
        worker.join()

if __name__ == "__main__":
    main()