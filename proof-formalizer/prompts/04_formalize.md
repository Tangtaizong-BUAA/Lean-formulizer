<!-- v3-anti-loop -->

# Stage 4: Formalize（v3 — Anti-Loop 主循环）

逐段翻译成 Lean 4 + Mathlib 代码。**Probe 先行，Goal-state 驱动，Anti-loop 强制升级**。

## 铁律（违反即作废）

1. 每次 attempt **前**必须调用 `ledger.py read_segment_state` 读取最新状态
2. 每次 attempt **前**必须调用 `ledger.py summarize_for_prompt` 把摘要塞入你的推理
3. **黑名单中的 tactic 不许再用**（包括 family-banned 的所有变体）
4. 升级到 **Level 4** 时必须重新跑 `lake env lean working.lean` 提取真实 goal state
5. 每次 attempt **后**必须写齐 4 个文件：`{n:02d}_tactic.lean` / `_stderr.txt` / `_diag.json` / `_prompt.md`
6. 每次 attempt **后**必须 append 一条到 `ledger.jsonl`
7. 总 attempts 硬上限 9 次，超出自动触发 help_request

---

## 策略模式分支（必须先读 strategy.md）

在进入主循环前，读取 `strategy.md` 中的策略模式：

| 模式 | 行为 |
|------|------|
| `full` | 原流程：逐段 formalize（见下方主循环） |
| `axiom` | 先把 axiom 列表写入 `working.lean` 顶部作为 `axiom` 声明，然后对剩余 segments 执行 formalize（跳过已被 axiom 覆盖的定理） |
| `decompose` | 将每个可行子定理独立 formalize，产出多个 `final_*.lean`，并在主 report 中汇总 |
| `abort` | 不进入 formalize 主循环，直接写 `help_request.md` 说明不可行原因 |

**强约束**：若 mode 为 `axiom` 或 `abort`，必须检查 `strategy.md` 中 `user_confirmed: true` 字段。若缺失，主循环必须停下询问用户确认。

---

## 优先采用 auto_solved tactic

读取 `alignment.md`，对每个 segment：
- 如果有 `auto_solved` 字段 → 直接使用该 tactic，跳过 LLM 生成
- 仍然要走 probe + compile（作为最终验证）

---

## 主循环

对 alignment.md 中的每个 segment，按顺序处理：

```python
# 初始化
run_dir = Path(run_dir)
from formalizer_helpers.v3.ledger import LedgerManager
from formalizer_helpers.v3.escalation import decide_next_level, update_blacklist
from formalizer_helpers.v3.error_classifier import classify
from formalizer_helpers.v3.fingerprint import fingerprint as compute_fingerprint, classify_tactic_family

for segment in segments:
    mgr = LedgerManager(run_dir, segment.id)
    state = mgr.update_segment_state(
        current_level=0,
        total_attempts=0,
        level_attempts_used={},
        blacklist=[],
        fingerprint_history=[],
        status="in_progress",
        last_tactic="",
        last_goal="",
    )

    last_diag = None
    last_tactic = ""
    last_family = ""

    while state["status"] == "in_progress":
        # --- Step 1: 决定 level ---
        next_level, reason = escalate.decide_next_level(state, last_diag)

        if next_level == 6:
            write_help_request(segment, state)
            state["status"] = "help_requested"
            mgr.update_segment_state(status="help_requested")
            break

        escalated = next_level > state["current_level"]
        if escalated:
            state = escalate.update_blacklist(state, last_tactic, last_family, escalated=True)

        state["current_level"] = next_level
        mgr.update_segment_state(current_level=next_level)

        # --- Step 2: 取真实 goal ---
        if next_level == 4 or state["total_attempts"] == 0:
            goal = extract_goal_state_from_compilation()
        else:
            goal = state.get("last_goal", "")

        # --- Step 3: 读 ledger summary + 黑名单 ---
        ledger_summary = mgr.summarize_for_prompt()
        blacklist = state.get("blacklist", [])
        allowed_families = escalate.get_allowed_families(state)

        # --- Step 4: 生成 tactic（按 level 路由）---
        level_prompt_path = f"prompts/level_{next_level}_*.md"
        tactic = generate_tactic(
            level=next_level,
            goal=goal,
            blacklist=blacklist,
            allowed_families=allowed_families,
            ledger_summary=ledger_summary,
            level_prompt=level_prompt_path,
            segment_context=alignment_info,
        )

        # --- Step 5: probe 所有标识符 ---
        if not probe_all_identifiers(tactic):
            # 退回生成（但不计 attempt）
            continue

        # --- Step 6: 全文编译 ---
        compile_result = run_lake_lean(snapshot_to_working_lean(tactic))
        if compile_result["exit_code"] == 0:
            # 成功！
            mgr.append_attempt({... "compile_result": "success", ...})
            mgr.write_attempt_files(attempt_n, tactic_lean, "", {}, prompt_text)
            state["status"] = "success"
            mgr.update_segment_state(status="success")
            break

        # --- Step 7: 失败 → 诊断 ---
        diag = classify(compile_result["stderr"])
        fp = compute_fingerprint(diag, goal, tactic)

        # --- Step 8: 写入 ledger ---
        attempt_n = mgr.append_attempt({
            "level": next_level,
            "level_attempt_n": state["level_attempts_used"].get(str(next_level), 0) + 1,
            "goal_before": goal,
            "tactic_used": tactic,
            "tactic_family": classify_tactic_family(tactic),
            "compile_result": "fail",
            "error_text_excerpt": compile_result["stderr"][:500],
            "error_class": diag["error_class"],
            "key_tokens": diag["key_tokens"],
            "fingerprint": fp,
        })

        # --- Step 9: 写 4 个 per-attempt 文件 ---
        mgr.write_attempt_files(attempt_n, tactic_lean, compile_result["stderr"], diag, prompt_text)

        # --- Step 10: 处理 timeout（先处理，不计 attempt）---
        if diag["error_class"] == "timeout":
            # timeout 不计入 attempt count，直接升级 heartbeat 重试
            from formalizer_helpers.v3.perf_hint import handle_timeout
            handle_timeout(working_lean_path, compile_result["stderr"])
            continue  # 重试，不增 total_attempts

        # --- Step 11: 更新 state ---
        lvl_key = str(next_level)
        state["level_attempts_used"][lvl_key] = state["level_attempts_used"].get(lvl_key, 0) + 1
        state["total_attempts"] += 1
        state["fingerprint_history"].append(fp)
        state["last_tactic"] = tactic
        state["last_goal"] = goal
        update_blacklist(state, tactic, classify_tactic_family(tactic), escalated=False)
        mgr.update_segment_state(**state)

        last_diag = diag
        last_tactic = tactic
        last_family = classify_tactic_family(tactic)
```

