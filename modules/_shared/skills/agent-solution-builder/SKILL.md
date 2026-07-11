---
name: agent-solution-builder
description: 当用户给出客户名称、行业、模糊需求、一句话场景、聊天记录、SOP 或业务材料，并希望直接生成可用的智能体提示词时使用。Use this skill to infer the hidden business logic behind a rough customer requirement and output one ready-to-use agent prompt, not a proposal or analysis package, unless the user explicitly asks for those.
---

# Agent Solution Builder

Use this skill to turn a vague customer requirement into a polished agent prompt.

The user does not want to do product analysis, prompt architecture, workflow sorting, or form filling. Do that work silently and return the agent prompt directly.

## Trigger

Use this skill when the user says things like:

- `客户叫 X，想做一个智能体，需求是...`
- `帮我给这个客户生成智能体提示词`
- `这个场景做个 agent prompt`
- `我给你名字和需求，你直接给我智能体提示词`
- `根据这段聊天记录做一个智能体`
- `做个技术智能体 / 销售智能体 / 客服智能体 / 运营智能体`

Do not use this skill for general AI education, model comparison, long proposal writing, or generic sales copy unless the user asks for a prompt that powers that agent.

## Default Output

By default, output only one complete prompt in a fenced code block.

Do not output:

- solution proposal;
- requirement table;
- delivery roadmap;
- test case table;
- long explanation of how you inferred the prompt;
- multiple prompt options unless the user asks.

Allowed outside the code block:

- one short sentence only if needed, such as `下面是可直接使用的智能体提示词：`.

## Core Principle

Infer first, ask later.

When the user gives a vague need, privately infer:

- customer industry and likely business goal;
- user role and end-user role;
- upstream input materials;
- downstream output that creates business value;
- hidden SOP or decision flow;
- data fields the agent should extract;
- rules for prioritization, classification, escalation, and refusal;
- permission boundaries and write-back safety;
- quality standard for a useful answer.

Ask a follow-up question only if one missing detail makes the prompt unsafe or impossible, such as:

- the agent would need to access private systems or write production data;
- the customer scenario is unknown and cannot be reasonably inferred;
- legal, medical, financial, or hiring decisions require policy boundaries.

Otherwise, make reasonable assumptions and bake them into the prompt as defaults.

## Prompt Construction Workflow

Before writing the final prompt, silently complete these steps:

1. Identify the agent's job-to-be-done in one sentence.
2. Choose a focused agent type:
   - `问答顾问型`: answers using documents or knowledge.
   - `流程执行型`: follows SOP and produces next actions.
   - `资料分析型`: extracts facts and generates conclusions.
   - `销售/客服辅助型`: drafts replies and follow-up actions.
   - `工具协作型`: prepares tool calls or write-back drafts for human approval.
   - `混合型`: combines the above, but still with one clear main job.
3. Reconstruct the likely business workflow from the rough requirement.
4. Define what the agent should read, extract, decide, and produce.
5. Add guardrails for hallucination, missing information, permissions, and customer promises.
6. Make the prompt specific enough that another AI can run it without asking the user to design the workflow.

## Generated Prompt Shape

The prompt you output should normally include these sections inside the code block:

```text
# 角色
你是...

# 目标
你的任务是...

# 使用场景
当用户提供...时，你要...

# 输入理解
你需要从用户输入中识别...
如果信息缺失，默认...

# 工作流程
1. ...
2. ...
3. ...

# 推断规则
- ...

# 输出要求
按下面格式输出...

# 边界与安全
- ...

# 追问规则
只有在...时才追问；否则先基于合理假设产出。
```

You may rename or merge sections when a cleaner prompt needs it, but keep the final result directly usable.

## Inference Rules

- If the user only gives a customer name and a broad need, infer from the customer's stated industry or the business nouns in the need.
- If the user says "智能体", assume they want a repeatable working instruction for an AI agent, not a marketing introduction.
- If the user says "技术的", make the prompt implementation-aware: include data, tools, permissions, failure handling, and output contract.
- If a workflow implies system writes, default to "generate draft and ask for human confirmation before write-back".
- If the customer need sounds like sales, customer success, HR, private-domain ops, IP content, or document analysis, use the matching business workflow vocabulary.
- If there is no explicit output format, design one that makes the agent's result immediately usable.

## Style Rules

- Write the generated prompt in Chinese unless the customer requirement is clearly English.
- Make it crisp and operational, not motivational.
- Avoid meta commentary like "我推断你需要".
- Avoid overbroad phrases such as "你是一个万能助手".
- Give the agent a narrow role and clear working loop.
- Include examples only if the prompt would otherwise be ambiguous.

## Minimal Input Mode

If the user provides only:

```text
客户名 + 模糊需求
```

still output a complete prompt.

Use this internal default:

- unknown systems become `用户提供的资料或已授权系统`;
- unknown write-back becomes `先生成草稿，不自动写回`;
- unknown user role becomes `业务人员`;
- unknown quality standard becomes `可直接用于客户沟通或内部执行`;
- unknown data schema becomes `先从原文抽取字段，并把缺失字段标为待确认`.

## When User Asks For More

If the user asks for implementation after receiving the prompt, then produce the requested artifact:

- system prompt refinement;
- tool schema;
- workflow diagram;
- test cases;
- code;
- Feishu or spreadsheet structure;
- delivery proposal.

Do not include those by default.
