"""
ChatKG 一键启动脚本
启动后端 API 服务器和前端开发服务器，然后打开浏览器。
"""
import subprocess
import time
import sys
import os
import webbrowser
import signal
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = BASE_DIR
FRONTEND_DIR = os.path.join(BASE_DIR, "chat-kg")

processes = []


def cleanup(signum=None, frame=None):
    """停止所有子进程。"""
    print("\n正在停止服务...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
    print("服务已停止。")
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, cleanup)


def port_in_use(port):
    """检查端口是否被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_port(port):
    """结束占用指定端口的进程 (Windows)。"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, shell=True
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True, shell=True)
                return True
    except Exception:
        pass
    return False


def check_python_deps():
    """检查 Python 依赖是否安装。"""
    required = ["flask", "flask_cors", "opencc", "jieba", "requests"]
    missing = []
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    return missing


def wait_for_server(url, timeout=30):
    """等待后端服务器就绪。"""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    print("=" * 40)
    print("  ChatKG - 知识图谱问答系统")
    print("=" * 40)
    print()

    # 检查 Python 依赖
    print("[检查] Python 依赖...")
    missing = check_python_deps()
    if missing:
        print(f"  缺少依赖: {', '.join(missing)}")
        print(f"  请运行: pip install {' '.join(missing)}")
        sys.exit(1)
    print("  依赖完整")
    print()

    # 检查前端依赖
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print("[检查] 前端依赖未安装，正在安装...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, shell=True)
    else:
        print("[检查] 前端依赖已安装")
    print()

    # 检查端口并处理冲突
    for port, name in [(8000, "后端"), (5173, "前端")]:
        if port_in_use(port):
            print(f"[端口] {name}端口 {port} 被占用，正在释放...")
            kill_port(port)
            time.sleep(2)
            if port_in_use(port):
                print(f"  无法释放端口 {port}，请手动关闭占用该端口的程序")
                sys.exit(1)
            else:
                print(f"  端口 {port} 已释放")
    print()

    # 启动后端
    print("[1/2] 启动后端服务器 (端口 8000)...")
    backend = subprocess.Popen(
        [sys.executable, "server/main_api.py"],
        cwd=BACKEND_DIR,
    )
    processes.append(backend)

    # 等待后端就绪
    print("      等待服务器就绪...")
    if wait_for_server("http://localhost:8000/", timeout=60):
        print("      后端服务器已就绪")
    else:
        print("      警告: 后端服务器启动超时，继续启动前端...")
    print()

    # 启动前端
    print("[2/2] 启动前端 (端口 5173)...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
    )
    processes.append(frontend)
    time.sleep(5)

    # 打开浏览器
    url = "http://localhost:5173"
    print()
    print("=" * 40)
    print("  启动完成！")
    print(f"  前端: {url}")
    print("  后端: http://localhost:8000")
    print("=" * 40)
    print()
    print("按 Ctrl+C 停止所有服务")
    print()

    webbrowser.open(url)

    # 等待任意子进程退出
    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"进程退出 (code {p.poll()})，正在停止所有服务...")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
