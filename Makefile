# YouDoub Makefile
# 用于在 Ubuntu 上安装 uv 并管理项目环境

.PHONY: help install-uv init install run clean dev-install test test-bili install-biliup

# 默认目标
help: ## 显示帮助信息
	@echo "YouDoub 项目管理工具"
	@echo ""
	@echo "可用的命令:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-uv: ## 在 Ubuntu 上安装 uv 包管理器
	@echo "正在安装 uv 包管理器..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "uv 已安装，版本: $$(uv --version)"; \
	else \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "请重新启动终端或运行: source ~/.bashrc"; \
	fi

init: ## 初始化项目环境 (需要先安装 uv)
	@echo "初始化项目环境..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "错误: uv 未安装，请先运行 'make install-uv'"; \
		exit 1; \
	fi
	uv venv
	@echo "虚拟环境已创建"

install: ## 安装项目依赖
	@echo "安装项目依赖..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在，请先运行 'make init'"; \
		exit 1; \
	fi
	uv pip install -e .
	@echo "提示: 如需 BiliBili 上传功能，请运行 'make install-biliup'"
	@echo "依赖安装完成"

dev-install: ## 安装开发依赖 (包括测试工具等)
	@echo "安装开发依赖..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在，请先运行 'make init'"; \
		exit 1; \
	fi
	uv pip install -e ".[dev]"

install-biliup: ## 安装 biliup (用于 BiliBili 上传)
	@echo "安装 biliup..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在，请先运行 'make init'"; \
		exit 1; \
	fi
	uv pip install biliup
	@echo "biliup 安装完成！"
	@echo "接下来配置 BiliBili 账号: biliup login"
	@echo "开发依赖安装完成"

run: ## 运行 YouDoub CLI
	@echo "运行 YouDoub..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在，请先运行 'make init' 和 'make install'"; \
		exit 1; \
	fi
	uv run youdoub --help

test: ## 运行测试 (如果有的话)
	@echo "运行测试..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在"; \
		exit 1; \
	fi
	@if [ -d "tests" ] || [ -f "test_*.py" ]; then \
		uv run python -m pytest; \
	else \
		echo "未找到测试文件"; \
	fi

test-bili: ## 测试 BiliBili 投稿功能
	@echo "测试 BiliBili 投稿功能..."
	@if [ ! -d ".venv" ]; then \
		echo "错误: 虚拟环境不存在"; \
		exit 1; \
	fi
	uv run python test_bili_submit.py

clean: ## 清理缓存文件和临时文件
	@echo "清理缓存文件..."
	rm -rf __pycache__ */__pycache__ *.pyc *.pyo .pytest_cache .coverage
	rm -rf work/cache work/out work/subs/*.tmp
	rm -rf .venv  # 可选：删除虚拟环境
	@echo "清理完成"

setup: install-uv init install ## 完整设置环境 (安装 uv + 初始化 + 安装依赖)

# 检查系统要求
check-system: ## 检查系统是否满足要求
	@echo "检查系统要求..."
	@python3 --version | grep -q "Python 3.11\|3.12\|3.13" && echo "✓ Python 版本合适" || echo "✗ 需要 Python >= 3.11"
	@command -v curl >/dev/null 2>&1 && echo "✓ curl 已安装" || echo "✗ 需要安装 curl"
	@echo "系统检查完成"