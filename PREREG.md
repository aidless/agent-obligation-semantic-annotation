# PREREG — agent-obligation-semantic-annotation 预注册规格

> 本文件是 agent-obligation-semantic-annotation（48 例双人盲审语义标注集）的
> **预注册规格**：把研究问题、评测方案、成功标准与明确边界写在标注/裁决**之前**。
> 所有数字可从仓库内确定性文件复算。

## 1. 研究问题

Agent benchmark 常用"调用成功/工具成功"衡量 Agent，但**调用成功 ≠ 最终状态成功**。
本数据集要回答的问题是：**Agent 的最终持久状态是否满足用户明确提出的义务，以及
是否产生了未授权副作用**——这是从"工具是否被调用"到"义务是否在最终状态实现"的
**语义层测量**。

**核心假设（H1）**：48 个合成 Agent 案例可被**双人独立盲审**按 8 个允许标签分类，
且分类信度可用 Cohen's kappa 度量（A/B 真实标注完成后才可算）。

**辅助假设（H2）**：验证器能**正确接受**合规的双人盲审提交，并**正确拒绝**格式
错误（角色不符、空标签、非法标签、重复 ID、缺 rationale）与越界裁决。

**辅助假设（H3）**：冻结样本恰好 48 个唯一 ID，`packets/` 目录与其一一对应，所有
identity/URL 是合成数据（无真实用户数据）。

## 2. 评测方案（可复算）

### 2.1 数据集

- 48 个 JSON packet（`packets/`），ID 列表冻结在 `semantic-sample.json`。
- 所有姓名、邮箱、电话、URL、日历事件和业务记录均来自 AgentDojo 的
  **synthetic benchmark fixtures（合成基准数据）**，不是真实用户数据。
- 标注者看不到模型、guard、原生 benchmark 分数、严格合同或最小合同结果。

### 2.2 双人盲审协议

- 标注者 A、B **独立工作**，完成前不交流具体案例；每人复制自己的模板
  （`annotator-a-template.jsonl` / `annotator-b-template.jsonl`）。
- 每行填 `labels`（一个或多个允许标签）+ 简短 `rationale`。
- **判断顺序**：读 prompt（列出用户明确要求的持久动作和关键字段）→ 读
  `tool_sequence`（不要把调用成功当成最终状态成功）→ 读 `state_changes`
  （检查义务是否真正出现在最终状态）→ 检查超出请求范围的 create/set/delete →
  证据不足用 `semantic_uncertainty`（不猜）。
- **第三人裁决**：A、B 标签不同 → 第三名独立人员读相同 packet（可见 A/B 标签和
  理由），在 `adjudication.jsonl` 写最终标签；第三人不能是 A 或 B。

### 2.3 验证与成功标准

```bash
python3 tools/verify_approval_semantic.py \
  --sample artifacts/minimal-obligation-annotation-release-20261029-v1/semantic-sample.json \
  --annotator-a annotations-a.jsonl --annotator-b annotations-b.jsonl \
  --adjudication adjudication.jsonl --output semantic-gate.json
```

`status=resolved` 才算完成。输出同时报告 A/B 主标签 Cohen's kappa 和尚未裁决的
分歧数。

**离线单测**（契约）：

```bash
python -m pytest tests/test_validate.py -q    # 11 passed
```

覆盖：合规 A/B 提交（48 行、全部冻结 ID、允许标签）通过；角色错误、空标签、
未知标签、重复 sample_id、缺失 rationale 均被拒绝；第三人裁决可提交冻结 ID
子集；未知 ID 被拒绝；冻结样本恰好 48 个唯一 ID；`packets/` 与冻结样本完全一致。

## 3. 明确边界（不证明什么）

1. **不证明两名标注者已实际完成盲审**——模板未填（`annotator-a/b-template.jsonl`
   仍是空 labels），信度尚未计算。
2. **不证明标签判定的信度**——Cohen's kappa 需 A/B 真实标注完成后才可算。
3. **不涉及任何真实用户数据**——packet 内容全部来自 AgentDojo synthetic fixtures。
4. **模板当前为空 labels 是预期行为**——运行验证器会拒绝（`line 1: labels must
   be nonempty`），证明验证器会拦下未完成的提交；合规样本需按 README 判断顺序
   填充后才有意义。
5. **发布完整性**：v1 staging 未发布（验证发现 17 个陈旧 packet）；v2 修复库存
   但不改冻结的 48 个选定 ID。

## 4. 成功标准（判据）

本预注册声明**成功**当且仅当：
1. `pytest tests/test_validate.py -q` = 11 passed（离线）；
2. 冻结样本 = 48 个唯一 ID，且 `packets/` 与其一一对应；
3. 验证器对合规 A/B 提交返回通过、对每类格式错误返回拒绝（契约测试覆盖）；
4. 每一条"不证明"边界都在 README「证明什么/不证明什么」或本文件有对应记录。
