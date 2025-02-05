import requests
import random
import string
import uuid
import threading  # 导入 threading 模块
from loguru import logger  # 导入 loguru

# 将 loguru 日志重定向到标准输出，确保能被 GitHub Actions 捕获
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
        logger.debug(f"URL: {url}, Status Code: {response.status_code}")  # 使用 logger 输出调试信息
        return response.status_code
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None

def worker(ip_file, found_ips):
    """工作线程，负责生成和测试子域名"""
    logger.info(f"Worker thread started: {threading.current_thread().name}")  # 添加线程启动日志
    while len(found_ips) <= 5:  # 检查全局条件
        subdomain = generate_subdomain()
        url = f"https://{subdomain}"
        status = check_status(url)

        if status == 200:
            logger.info(f"{url} is up!")
            with open(ip_file, 'a') as ip_out:  # 使用追加模式
                ip_out.write(url + '\n')
            found_ips.append(url)  # 添加到全局列表
        else:
            logger.debug(f"{url} is down or unreachable.")

    logger.info(f"Worker thread finished: {threading.current_thread().name}")  # 添加线程结束日志

def scan_subdomains():
    ip_file = 'ip.txt'
    ip2_file = 'ip2.txt'

    # 保存 200 状态的域名 (使用线程安全的列表)
    found_ips = []  # 不需要线程安全的列表，因为不再是所有工作线程共享.
    logger.info("Starting subdomain scan...")  # 添加扫描开始日志

    # 创建线程
    threads = []
    NUM_THREADS = 50
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=worker, args=(ip_file, found_ips))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    logger.info("Found more than 5 valid domains, stopping the process.")

if __name__ == "__main__":
    logger.info("Script started") # 脚本开始的日志
    scan_subdomains()
    logger.info("Script completed")  # 脚本结束的日志