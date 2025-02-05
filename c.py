import requests
import random
import string
import uuid
import threading
from loguru import logger

logger.add(lambda msg: print(msg, end=""), format="{time} {level} {message}")

def generate_subdomain():
    """生成包含 UUID 和指定区域的子域名"""
    uuid_str = str(uuid.uuid4())  # 生成 UUID
    region = "e1-us-east-azure"  # 指定区域
    return f"{uuid_str}.{region}.choreoapps.dev"

def check_status(url):
    """检查 URL 的状态码"""
    try:
        response = requests.get(url, timeout=5)
        logger.debug(f"URL: {url}, Status Code: {response.status_code}")
        return response.status_code
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None

def worker(ip_file, found_ips, lock, stop_flag):
    """工作线程，负责生成和测试子域名"""
    logger.info(f"Worker thread started: {threading.current_thread().name}")
    while len(found_ips) < 1 and not stop_flag.is_set():  # 使用 stop_flag
        subdomain = generate_subdomain()
        url = f"https://{subdomain}"
        status = check_status(url)

        if status == 200:
            logger.info(f"{url} is up!")
            with lock:  # 获取锁，确保线程安全
                with open(ip_file, 'a') as ip_out:
                    ip_out.write(url + '\n')
                found_ips.append(url)
                stop_flag.set()  # 设置 stop_flag，通知其他线程停止
        else:
            logger.debug(f"{url} is down or unreachable.")

    logger.info(f"Worker thread finished: {threading.current_thread().name}")

def scan_subdomains():
    ip_file = 'ip.txt'
    ip2_file = 'ip2.txt'

    # 使用线程锁
    lock = threading.Lock()
    stop_flag = threading.Event() # 使用 threading.Event
    # 保存 200 状态的域名 (使用线程安全的列表)
    found_ips = []

    logger.info("Starting subdomain scan...")

    # 创建线程
    threads = []
    NUM_THREADS = 200
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=worker, args=(ip_file, found_ips, lock, stop_flag))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    logger.info("Found a valid domain, stopping the process.")

if __name__ == "__main__":
    logger.info("Script started")
    scan_subdomains()
    logger.info("Script completed")