#!/usr/bin/env python3
"""
网络诊断脚本 - 检查 Hugging Face Hub 连接问题
"""

import os
import sys
import subprocess
import urllib.request
import socket
from pathlib import Path

def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f"\n🔍 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ 成功: {result.stdout.strip()}")
            return True, result.stdout.strip()
        else:
            print(f"❌ 失败: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False, str(e)

def test_dns_resolution():
    """测试 DNS 解析"""
    print("\n🔍 测试 DNS 解析...")
    try:
        ip = socket.gethostbyname('huggingface.co')
        print(f"✅ huggingface.co 解析到: {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS 解析失败: {e}")
        return False

def test_http_connection():
    """测试 HTTP 连接"""
    print("\n🔍 测试 HTTP 连接...")
    try:
        # 设置超时
        req = urllib.request.Request('https://huggingface.co', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ HTTP 连接成功 (状态码: {response.getcode()})")
            return True
    except Exception as e:
        print(f"❌ HTTP 连接失败: {e}")
        return False

def test_hf_api_connection():
    """测试 Hugging Face API 连接"""
    print("\n🔍 测试 Hugging Face API 连接...")
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        # 尝试获取用户信息 (这是一个轻量级请求)
        user = api.whoami()
        print("✅ HF API 连接成功"        return True
    except ImportError:
        print("❌ huggingface_hub 未安装")
        return False
    except Exception as e:
        print(f"❌ HF API 连接失败: {e}")
        return False

def test_whisper_model_download():
    """测试 Whisper 模型下载"""
    print("\n🔍 测试 Whisper 模型下载 (tiny)...")
    try:
        from faster_whisper import WhisperModel
        # 尝试下载 tiny 模型
        model = WhisperModel('tiny', download_root='./models', local_files_only=False)
        print("✅ Tiny 模型下载成功"        return True
    except ImportError:
        print("❌ faster_whisper 未安装")
        return False
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        return False

def check_environment():
    """检查环境变量"""
    print("\n🔍 检查环境变量...")
    env_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'HF_ENDPOINT', 'HF_HUB_CACHE', 'HF_HOME', 'HUGGINGFACE_HUB_CACHE'
    ]

    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} = {value}")
        else:
            print(f"⚠️  {var} 未设置")

def check_firewall():
    """检查防火墙设置"""
    print("\n🔍 检查防火墙...")
    # 检查是否能连接到常用端口
    test_ports = [
        ('huggingface.co', 443),  # HTTPS
        ('huggingface.co', 80),   # HTTP
    ]

    for host, port in test_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                print(f"✅ 端口 {host}:{port} 可访问")
            else:
                print(f"❌ 端口 {host}:{port} 被阻止")
        except Exception as e:
            print(f"❌ 端口检查失败 {host}:{port}: {e}")

def main():
    print("🚀 YouDoub 网络诊断工具")
    print("=" * 50)

    # 检查基本网络
    run_command("ping -c 3 8.8.8.8", "测试基本网络连接")
    run_command("curl -I https://www.google.com", "测试 HTTPS 连接")

    # DNS 测试
    test_dns_resolution()

    # HTTP 连接测试
    test_http_connection()

    # HF API 测试
    test_hf_api_connection()

    # 环境变量检查
    check_environment()

    # 防火墙检查
    check_firewall()

    # Whisper 下载测试
    test_whisper_model_download()

    print("\n" + "=" * 50)
    print("📋 诊断完成")
    print("\n🔧 建议解决方案:")
    print("1. 如果 DNS 失败: 检查 DNS 设置或使用 8.8.8.8")
    print("2. 如果 HTTP 失败: 检查防火墙或代理设置")
    print("3. 如果 HF API 失败: 设置 HF_ENDPOINT=https://hf-mirror.com")
    print("4. 如果模型下载失败: 尝试使用代理或 VPN")
    print("5. 设置环境变量:")
    print("   export HF_ENDPOINT=https://hf-mirror.com")
    print("   export HF_HUB_CACHE=./models")

if __name__ == "__main__":
    main()