# 安装与更新

## 选择安装范围

在仓库根目录执行：

```bash
python3 scripts/install.py --app codex
python3 scripts/install.py --app claude
python3 scripts/install.py --app agents
python3 scripts/install.py --dest /path/to/skills
```

每次只选一个目标。默认目录分别是 `~/.codex/skills`、`~/.claude/skills`、`~/.agents/skills`。Codex 设置了 `CODEX_HOME` 时，使用该目录下的 `skills`。

查看计划而不安装：

```bash
python3 scripts/install.py --app codex --dry-run
```

只装一个：

```bash
python3 scripts/install.py --app codex --skill koubo-advisor
```

总入口可以在模块缺失时完成自己能做的部分，但完整流程建议安装全部六项。

## 已有同名技能

默认遇到同名目录会停止，避免覆盖你自己长期维护的版本。先比较内容；确认要更新后：

```bash
python3 scripts/install.py --app codex --replace
```

旧目录会备份到目标技能目录旁的 `skill-backups/emma-video-skills-时间戳/`，安装器会显示路径。符号链接形式的同名技能会被拒绝，需先弄清它指向哪个项目；不要把上游项目或插件缓存当作普通文件覆盖。

恢复时，先保留当前版本，再将备份文件夹中的对应技能复制回目标技能目录。卸载只需移除这次安装的六个目录；不要删除整个技能目录。

本仓库的公开版经过通用化，不包含作者本机的私人参考图和历史案例。已有私人版本不必为了使用总入口全部替换。

## 可选：本地转写

使用已有 SRT / TXT 不需要安装以下依赖。需要在本机转写时：

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 可用 .venv\Scripts\Activate.ps1
python -m pip install -r requirements-transcription.txt
```

首次使用且需要下载模型：

```bash
python skills/video-transcribe/scripts/transcribe_local.py \
  /path/to/recording.mp4 --output-dir /path/to/new-transcript \
  --model small --language zh --allow-model-download
```

之后模型已缓存，可省略 `--allow-model-download`。默认只查本地模型，不在后台上传媒体或切换到付费转写 API。也可以把 `--model` 指向本地模型目录。

`--output-dir` 必须是不存在的新目录，以免覆盖原稿。脚本输出 `transcript.txt`、`transcript.srt`、`transcript.json`。转写速度取决于电脑和模型；较大模型不保证每个词都正确。

## 剪辑和图片工具

它们由宿主或另外安装的工具提供。本安装器只安装本仓库的 Skills，不安装剪映、第三方剪辑后端、字体、图片模型或官方程序库。具体前提见 [依赖说明](dependencies.md)。
