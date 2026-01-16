# biliup 安装和配置指南

## 问题描述

运行 `youdoub bili upload` 或 `youdoub bili submit` 时出现以下错误：
```
FileNotFoundError: [Errno 2] No such file or directory: 'biliup'
```

这表示系统上未安装 biliup 工具。

## 解决方案

### 1. 安装 biliup

#### 使用 uv (推荐，与项目环境一致)
```bash
cd /path/to/YouDoub
uv pip install biliup
```

#### 或使用 pip
```bash
pip install biliup
```

#### 或使用 Makefile
```bash
cd /path/to/YouDoub
make install-biliup
```

### 2. 验证安装

```bash
biliup --version
```

成功输出类似：
```
biliup x.x.x
```

### 3. 配置 BiliBili 账号

```bash
biliup login
```

按照提示完成登录流程。

### 4. 测试功能

```bash
# 测试上传功能
youdoub bili upload

# 或使用一键投稿
youdoub bili submit --title "测试视频" --desc "测试描述"
```

## 详细说明

### biliup 是什么？

biliup 是 BiliBili 官方的命令行上传工具，支持：
- 视频上传到 BiliBili
- 批量上传
- 字幕文件上传
- 自定义分区、标签等

### 配置文件格式

YouDoub 会自动生成 `work/bili/biliup.yaml` 配置文件，包含：

```yaml
common:
  title: "视频标题"
  desc: "视频描述"
  tid: 123
  tags: ["标签1", "标签2"]

videos:
  - path: "video.mp4"

subtitle:
  path: "out/zh-Hans.srt"
```

### 常见问题

#### 1. 权限问题
如果遇到权限错误，尝试：
```bash
sudo pip install biliup
# 或
pip install --user biliup
```

#### 2. PATH 问题
如果安装后仍找不到命令，可能需要刷新 PATH：
```bash
source ~/.bashrc
# 或重新打开终端
```

#### 3. 网络问题
如果登录时遇到网络问题，尝试使用代理或 VPN。

#### 4. 账号问题
- 确保 BiliBili 账号有上传权限
- 检查账号是否被限制上传

## 自动化安装脚本

你可以创建一个安装脚本 `install_biliup.sh`：

```bash
#!/bin/bash
echo "安装 biliup..."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "请先激活虚拟环境: source .venv/bin/activate"
    exit 1
fi

# 安装 biliup
uv pip install biliup

# 验证安装
if command -v biliup &> /dev/null; then
    echo "✅ biliup 安装成功"
    echo "版本: $(biliup --version)"
    echo ""
    echo "下一步: 配置 BiliBili 账号"
    echo "运行: biliup login"
else
    echo "❌ biliup 安装失败"
    exit 1
fi
```

然后运行：
```bash
chmod +x install_biliup.sh
./install_biliup.sh
```

## 故障排除

如果仍然遇到问题：

1. 检查 Python 版本（需要 Python 3.7+）
2. 确认虚拟环境已激活
3. 查看详细错误信息
4. 尝试重新安装 biliup

安装完成后，你就可以正常使用 YouDoub 的 BiliBili 投稿功能了！🎉