---

## 已 probe 通过的标识符及其类型签名

<从 probe_signatures.json 读取，渲染为表格>

| 标识符 | 类型签名 | docstring 摘要 |
|--------|---------|--------------|
| Nat.gcd | (m n : ℕ) → ℕ | 最大公约数 |
| Finset.prod_erase_mul | ... | ... |

**强约束**：你写的 tactic 必须基于上面的真实类型，不许凭记忆猜参数顺序、隐式参数、类型类约束。

---

## 失败诊断与建议（来自 retry_strategy）

- next_tactic_hint: <RETRY_STRATEGY_HINT>
- 推荐 family: <SUGGESTED_FAMILIES>
- 辅助工具结果: <AUXILIARY_RESULTS>

---

## Per-Level 路由

| Level | 名称 | Prompt 文件 | 说明 |
|-------|------|-----------|------|
| 0 | tweak | `prompts/level_0_tweak.md` | 同 tactic 微调参数 |
| 1 | switch_within | `prompts/level_1_switch_within.md` | 同 family 内切换 |
| 2 | switch_family | `prompts/level_2_switch_family.md` | 切换 tactic family |
| 3 | lemma_rotate | `prompts/level_3_lemma_rotate.md` | 换 mathlib 候选引理 |
| 4 | replan | `prompts/level_4_replan.md` | 重读 goal + 新规划 |
| 5 | resegment | `prompts/level_5_resegment.md` | 拆分 segment |

---

## 编译

```bash
cd ~/v3-sandbox/math-agent-workspace && lake env lean <working.lean>
```

超时控制使用 portability shim：
```bash
if command -v gtimeout >/dev/null 2>&1; then TO="gtimeout"
elif command -v timeout >/dev/null 2>&1; then TO="timeout"
else TO="perl -e 'alarm shift @ARGV; exec @ARGV' --"; fi
$TO 15 lake env lean ...
```

---

## 最终审计

- 0 sorry + 编译通过 → 成功，输出 final.lean
- 有 sorry 或 help_request 非空 → 输出 help_request.md + 当前 working.lean
- 总 attempts ≥ 9 的 segment → 自动标记 help_requested

## Probe 自动替换规则（继承 v2）

1. 取 suggestion 首条
2. 直接替换，不询问
3. 替换后再 probe 验证
4. 写注释：`-- [PROBE-REPLACE] OldName → NewName`
5. 首选 NOT_FOUND → 试第二条；全不行 → tactic 失败

## API 用法错误（继承 v2 二次防线）

Probe 验证标识符存在，不验证用法。编译失败时：
1. 调用 `formalizer_helpers/api_usage_checker.py --code <failed.lean> --error <error.txt> --output <diag.json>`
2. 根据诊断结果修正标识符用法
3. 从 mathlib_lookup 找正确用法示例
