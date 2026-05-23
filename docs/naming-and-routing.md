# Skill 命名与归属规范

这份规范用于解决三个问题：

- skill 应该叫什么名字。
- skill 应该放到哪个部门模块。
- Agent 在创建、保存、上传、PR 时应该怎么主动确认。

## 总原则

```text
机器识别名：拼音 / 英文 / ASCII
业务说明：中文
专业术语：保留英文
```

机器识别名包括：

- 分支名。
- skill 目录名。
- `SKILL.md` frontmatter `name`。
- 手动调用名 `$skill-name`。
- tag。
- GitHub Actions workflow name、job name、step name。
- artifact name。
- 脚本参数中的固定 ID。

这些位置不要使用中文，避免乱码、命令行识别失败、分支保护检查名失效。

## Skill 命名

skill 名按功能命名，不按人员命名。

目录名、`SKILL.md` frontmatter `name` 和手动调用名必须一致：

```text
modules/<module-id>/skills/<skill-name>/
name: <skill-name>
$<skill-name>
```

`SKILL.md` 是固定入口文件名，不是 skill 名。它必须保持大写 `SKILL.md`，但在回复用户时不要只显示“SKILL.md”，应显示为“`<skill-name>` 的 `SKILL.md`”。

推荐：

```text
kehu-xuqiu-jiaofu-fenxi
shangji-genjin-fenxi
mianshi-jilu-zhengli
```

不推荐：

```text
zhangsan-skill
我的客户分析
skill-v1
```

版本号不要塞进目录名。版本应写在：

- `VERSION`
- `CHANGELOG.md`
- 正式 tag：`<module-id>/<skill-name>/v<version>`

示例：

```text
modules/customer-success/skills/kehu-xuqiu-jiaofu-fenxi/
VERSION = 0.1.0
tag = customer-success/kehu-xuqiu-jiaofu-fenxi/v0.1.0
```

只有在确实需要长期并行维护两个不兼容版本时，才允许在 skill 名中使用版本后缀，例如 `kehu-xuqiu-fenxi-v2`，且必须在 `README.md` 说明原因。

## 模块归属

正式 skill 必须放在：

```text
modules/<module-id>/skills/<skill-name>/
```

当前模块：

模块目录名不能直接改成中文，否则会影响脚本、打包、tag、分支保护和跨平台兼容性。给人看的地方统一显示为“英文机器 ID + 中文部门名”。

| 机器 ID | 中文名 | 适用范围 |
| --- | --- |
| `customer-success` | 客户成功 | 客户交接、客户过程记录、客户需求与交付、客户健康度、续费、风险、客户会议和行动项 |
| `sales` | 销售 | 线索、商机、拜访、报价、合同、回款前推进、销售跟进和销售材料 |
| `ip` | IP 部门 | IP 内容策划、账号定位、选题、脚本、发布计划、内容资产沉淀 |
| `private-domain` | 私域部门 | 社群运营、用户分层、私域触达、活动转化、私域数据和过程资料 |
| `hr` | HR 部门 | 招聘、面试、候选人跟进、入职、培训、绩效和组织资料 |
| `_shared` | 跨部门通用 | 两个及以上部门都能复用，或属于 Git/GitHub、文档、表格、会议、知识库、流程治理等通用能力 |

## Agent 命中机制

当用户出现这些意图时，Agent 必须启用本规范：

- “创建一个 skill”
- “封装成 skill”
- “保存这个 skill”
- “上传这个 skill”
- “发起 PR”
- “发布 skill”
- “帮同事建 skill”
- “把这批 skill 提交上去”

触发后必须做四步检查：

1. 如果用户只说“创建一个 skill”，先问清场景、使用人、输入、输出和可用标准，不要直接创建文件。
2. 确认 skill 功能名是否为拼音/英文 ASCII。
3. 确认应该进入哪个 `module-id`，提问时同时显示中文部门名。
4. 确认是否需要更新 `VERSION` 和 `CHANGELOG.md`。
5. 如果用户需要 `$skill-name` 手动调用，确认 `.codex/skills/<skill-name>/` 项目可调用入口是否同步更新。
6. 上传、推送或创建 PR 前，再次确认模块归属。

确认后不要立刻进入后续危险动作。每个稳定阶段结束时，Agent 应说明当前状态，并只给两个方向：继续深化调整，或进入下一步流程。用户选择继续深化时，不推进 commit、push 或 PR。

如果用户没有说明部门，Agent 必须提问：

```text
这个 skill 准备归到哪个模块？可选：customer-success（客户成功）、sales（销售）、ip（IP 部门）、private-domain（私域部门）、hr（HR 部门）、_shared（跨部门通用）。
```

如果 Agent 能推断候选模块，也只能给建议，不能直接当作最终决定：

```text
我判断它更像 customer-success，因为它处理客户会议和交付跟进。你确认放到 customer-success 吗？
```

## 信息补偿机制

个人长期分支只表达“谁在工作”，例如：

```text
work/renqc
```

它不表达本次改了什么。本次变更信息必须放在：

- commit message。
- PR 标题。
- PR 描述。

推荐 commit：

```text
skill(customer-success/kehu-xuqiu-jiaofu-fenxi): 新增逐字稿需求拆解
skill(sales/shangji-genjin-fenxi): 新增商机跟进分析
work(renqc): 补充团队 skill 命名与上传规范
```

推荐 PR 标题：

```text
work(renqc): 新增客户成功与销售 skill 批次
skill(customer-success/kehu-xuqiu-jiaofu-fenxi): 新增逐字稿需求拆解
```

PR 描述必须逐项列出路径：

```markdown
## 本次变更

- `modules/customer-success/skills/kehu-xuqiu-jiaofu-fenxi`：新增逐字稿需求拆解 skill
- `modules/sales/skills/shangji-genjin-fenxi`：新增商机跟进分析 skill
```

PR 标题和描述默认由 Codex 根据当前 diff、skill 内容、`VERSION`、`CHANGELOG.md` 和校验结果生成，并按 `.github/pull_request_template.md` 填写；不要让没有开发经验的同事从零写 PR。Codex 应先给出自己的模块、路径、范围、PR 内容和目标分支建议，再让用户核实关键项。
