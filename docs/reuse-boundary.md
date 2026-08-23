# 复用边界与来源审计

本文档用于防止把第三方项目的实现误当作本项目代码。当前仓库历史中，
`201309c` 及其祖先来自 `https://github.com/minihellboy/factorminer.git`；
`062ab95` 在该代码基础上增加了 RSI 递归研究层。MIT 许可证允许在满足
归属条件的情况下复用代码，但许可证不等于项目所有者授权我们把第三方
仓库整体发布成自己的项目。因此，后续重构默认采用“借鉴契约，独立实现”
原则。

## 可以复用

以下内容可以作为设计输入，不能直接复制实现：

| 内容 | 复用方式 | 进入新项目的形态 |
| --- | --- | --- |
| Wilder RSI / RMA 数学定义 | 使用公开算法并重新实现 | `rsi_harness/backtest.py` 的独立实现与测试 |
| 因果信号与下一周期收益约定 | 复用研究原则 | `contracts.py`、回测测试和实验规范 |
| 时间切分、费用、换手、回撤、Sharpe 指标 | 复用指标语义 | 新的 metrics 模块，逐项补测试 |
| 内容寻址证据包 | 复用“规范化 JSON + SHA-256”思路 | 新的 evidence schema 和验证器 |
| 代际、试验预算、异常、能力提案 | 复用状态机概念 | 新的 campaign ledger，不复制上游账本代码 |
| MCP 的 stdio / streamable HTTP 传输 | 复用协议标准 | 只实现本项目需要的 RSI 工具 |
| DigitalScholar 的工具语义 | 调用其公开 MCP 接口 | Harness 编排 `search`、`novelty`、`orient` 等工具 |
| DeepSeek Harness 的 patch 配置形式 | 遵循 Harness 配置协议 | 使用环境变量和本项目工具名的最小 patch |

## 不能直接复用

以下内容来自上游仓库，必须删除、重写，或在获得明确授权并完成第三方
归属后才可继续保留：

| 路径/资产 | 原因 | 处理结论 |
| --- | --- | --- |
| `factorminer/` 的大部分 250 个 Python 文件 | 上游实现，不是本项目独立实现 | 新项目不直接携带；只逐项重写必要能力 |
| `factorminer/tests/` 上游测试 | 测试与上游内部实现、命名和行为绑定 | 删除；只保留针对新契约重写的测试 |
| `factorminer/configs/`、`data/`、`examples/` | 上游配置、样例和数据资产 | 删除或改为本项目原创最小样例 |
| `scripts/run_demo.py`、`run_phase2_benchmark.py` 等 | 上游工作流脚本 | 不迁移；重新编写 RSI CLI/实验脚本 |
| `docs/architecture.md` 等上游文档 | 描述上游产品和论文复现范围 | 不作为本项目文档使用；重新撰写 |
| `integrations/factor-researcher/` 原有集成 | 上游 Agent 部署资产，包含上游工具契约 | 只保留本项目 RSI Skill 的原创部分 |
| 原 `README.md`、`CONTRIBUTING.md`、`pyproject.toml` | 含上游作者、仓库地址和能力声明 | 全部重写 |
| 原 `LICENSE` 中的作者归属 | 不能把上游作者信息改成自己的 | 新项目需单独确定许可证和归属文件 |
| 上游论文、因子目录、110 因子 catalog | 第三方项目内容和研究资产 | 不纳入 RSI 项目 |

## 当前代码的判定

### 可作为重写起点的原创代码

`rsi_harness/` 是本次会话新写的代码，但仍需以本边界为约束进行逐项审查：

- `backtest.py`：RSI 和因果回测逻辑可以保留，需继续补充边界测试。
- `contracts.py`：实验契约可以保留，需补充时间戳而不是只用整数偏移。
- `campaign.py`：代际账本可以保留，需补充并发写保护和版本迁移。
- `evidence.py`：证据哈希逻辑可以保留，需补充 schema 校验。
- `agent.py`：规划器接口可以保留，Harness 输入输出协议需固定版本。
- `mcp_server.py`：只保留 RSI 工具，不暴露上游 FactorMiner 工具。

### 已移除的依赖

上游 `factorminer/` 目录、测试、脚本、文档和配置已从当前工作树移除。
它们不再是本项目的运行时依赖，也不再作为本项目质量证明。

## 清理后的目标目录

```text
FactorMiner/
├── rsi_harness/          # 独立实现：RSI、实验、证据、代际账本、MCP
├── integrations/         # 仅保留 DeepSeek Harness 的 RSI 配置/Skill
├── config/               # 本项目配置
├── data/                 # 原创最小测试数据或不入库的数据说明
├── docs/                 # 本项目协议、威胁边界、复现说明
├── pyproject.toml        # 只声明本项目依赖和入口
└── README.md             # 只描述本项目能力
```

清理动作会删除大量文件并改变远端 `main` 的当前树，属于仓库级变更。本次
清理已得到用户确认；提交前仍会执行文件清单、静态检查和测试核验。旧提交
历史不做强制重写，以保留可审计的来源记录。
