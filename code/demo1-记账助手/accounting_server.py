import json
import os
from pathlib import Path
from datetime import datetime
from typing import Annotated

from pydantic import Field
from mcp.server.fastmcp import FastMCP

# 创建一个 MCP 服务器；host=0.0.0.0 让 Docker 里的 Dify 能访问到宿主机
mcp = FastMCP(
    "记账小助手",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8000")),
)

# 账目存到脚本同目录下的 expenses.json
DATA_FILE = Path(__file__).parent / "expenses.json"


def _load():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def _save(records):
    DATA_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8")


@mcp.tool()
def add_expense(
    amount: Annotated[float, Field(description="金额，单位元，如 35.5")],
    category: Annotated[str, Field(description="消费分类，如 餐饮/交通/购物")],
    note: Annotated[str, Field(description="备注说明，可选，默认空")] = "",
) -> str:
    """记一笔账。amount 金额(元)，category 分类(如 餐饮/交通)，note 备注(可选)。"""
    records = _load()
    records.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "amount": amount,
        "category": category,
        "note": note,
    })
    _save(records)
    return f"已记录：{category} {amount} 元（{note or '无备注'}）"


@mcp.tool()
def list_expenses(
    category: Annotated[
        str, Field(description="按分类过滤，如 餐饮；留空则列出全部账目")
    ] = "",
) -> str:
    """列出账目。传 category 只看某分类；不传则列出全部。"""
    records = _load()
    if category:
        records = [r for r in records if r["category"] == category]
    if not records:
        return "暂无记录。"
    return "\n".join(
        f'{r["date"]} | {r["category"]} | {r["amount"]}元 | {r["note"]}'
        for r in records)


@mcp.tool()
def summary(
    category: Annotated[
        str, Field(description="只统计某个分类，如 餐饮；留空则统计总支出与各分类合计")
    ] = "",
) -> str:
    """统计支出。不传 category 则统计总支出和各分类合计；传 category 只统计该分类。"""
    records = _load()
    if not records:
        return "暂无记录。"
    if category:
        records = [r for r in records if r["category"] == category]
        if not records:
            return f"分类「{category}」暂无记录。"
        total = sum(r["amount"] for r in records)
        return f"{category} 共支出：{total} 元（{len(records)} 笔）"
    total = sum(r["amount"] for r in records)
    by_cat = {}
    for r in records:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["amount"]
    lines = [f"总支出：{total} 元", "分类明细："]
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        lines.append(f"  {cat}：{amt} 元")
    return "\n".join(lines)


@mcp.tool()
def delete_last() -> str:
    """删除最近记的一笔账。"""
    records = _load()
    if not records:
        return "暂无记录，无法删除。"
    removed = records.pop()
    _save(records)
    return f"已删除最近一笔：{removed['category']} {removed['amount']} 元（{removed['note'] or '无备注'}）"


if __name__ == "__main__":
    # transport 由环境变量控制：
    #   stdio          —— 本地调试 
    #   sse            —— 接入 Dify（默认），通过 URL 连接
    #   streamable-http—— 较新的 HTTP 传输
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport)
