# 长篇网文蒸馏项目

这是一个面向“长篇网文高保真续写”的可执行蒸馏工程。

它的目标是把输入的作品文本，转化成一套可直接用于后续续写的结构化档案，包含：
- 作品总览
- 人物档案
- 世界设定
- 剧情结构
- 伏笔与回收
- 风格与语言
- 续写蓝图
- 审校清单

## 功能特点

- 支持从本地文本文件输入作品正文
- 自动统计字数、词数、估计长度
- 自动生成蒸馏档案骨架
- 内置主提示词模板，适合直接给大模型使用
- 输出结果可直接作为后续续写的工作目录

## 项目结构

```text
.
├── README.md
├── requirements.txt
├── prompts/
│   └── main_prompt.md
├── templates/
│   ├── 01_作品总览.md
│   ├── 02_人物档案.md
│   ├── 03_世界设定.md
│   ├── 04_剧情结构.md
│   ├── 05_伏笔与回收.md
│   ├── 06_风格与语言.md
│   ├── 07_续写蓝图.md
│   └── 08_审校清单.md
├── scripts/
│   └── run_distillation.py
└── examples/
    └── sample_novel.txt
```

## 快速开始

1. 准备小说文本文件，例如 `examples/sample_novel.txt`
2. 运行脚本：

```bash
python scripts/run_distillation.py --input examples/sample_novel.txt --output output/demo_archive
```

3. 运行完成后，会在 `output/demo_archive/` 中生成：
- `source/novel.txt`
- `prompts/main_prompt.md`
- `distillation_archive/01_作品总览.md`
- `distillation_archive/02_人物档案.md`
- `distillation_archive/03_世界设定.md`
- `distillation_archive/04_剧情结构.md`
- `distillation_archive/05_伏笔与回收.md`
- `distillation_archive/06_风格与语言.md`
- `distillation_archive/07_续写蓝图.md`
- `distillation_archive/08_审校清单.md`
- `metadata.json`

## 使用说明

- 你可以把生成的 `prompts/main_prompt.md` 作为大模型的系统提示词或用户提示词。
- 生成的档案文件可以直接作为后续人工/模型续写的工作底稿。
- 这个版本先提供“工程化骨架 + 可执行入口”，后续可以继续扩展成：
  - 支持上传文本自动处理
  - 支持交互式网页界面
  - 支持把蒸馏结果进一步导出为 JSON/CSV/Docx

## 说明

当前版本重点解决的是“把一篇作品文本转成可执行的蒸馏工程目录”。如果你需要进一步把它升级为“自动调用大模型进行蒸馏”的版本，我可以继续帮你补上调用接口。