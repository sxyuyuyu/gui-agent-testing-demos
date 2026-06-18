# 考题四完整版代码：基于 PRD 召回知识库生成测试点

## 说明

这是在轻量 Demo 基础上整理出的工程化版本，使用纯 Python 标准库实现，便于答辩、演示和二次扩展。

核心能力：

- PRD 解析：提取功能点、业务实体、规则、边界条件、异常条件、关键词。
- 查询生成：基于功能点、边界、异常和关键词生成检索 query。
- 混合检索：关键词检索、向量相似、历史缺陷相似、规则命中综合打分。
- 知识重排：输出命中的知识、分数明细、匹配关键词。
- 测试点生成：生成结构化 JSON 测试点。
- 质量校验：输出需求风险、覆盖风险和测试点质量风险。

## 目录结构

```text
prd_testpoint_agent/
  config.py          配置和检索权重
  schema.py          数据结构定义
  text_utils.py      文本处理与分词
  prd_parser.py      PRD 解析
  knowledge_base.py  知识库加载
  retriever.py       混合检索
  generator.py       测试点生成
  validator.py       质量校验
  pipeline.py        编排 pipeline
  cli.py             命令行入口

full_prd_testpoint_agent.py  完整版入口
run_full_agent.ps1           Windows 启动脚本
data/sample_prd.txt          示例 PRD
data/prds/                   多业务 PRD 样例目录
data/knowledge_base.json     示例知识库
output/full_test_points.json 完整版输出
```

## 运行方式

Windows 推荐：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_full_agent.ps1
```

如果本机已安装 Python：

```bash
python full_prd_testpoint_agent.py --prd data/sample_prd.txt --kb data/knowledge_base.json --out output/full_test_points.json
```

## 如何切换要测试的 PRD 文件

推荐方式是在命令里修改 `--prd` 参数，不需要改代码。

例如测试退款 PRD：

```bash
python full_prd_testpoint_agent.py --prd data/prds/prd_refund_flow.txt --kb data/knowledge_base.json --out output/refund_test_points.json --title 订单退款 --prd-id PRD_REFUND_001
```

测试优惠券 PRD：

```bash
python full_prd_testpoint_agent.py --prd data/prds/prd_coupon_center.txt --kb data/knowledge_base.json --out output/coupon_test_points.json --title 优惠券领取与使用 --prd-id PRD_COUPON_001
```

测试登录风控 PRD：

```bash
python full_prd_testpoint_agent.py --prd data/prds/prd_login_risk_control.txt --kb data/knowledge_base.json --out output/login_risk_test_points.json --title 登录风控与验证码 --prd-id PRD_LOGIN_RISK_001
```

测试通知设置 PRD：

```bash
python full_prd_testpoint_agent.py --prd data/prds/prd_notification_setting.txt --kb data/knowledge_base.json --out output/notification_test_points.json --title 消息通知设置 --prd-id PRD_NOTIFICATION_001
```

如果使用 Windows 脚本运行，可以修改这个文件里的 PRD 路径：

- `run_full_agent.ps1`

当前脚本默认执行：

```powershell
full_prd_testpoint_agent.py --out output/full_test_points.json
```

你可以改成：

```powershell
full_prd_testpoint_agent.py --prd data/prds/prd_refund_flow.txt --out output/refund_test_points.json --title 订单退款 --prd-id PRD_REFUND_001
```

如果想修改程序默认 PRD 路径，可以改这里：

- `prd_testpoint_agent/cli.py`
- 参数：`parser.add_argument("--prd", default="data/sample_prd.txt", ...)`

优先级建议：

1. 临时测试：改命令里的 `--prd` 参数。
2. 固定脚本演示：改 `run_full_agent.ps1`。
3. 修改默认行为：改 `prd_testpoint_agent/cli.py`。

## 已提供的 PRD 样例

- `data/sample_prd.txt`：会员自动续费。
- `data/prds/prd_refund_flow.txt`：订单退款。
- `data/prds/prd_coupon_center.txt`：优惠券领取与使用。
- `data/prds/prd_login_risk_control.txt`：登录风控与验证码。
- `data/prds/prd_notification_setting.txt`：消息通知设置。

## 可配置参数

```bash
python full_prd_testpoint_agent.py \
  --prd data/sample_prd.txt \
  --kb data/knowledge_base.json \
  --out output/full_test_points.json \
  --top-k 8 \
  --keyword-weight 0.35 \
  --vector-weight 0.35 \
  --defect-weight 0.20 \
  --rule-weight 0.10
```

## 输出说明

输出 JSON 包含：

- `summary`：功能点数、测试点数、知识命中数、风险数。
- `requirementModel`：PRD 结构化解析结果。
- `retrievedKnowledge`：混合检索召回结果，包含综合分和分项得分。
- `testPoints`：最终结构化测试点。
- `risks`：需求不明确、覆盖缺失或测试点质量风险。

## 工程化亮点

- 保留需求原文引用，测试点可追溯。
- 保留知识库引用，说明测试点来自哪些历史经验。
- 检索分数可解释，便于调参。
- 风险单独输出，不强行编造 PRD 未明确的信息。
- 模块边界清晰，后续可以替换为真实向量库、真实知识库或 LLM 生成器。
