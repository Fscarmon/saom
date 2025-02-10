import requests
import random
import string
import threading
import time
from loguru import logger
import configparser

logger.add(lambda msg: print(msg, end=""), format="{time} {level} {message}")

def generate_subdomain():
    """生成以 .freewebhostmost.com 结尾，前缀为 3 到 6 个随机字母数字组合（大小写随机）的域名"""
    prefix_length = random.randint(3, 6)  # 随机生成 3 到 6 的数字
    characters = string.ascii_letters + string.digits  # 所有字母（大小写）和数字
    prefix = ''.join(random.choice(characters) for _ in range(prefix_length))  # 生成随机前缀
    return f"{prefix}.freewebhostmost.com"

def check_status(url):
    """检查 URL 的状态码"""
    try:
        response = requests.get(url, timeout=5)
        logger.debug(f"URL: {url}, Status Code: {response.status_code}")
        return response.status_code
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None

def worker(ip_file, found_ips, lock, stop_flag, max_ips, end_time):
    """工作线程，负责生成和测试子域名"""
    logger.info(f"Worker thread started: {threading.current_thread().name}")
    while len(found_ips) < max_ips and not stop_flag.is_set() and time.time() < end_time:
        subdomain = generate_subdomain()
        url = f"https://{subdomain}"
        status = check_status(url)

        if status == 200:
            logger.info(f"{url} is up!")
            with lock:
                with open(ip_file, 'a') as ip_out:
                    ip_out.write(url + '\n')
                found_ips.append(url)
                if len(found_ips) >= max_ips: #检查是否达到最大数量
                    stop_flag.set()
        else:
            logger.debug(f"{url} is down or unreachable.")

    logger.info(f"Worker thread finished: {threading.current_thread().name}")

def test_sub_paths(ip_file, ip2_file):
    """测试 ip.txt 中的域名 + /sub 是否返回 200，如果是则保存到 ip2.txt"""
    with open(ip_file, 'r') as ip_in:
        for line in ip_in:
            domain = line.strip()
            sub_url = f"{domain}/sub"
            status = check_status(sub_url)
            if status == 200:
                logger.info(f"{sub_url} is up!")
                with open(ip2_file, 'a') as ip2_out:
                    ip2_out.write(domain + '\n') # 只保存域名本身
            else:
                logger.debug(f"{sub_url} is down or unreachable.")

def scan_subdomains(max_ips=100, time_limit_minutes=30):
    ip_file = 'ip.txt'
    ip2_file = 'ip2.txt'

    # 使用线程锁
    lock = threading.Lock()
    stop_flag = threading.Event()
    # 保存 200 状态的域名 (使用线程安全的列表)
    found_ips = []

    logger.info("Starting subdomain scan...")

    # 计算结束时间
    end_time = time.time() + time_limit_minutes * 60  # 秒

    # 创建线程
    threads = []
    NUM_THREADS = 50
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=worker, args=(ip_file, found_ips, lock, stop_flag, max_ips, end_time))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    logger.info("Found max valid domains, stopping the process.")
    if time.time() < end_time: # Only run if time remains
        logger.info("Starting subdomain /sub check...")
        test_sub_paths(ip_file, ip2_file)
        logger.info("subdomain /sub check finished.")
    else:
        logger.info("Time limit reached, skipping /sub check.")

    logger.info("Scan finished.") # General scan finished message


if __name__ == "__main__":
    logger.info("Script started")
    scan_subdomains()
    logger.info("Script completed")
