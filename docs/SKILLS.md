# 技能清单与安装

这里区分“本次创作中提到或使用过的第三方技能”和“本仓库提供的可安装项目技能”。技能是工作方法与提示指令，不是模型或 ComfyUI 节点，也不会凭空提升显卡算力。

## 创作记录

| 技能 | 阶段 | 可核对的范围 |
|---|---|---|
| agentic-video-foundry | 概念、镜头到视频流程 | 用户明确指定；本机安装的版本，未确认公开上游来源 |
| remotion-video | 前端剪辑与生成编排 | 用户明确指定；本机版本，不把它当作所有最终剪辑的执行工具 |
| remotion-best-practices | Remotion 合成 | 用户明确指定；[公开技能仓库](https://github.com/remotion-dev/skills) 可安装，未声称与本机文件逐字相同 |
| beat-sync-editing | 节拍与切点 | 精修记录使用的技能；未确认该本机副本的公开上游 |
| shot-composition | 构图与连续性 | 精修记录使用的技能；未确认该本机副本的公开上游 |
| cua-driver | 剪映界面查看与验证 | 精修记录；平台相关，不是模型插件 |
| grill-me、brainstorming、i-have-adhd | 网站共创与需求收敛 | 用户在网站阶段指定，与 MV 生成阶段分开列出 |
| writing-plans、executing-plans、github | 网站实现与发布 | 本次发布阶段使用 |

来源不明确的第三方技能不复制进开源包，也不编造下载地址。可核对来源：

- [Remotion skills](https://github.com/remotion-dev/skills)：按上游 README 安装，例如 `npx skills add remotion-dev/skills`。
- [Superpowers](https://github.com/obra/superpowers)：包含 brainstorming、writing-plans 等；按你的 AI 客户端选择对应安装方式。
- [剪映 MCP](https://github.com/Xanthus-Sanslab/jianying-ai-mcp)：它是工具服务，按上游安装说明配置，不当作普通 SKILL.md。

## 本仓库提供的项目技能

`skills/ascension-production/SKILL.md` 是围绕这次实践新编写的项目技能，覆盖人物锁定、镜头提示词、单镜生成、筛选和节拍验证。它是可复用的方法提炼，不冒充第三方技能的原始源码。

将 `skills/ascension-production` 整个目录复制到支持 Agent Skills 的客户端技能目录，例如个人目录下的 `.agents/skills/`。重启或刷新客户端技能发现后，在对话中明确要求使用 `ascension-production`。不要覆盖同名已有技能。

PowerShell（在仓库根目录执行）：

```powershell
$target = Join-Path $env:USERPROFILE '.agents/skills/ascension-production'
if (Test-Path -LiteralPath $target) { throw '同名技能已存在，请先比较内容' }
Copy-Item -LiteralPath './skills/ascension-production' -Destination $target -Recurse
```

项目技能不包含密钥、远程上传权限或自动运行队列。模型、素材与软件仍需单独安装。
