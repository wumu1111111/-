# 长篇网文蒸馏器

这是一个面向“长篇网文高保真续写”的 Windows 桌面软件，支持：
- 上传小说文本文件
- 选择内置国产/国际模型提供商
- 只填 API Key 即可使用
- 自动调用大模型生成结构化蒸馏档案
- 实时显示进度、日志和结果预览
- 支持打包为 Windows 可执行文件和安装包

## 主要特点

- 内置多家模型提供商配置：OpenAI、DeepSeek、智谱AI、通义千问、Moonshot、SiliconFlow、OpenRouter
- 用户只需要填写密钥，其他配置已内置
- 支持上传 `.txt` 文本文件
- 自动输出 8 份蒸馏文件和一份元数据文件
- 支持结果预览和日志查看
- 可通过 PyInstaller 打包成 Windows 可执行文件
- 可通过 Inno Setup 生成安装包

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 启动桌面软件

```bash
python app.py
```

## 命令行版本

```bash
python scripts/ai_distillation.py --input examples/sample_novel.txt --output output/demo_archive --api-key YOUR_API_KEY --base-url https://api.deepseek.com/v1 --model deepseek-chat --title "示例小说"
```

## 打包为 Windows 可执行文件

```bash
python build_installer.py
```

生成后的 exe 位于 `dist/installer/长篇网文蒸馏器.exe`。

## 生成 Windows 安装包

请先安装 Inno Setup，然后运行：

```bat
build_installer.bat
iscc installer\installer.iss
```

## 项目结构

```text
.
├── app.py
├── build_installer.py
├── README.md
├── requirements.txt
├── build_installer.bat
├── installer/
│   └── installer.iss
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
│   ├── ai_distillation.py
│   └── run_distillation.py
└── examples/
    └── sample_novel.txt
```
