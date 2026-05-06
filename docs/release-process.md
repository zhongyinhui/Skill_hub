# Release Process

这份文档描述一个 skill 从修改到发布的推荐流程。

## 1. 创建分支

```powershell
git switch -c skill/<module-id>/<skill-name>/<short-change>
```

## 2. 修改 skill

至少检查这些文件：

- `SKILL.md`
- `README.md`
- `VERSION`
- `CHANGELOG.md`
- `examples/`
- `tests/`

## 3. 本地校验

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

如果已经启用 `.githooks/`，提交和推送时也会自动运行同一套检查。

## 4. 提交

```powershell
git add modules/<module-id>/skills/<skill-name>
git commit -m "skill(<module-id>/<skill-name>): 用中文说明这次改动"
```

## 5. 合并

合并前重点审查：

- 是否有清晰 diff。
- 版本号是否正确。
- CHANGELOG 是否说明原因。
- 示例和测试是否匹配新行为。

## 6. 发布 tag

可以先让脚本检查模块、skill 和版本号：

```powershell
powershell -ExecutionPolicy Bypass -File tools/release-skill.ps1 -ModuleId customer-success -SkillName customer-handover
```

确认无误后再创建 tag：

```powershell
git tag <module-id>/<skill-name>/v<version>
git push origin <module-id>/<skill-name>/v<version>
```

示例：

```powershell
git tag customer-success/customer-handover/v1.2.0
```
