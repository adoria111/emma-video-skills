# 外部依赖与许可

本仓库的内容规划、交付方法和辅助脚本，与实际剪辑、转写、图片生成服务分开提供。

## 剪辑工具怎么选

**ChatCut 可以作为剪映无界面方案的替代选择，承担本流程中的剪辑执行环节。** 两者不必同时安装，选题、剪辑单、封面和发布文案仍可使用本仓库的 Skills。也可以使用自己已有的剪辑器。

- 希望通过自然语言或 AI 助手剪辑：可选择 ChatCut。
- 需要通过指定的无界面工具操作剪映：可选择下方上游方案，先核对环境和许可。
- 已在某个剪辑器手动修改工程：优先沿用能读取该最新工程的工具；不要假设更换工具就能完整接续原工程。

## ChatCut：外部可选能力

- 官网：[ChatCut](https://chatcut.io/)
- 能力说明：[What is ChatCut?](https://chatcut.io/docs/what-is-chatcut)
- AI 助手接入：[Agent Plugin](https://chatcut.io/docs/agent-plugin)
- 剪映工程交接：[导出可编辑剪映 / CapCut 草稿](https://chatcut.io/docs/export-capcut-jianying)

截至 **2026-10-05**，官方文档列出剪切、重排、转写、字幕修改及成片导出能力，可用于直播切片和口播剪辑。Agent Plugin 文档提供 Claude Code、Codex 和 WorkBuddy 的接入说明；须按对应宿主的最新指引单独安装并授权，不能把普通网页聊天或安装本仓库视为已经接通 ChatCut。

如果之后需要在剪映里精修，可以使用 **ChatCut Desktop** 将当前时间轴导出为可编辑草稿，需要本机安装兼容的剪映 / CapCut。导出时检查不支持项，进入目标编辑器复核字幕、效果和时间轴；不能承诺所有属性完整转移，也不能据此假定它能无损接续任意已有剪映工程。

本仓库只提供流程对接和官方链接，不分发 ChatCut 软件或插件。账号、价格、额度和使用条款以服务当前说明为准；素材上传和付费操作按用户授权执行。上述能力依据官方文档核对，本仓库尚未完成 ChatCut 全流程实测。

## 剪映无界面剪辑：外部可选能力

- 核心项目：[mcncarl/jianying-headless](https://github.com/mcncarl/jianying-headless)
- 上游 Skill：[mcncarl/yichen-skills · yichen-jianying-edit](https://github.com/mcncarl/yichen-skills/tree/main/yichen-jianying-edit)
- 许可：[上游 LICENSE](https://github.com/mcncarl/jianying-headless/blob/main/LICENSE)

截至本仓库整理日 **2026-10-05**，核对到的上游许可为 **Personal Learning and Non-Commercial Use License**，包括非商业使用和公开再分发限制。这是源码可见项目，不能把它概括为可以任意商用、再打包的 MIT 开源依赖。

本仓库只提供来源链接和对接流程，不分发上游代码、Skill 目录、编译产物、官方程序库或安装包。本仓库的 MIT 许可不能替代上游许可，也不代表已取得课程获客、客户交付或其他业务用途授权。

安装时直接阅读上游当前说明。已使用过的本机环境是 Apple Silicon macOS，匹配剪映 11.5.0，兼容配置涉及 11.4.2；这不是对其他电脑或未来版本的支持承诺。精确版本、组件校验、编译工具和运行前提以你安装的上游版本为准。遇到校验失败，不修改固定哈希来假装兼容。

如果不使用这项依赖，可以选择上面的 ChatCut，或在你有权使用的剪辑器里根据剪辑单操作，再把成片和字幕交给本仓库的后续模块。交付时说明实际使用的工具。

## 本地转写

附带的 `transcribe_local.py` 是本仓库自行编写的薄封装，调用另行安装的 [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)。第三方包、运行库和模型遵循各自条款，不随此仓库分发。

已经有匹配字幕时不必重新转写。首次模型下载需要网络；媒体在本机处理。若用户主动选择其他转写服务，费用、上传和账号要求由该服务及当前授权决定。

## 图片与字体

封面制作使用宿主提供或用户选定的图片编辑能力。没有附送人物照片、参考截图或字体文件。使用用户拥有或有权使用的视频帧；字体和图像工具的授权各自适用。

如果使用生成式编辑，完成后检查人物、文字和上下图的一致性；不要把生成结果说成像素级无损复制。无需为了精确尺寸擅自换到付费 API。

## 发布平台

本仓库没有自动登录、上传或发布脚本。发布正文和标题是交付物，不包含对外发布授权。实际发布必须另有明确指令，并遵守宿主工具要求。
