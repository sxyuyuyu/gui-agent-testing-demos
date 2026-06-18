# 考题二完整版工程：自然语言手工用例转 GUI Agent 可执行用例

## 1. 工程说明

本工程用于演示“自然语言描述的手工用例”如何转换为 GUI Agent 可稳定执行的结构化步骤。

完整流程如下：

```text
自然语言手工用例
  -> 句子拆分
  -> 动作意图识别
  -> 页面 / 控件实体绑定
  -> 页面跳转路径规划
  -> 断言补全
  -> 中间表示 IR
  -> GUI Agent DSL JSON
```

## 2. 目录结构

```text
manual-case-to-agent-demo/
  convert_manual_case.py              命令行入口
  run_converter.ps1                   Windows 运行脚本
  README.md                           中文说明文档

  manual_case_agent/
    schema.py                         数据结构
    text_utils.py                     文本清洗与拆句
    page_model.py                     页面模型与路径规划
    intent_parser.py                  自然语言动作意图解析
    ir_builder.py                     中间表示 IR 构建
    agent_dsl.py                      GUI Agent DSL 生成
    converter.py                      完整 pipeline 编排

  data/
    page_model.json                   页面对象模型、控件库、页面跳转图
    manual_cases/                     多个自然语言手工用例样例

  output/                             运行后生成的 JSON 输出
```

## 3. 运行方式

Windows 推荐：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_converter.ps1
```

如果本机已安装 Python：

```bash
python convert_manual_case.py --case data/manual_cases/notification_switch_persist.txt --page-model data/page_model.json --out output/notification_switch_persist.json
```

## 4. 如何修改测试文件路径

最推荐的方式是修改命令中的 `--case` 参数。

例如运行优惠券领取用例：

```bash
python convert_manual_case.py --case data/manual_cases/coupon_receive_success.txt --out output/coupon_receive_success.json --case-id TC_COUPON_001 --title 优惠券领取成功
```

运行退款申请用例：

```bash
python convert_manual_case.py --case data/manual_cases/refund_apply_success.txt --out output/refund_apply_success.json --case-id TC_REFUND_001 --title 退款申请成功
```

运行登录验证码边界用例：

```bash
python convert_manual_case.py --case data/manual_cases/login_captcha_boundary.txt --out output/login_captcha_boundary.json --case-id TC_LOGIN_001 --title 登录验证码边界
```

运行模糊断言用例：

```bash
python convert_manual_case.py --case data/manual_cases/ambiguous_assertion.txt --out output/ambiguous_assertion.json --case-id TC_AMBIGUOUS_001 --title 模糊断言示例
```

如果你使用 `run_converter.ps1`，可以修改脚本里的这一行：

```powershell
convert_manual_case.py --out output/notification_switch_persist.json
```

改成你想测试的文件，例如：

```powershell
convert_manual_case.py --case data/manual_cases/refund_apply_success.txt --out output/refund_apply_success.json --case-id TC_REFUND_001 --title 退款申请成功
```

如果想修改程序默认读取的测试文件路径，可以改：

```text
convert_manual_case.py
```

找到这一行：

```python
parser.add_argument("--case", default="data/manual_cases/notification_switch_persist.txt", help="Manual case file path.")
```

把 `default` 改成新的用例路径即可。

## 5. 已提供的测试样例

```text
data/manual_cases/notification_switch_persist.txt
```

通知开关状态保留：

```text
登录后进入“我的”页面，点击“设置”，关闭通知开关，返回“我的”页面，再次点击“设置”，验证开关状态保留。
```

```text
data/manual_cases/coupon_receive_success.txt
```

优惠券领取成功：

```text
登录后进入优惠券中心，点击立即领取，验证优惠券领取成功并展示在优惠券卡片中。
```

```text
data/manual_cases/refund_apply_success.txt
```

退款申请成功：

```text
登录后进入订单列表，点击第一笔订单，点击申请退款，选择退款原因“买错了”，点击提交退款，验证订单进入退款审核中。
```

```text
data/manual_cases/login_captcha_boundary.txt
```

登录验证码边界：

```text
进入登录页，输入手机号“13800000000”，输入密码“wrong_password”，点击登录按钮，验证第 3 次密码错误后展示图形验证码。
```

```text
data/manual_cases/ambiguous_assertion.txt
```

模糊断言：

```text
登录后进入我的页面，点击设置，关闭通知开关，验证成功。
```

这个样例会输出风险，因为“验证成功”没有明确说明验证哪个控件、哪个状态或哪个页面结果。

## 6. 输出 JSON 说明

输出文件包含：

- `clauses`：从自然语言中拆出来的句子片段。
- `intents`：识别出的动作意图，例如登录、跳转、点击、输入、开关、断言。
- `intermediateRepresentation`：中间表示 IR，包含前置条件、步骤、断言和风险。
- `agentInput`：最终交给 GUI Agent 的执行 DSL。
- `summary`：意图数量、IR 步骤数量、断言数量、风险数量。
- `risks`：无法自动确认的问题，例如页面不明确、控件不明确、断言不明确。

## 7. 页面模型如何扩展

如果要支持新的 App 页面或控件，修改：

```text
data/page_model.json
```

主要补充三类内容：

1. `pages`：页面、页面断言、控件列表和控件定位。
2. `aliases`：自然语言页面别名到标准页面名的映射。
3. `transitions`：页面之间的跳转关系，例如从首页点击某个入口进入订单页。

新增页面和控件后，转换器就能把自然语言里的页面名、控件名映射成 Agent 可执行定位。
