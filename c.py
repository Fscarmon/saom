import requests
import random
import string
import uuid
import threading  # 导入 threading 模块

def generate_subdomain():
    """生成包含 UUID 和指定区域的子域名"""
    uuid_str = str(uuid.uuid4())  # 生成 UUID
    region = "e1-us-east-azure"  # 指定区域
    return f"{uuid_str}.{region}.choreoapps.dev"

def check_status(url):
    """检查 URL 的状态码"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def worker(ip_file, found_ips):
    """工作线程，负责生成和测试子域名"""
    while len(found_ips) <= 5:  # 检查全局条件
        subdomain = generate_subdomain()
        url = f"https://{subdomain}"
        status = check_status(url)

        if status == 200:
            print(f"{url} is up!")
            with open(ip_file, 'a') as ip_out:  # 使用追加模式
                ip_out.write(url + '\n')
            found_ips.append(url)  # 添加到全局列表

def scan_subdomains():
    ip_file = 'ip.txt'
    ip2_file = 'ip2.txt'

    # 保存 200 状态的域名 (使用线程安全的列表)
    found_ips = []  # 不需要线程安全的列表，因为不再是所有工作线程共享.

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

    print("Found more than 5 valid domains, stopping the process.")

if __name__ == "__main__":
    scan_subdomains()