# 记账小助手 MCP 服务器（接入 Dify）

一个基于 **MCP（Model Context Protocol，模型上下文协议）** 的记账服务器示例。它给 AI 装上“动手”的能力：真正帮你记一笔账、查账目、做统计，数据保存在本地 `expenses.json` 文件里。本文档说明如何把它**接入 Dify**，作为应用的“外挂能力”使用。

> MCP 就像 AI 世界的“USB-C 接口”——工具按统一标准实现一次，所有支持 MCP 的 AI/平台都能即插即用。服务器是**被动的工具箱**，由模型决定何时调用、传什么参数。

## 功能（工具列表）

| 工具 | 说明 |
| --- | --- |
| `add_expense(amount, category, note="")` | 记一笔账，写入 `expenses.json` |
| `list_expenses(category="")` | 列出账目，可按分类过滤 |
| `summary(category="")` | 统计总支出与各分类合计；传分类则只统计该类 |
| `delete_last()` | 删除最近记的一笔账 |

## 与接入 Claude 的区别

- **Claude 桌面端**：通过 `stdio` 启动本地脚本（`mcp install` 一键安装）。
- **Dify**：通过 **URL** 连接，需要服务器以 **SSE / Streamable HTTP** 方式作为网络服务跑起来。

因此本服务器默认用 `sse` 传输启动，并监听 `0.0.0.0:8000`，方便 Docker 里的 Dify 访问宿主机。

## 环境要求

- Python ≥ 3.10
- 安装官方 MCP 开发包：

```bash
pip install "mcp[cli]"
```

> ⚠️ `"mcp[cli]"` 要带引号，否则 zsh 会把方括号当通配符报错。

## 启动服务器

```bash
# 默认 SSE 传输，监听 0.0.0.0:8000，SSE 端点为 /sse
python accounting_server.py
```

可用环境变量调整：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MCP_TRANSPORT` | `sse` | 传输方式：`sse` / `streamable-http` / `stdio` |
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |

启动后 SSE 接入地址为：`http://<宿主机地址>:8000/sse`

## 接入 Dify

1. 启动本服务器：`python accounting_server.py`
2. 在 Dify 中进入 **工具（Tools）→ MCP**，点击 **添加 MCP 服务器**。
3. 填写服务器 **URL**：
   - Dify 用 Docker 部署（本仓库 `demo1` 即是）时，容器访问宿主机要用：
     `http://host.docker.internal:8000/sse`
   - 若 Dify 与服务器在同一台机器、非容器环境：
     `http://127.0.0.1:8000/sse`
4. 保存后，Dify 会自动拉取工具清单（`add_expense`、`list_expenses`、`summary`、`delete_last`）。
5. 在 **Agent / 工作流** 应用中把这些工具勾选进来即可使用。

> 💡 macOS/Windows 的 Docker Desktop 默认支持 `host.docker.internal`；Linux 上可能需要在 `docker-compose` 中加 `extra_hosts: ["host.docker.internal:host-gateway"]`，或直接填宿主机局域网 IP。

## 在 Dify 里用起来

在 Agent 应用中用大白话指挥：

- “帮我记一笔，午饭 35 元，餐饮” → 调用 `add_expense`
- “这个月一共花了多少？” → 调用 `summary`
- “看看餐饮都花在哪了” → 调用 `list_expenses`
- “餐饮一共花了多少？” → 调用 `summary(category="餐饮")`
- “删掉刚才记错的那笔” → 调用 `delete_last`

## 本地调试（可选）

接入 Dify 前，可先用 Inspector 逐个测试工具：

```bash
mcp dev accounting_server.py
```

## 工作原理

模型完全靠函数的三件信息读懂工具：

1. **函数名** → 工具名（`add_expense`）
2. **参数类型注解** → 该传什么（`amount: float`）
3. **docstring 说明** → 这个工具是干嘛的

AI 负责“听懂和决策”，服务器负责“干活”，MCP 协议在中间传话。
