# 模板

这里放创建 skill 或 skill 包时可以复制的模板。

- `templates/skill`：单个 skill 的基础模板。

模板不是正式发布的 skill，不参与模块组包。创建新 skill 时，应复制模板到对应模块：

```powershell
Copy-Item -Recurse templates/skill modules/customer-success/skills/my-skill
```

