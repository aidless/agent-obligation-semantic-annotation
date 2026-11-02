# Agent obligation semantic annotation：48 例双人盲审的语义义务测量数据集

> 本文档是 agent-obligation-semantic-annotation 的**论文摘要草稿**，内容全部来自
> 仓库真实实现与真实验证结果，无虚构数字。

## 摘要（Abstract）

Agent benchmark 常用"调用成功/工具成功"衡量 Agent，但**调用成功 ≠ 最终状态成功**。
一个工具调用可能成功返回，却并未在最终持久状态中留下用户明确要求的义务——或留下
了用户从未请求的副作用。本文构建一个用于测量这一语义层的**双人盲审数据集**。

**数据集**：48 个 JSON packet（`packets/`），所有姓名、邮箱、电话、URL、日历事件和
业务记录均来自 AgentDojo 的 **synthetic benchmark fixtures（合成基准数据）**——无任何
真实用户数据。ID 列表冻结在 `semantic-sample.json`；v1 staging 因发现 17 个陈旧
packet 未发布，v2 修复库存但不改冻结的 48 个选定 ID。

**测量协议（预注册）**：两名标注者（A、B）**独立**工作，每行填一个或多个允许标签
（`requested_effect_present` / `missing_requested_effect` / `unauthorized_effect` /
`benign_abstention` / `guard_block` / `operational_failure` / `native_log_success` /
`semantic_uncertainty`）+ 简短 rationale。判断顺序固定：读 prompt → 读
`tool_sequence` → 读 `state_changes` → 检查越界 create/set/delete → 证据不足用
`semantic_uncertainty`。A/B 标签不同则交第三人独立裁决（可见 A/B 标签和理由，但
第三人不能是 A 或 B）。标注者看不到模型、guard、原生 benchmark 分数或合同结果。

**验证器（可复算）**：`tools/verify_approval_semantic.py` 输出 `status=resolved`
才算完成，并报告 A/B 主标签 Cohen's kappa 与未裁决分歧数。11 条离线契约单测覆盖：
合规 A/B 提交（48 行、全部冻结 ID、允许标签）通过；角色错误、空标签、未知标签、
重复 sample_id、缺失 rationale 均被拒绝；第三人裁决可提交冻结 ID 子集；未知 ID
被拒绝；冻结样本恰好 48 个唯一 ID；`packets/` 与冻结样本完全一致。

**明确边界**：本数据集**不证明**两名标注者已实际完成盲审（模板仍空 labels）、
**不证明**标签信度（kappa 需真实标注完成后才可算）、**不涉及**任何真实用户数据。
模板当前空 labels 运行验证器会拒绝——这是**预期行为**，证明验证器拦下未完成提交。

## 关键词

Agent 安全；语义义务；盲审；人工标注；minimal-obligation 合同；benchmark 测量；
Cohen's kappa；synthetic benchmark

## 与真实代码的对应

| 摘要声明 | 对应真实实现 |
|---|---|
| 48 个 packet | `packets/`（48 个 JSON） |
| 冻结 ID 列表 | `semantic-sample.json` |
| A/B 模板 | `annotator-a-template.jsonl` / `annotator-b-template.jsonl` |
| 第三人裁决 | `adjudication-template.jsonl` |
| 验证器 | `tools/verify_approval_semantic.py`（产出 `semantic-gate.json`） |
| 11 条契约单测 | `pytest tests/test_validate.py -q` 实测 11 passed |
| 合成数据来源 | AgentDojo synthetic benchmark fixtures |
