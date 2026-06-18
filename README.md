# GUI Agent 测试开发工程 Demo

本仓库包含两个可本地运行的测试开发工程 Demo，分别对应：

- 考题二：自然语言手工用例转 GUI Agent 可执行用例
- 考题四：基于 PRD 召回知识库生成测试点

两个工程均使用 Python 标准库实现，不依赖第三方包，适合直接下载、运行和阅读源码。

## 项目一：自然语言手工用例转 GUI Agent 可执行用例

目录：

```text
manual-case-to-agent-demo/
```

能力：

- 输入自然语言手工用例。
- 自动拆分步骤并识别动作意图。
- 基于页面模型绑定页面、控件和定位信息。
- 自动规划跨页面跳转路径。
- 生成中间表示 IR。
- 输出 GUI Agent 可执行 JSON DSL。
- 对模糊页面、模糊控件、模糊断言输出风险提示。

运行：

```powershell
cd manual-case-to-agent-demo
powershell -ExecutionPolicy Bypass -File .\run_converter.ps1
```

输出示例：

```text
manual-case-to-agent-demo/output/notification_switch_persist.json
```

更多说明见：

```text
manual-case-to-agent-demo/README.md
```

## 项目二：基于 PRD 召回知识库生成测试点

目录：

```text
prd-testpoint-agent-demo/
```

能力：

- 输入 PRD 文本。
- 自动抽取功能点、实体、规则、边界条件、异常条件和关键词。
- 基于本地知识库进行混合检索。
- 支持关键词检索、向量相似、历史缺陷相似和规则命中综合打分。
- 输出结构化 JSON 测试点。
- 输出需求风险、覆盖风险和测试点质量风险。

运行：

```powershell
cd prd-testpoint-agent-demo
powershell -ExecutionPolicy Bypass -File .\run_full_agent.ps1
```

输出示例：

```text
prd-testpoint-agent-demo/output/full_test_points.json
```

更多说明见：

```text
prd-testpoint-agent-demo/README.md
```

## 如何下载使用

在 GitHub 仓库页面点击：

```text
Code -> Download ZIP
```

下载后解压，分别进入两个工程目录，按照各自 README 运行即可。

## 环境要求

- Windows PowerShell
- Python 3

如果在 Codex 环境中运行，脚本会优先使用 Codex 自带 Python；如果在普通本机运行，请确保 `python` 或 `py` 命令可用。

## 目录总览

```text
.
├── manual-case-to-agent-demo/
├── prd-testpoint-agent-demo/
├── 考题二-自然语言手工用例到Agent可执行用例的转换方案.md
├── 考题四-基于PRD召回知识库生成测试点.md
└── README.md
```

