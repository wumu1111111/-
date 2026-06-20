import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests

SECTION_FILES = {
    "作品总览": "01_作品总览.md",
    "人物档案": "02_人物档案.md",
    "世界设定": "03_世界设定.md",
    "剧情结构": "04_剧情结构.md",
    "伏笔与回收": "05_伏笔与回收.md",
    "风格与语言": "06_风格与语言.md",
    "续写蓝图": "07_续写蓝图.md",
    "审校清单": "08_审校清单.md",
}

PROVIDER_PRESETS = {
    "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4.1-mini"},
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "智谱AI": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-plus"},
    "通义千问": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-max"},
    "Moonshot": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "SiliconFlow": {"base_url": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen2.5-72B-Instruct"},
    "OpenRouter": {"base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o-mini"},
    "自定义": {"base_url": "https://api.openai.com/v1", "model": "gpt-4.1-mini"},
}


def normalize_base_url(base_url: str) -> str:
    value = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    if value.endswith("/chat/completions"):
        return value[: -len("/chat/completions")]
    if value.endswith("/v1"):
        return value
    if "/v1" in value:
        return value
    return value + "/v1"


def call_chat_completion(
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 1800,
) -> str:
    endpoint = normalize_base_url(base_url) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2400,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    if response.status_code >= 400:
        raise RuntimeError(f"API 请求失败：{response.status_code} {response.text}")
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"API 返回格式异常：{data}") from exc


def parse_model_output(raw_text: str) -> Dict[str, str]:
    text = raw_text.strip()
    if text.startswith("```json"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    elif text.startswith("```"):
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        text = match.group(0)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"模型返回不是有效 JSON：{text[:1000]}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("模型返回的不是对象格式")
    result: Dict[str, str] = {}
    for section_name, filename in SECTION_FILES.items():
        if section_name in payload:
            value = payload[section_name]
            if isinstance(value, str):
                result[section_name] = value
            else:
                result[section_name] = json.dumps(value, ensure_ascii=False, indent=2)
    if not result:
        raise RuntimeError("模型返回中没有识别到任何蒸馏章节")
    return result


def build_system_prompt(title: str) -> str:
    return f"""
你是一名专业的长篇网络文学蒸馏师、叙事分析师与续写顾问。
你的任务不是“概括”，而是“高保真重建原作的结构、人物、设定、风格、节奏、情绪与叙事逻辑”，以便后续进行忠实续写、同人创作或改编。

请遵守以下要求：
1. 先提取事实，再总结解释；任何结论必须能追溯到原文证据。
2. 不能因为概括而制造新设定；如信息不足，请明确写成“待确认/推测/低置信度”。
3. 你必须同时重建：主线、人物、关系、世界规则、因果链、伏笔、情绪节奏、章节功能与续写可用性。
4. 你需要特别注意网文的“连续阅读动力”：悬念、爽点、反转、虐点、成长、资源推进、章节收束等。
5. 输出必须是严格的 JSON 对象，不要额外解释文本。
6. 键名必须是以下 8 个：作品总览、人物档案、世界设定、剧情结构、伏笔与回收、风格与语言、续写蓝图、审校清单。
7. 每个值都必须是一段 Markdown 文本，可以包含标题、列表、子标题、表格与说明，适合直接写入文件。
8. 你要尽量保留原文的关键信息、场景特征、人物口吻、语言气质和叙事节奏，而不是只给抽象总结。
9. 作品标题：{title}

请把每一节写得足够细，内容要覆盖：
- 作品总览：故事核心、主线一句话概括、气质、情绪、独特性和续写锚点。
- 人物档案：人物基本信息、外貌、性格、口头禅、动机、欲望、恐惧、关系、成长线、底线、续写约束。
- 世界设定：世界观背景、地理与场景、权力结构、规则系统、硬规则/软规则、文化常识。
- 剧情结构：主线脉络、关键转折、伏笔与回收、高潮与结局、因果链、节奏节点。
- 伏笔与回收：每个伏笔的出现位置、作用、回收方式、闭环与风险点。
- 风格与语言：叙事视角、句式特征、描写偏好、情绪表达、语言气质、可复用的写法模板。
- 续写蓝图：最重要的三条续写原则、角色底线、设定硬约束、下一步推进方向、情绪/节奏区间、典型错误、接续提示词。
- 审校清单：事实与推测的标注、角色一致性、世界规则一致性、续写接续性、风险点说明。
"""


def build_user_prompt(text: str, title: str, source_name: str) -> str:
    preview = text[:28000]
    return f"""
作品标题：{title}
来源文件：{source_name}
正文如下（仅取前 28000 字符作为输入，若文稿更长请在输出中标注“待确认/推测/低置信度”）：

{preview}

请严格输出 JSON。不要额外说明。请确保每个章节里的内容足够细致、足够实用，便于后续接续写作。
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_main_prompt_file(title: str, source_name: str, word_count: int, char_count: int) -> str:
    return f"""# 主提示词模板

作品名称：{title}
来源文件：{source_name}
词数：{word_count}
字符数：{char_count}

你是一个专业的长篇网络文学蒸馏师、叙事分析师和续写顾问。
你的任务不是“概括”，而是“高保真重建原作的结构、人物、设定、风格、节奏与叙事逻辑”，以便后续进行忠实续写、同人创作或改编。

请遵守以下要求：
1. 先提取事实，再总结解释；任何结论必须能追溯到原文证据。
2. 不能因为概括而制造新设定；如信息不足，请明确写成“待确认/推测/低置信度”。
3. 必须同时重建主线、人物、关系、世界规则、因果链、伏笔、情绪节奏、章节功能与续写可用性。
4. 要特别注意网文的连续阅读动力：悬念、爽点、反转、虐点、成长、资源推进、章节收束等。
5. 输出必须是严格的 JSON 对象，键名必须是 8 个章节名。
6. 每个值都必须是一段 Markdown 文本，适合直接写入文件。

请针对以下 8 个部分分别输出：
- 作品总览
- 人物档案
- 世界设定
- 剧情结构
- 伏笔与回收
- 风格与语言
- 续写蓝图
- 审校清单

请在输出时尽量使用结构化内容，并在信息不足时明确标注“待确认/推测/低置信度”。
"""


def distill_text_file(
    input_path: Path,
    output_dir: Path,
    title: str,
    api_key: str,
    base_url: str,
    model: str,
    progress_callback: Optional[object] = None,
    log_callback: Optional[object] = None,
) -> Dict[str, str]:
    input_path = input_path.resolve()
    output_dir = output_dir.resolve()
    if progress_callback:
        progress_callback("读取输入文件", 5)
    if log_callback:
        log_callback(f"读取文件：{input_path}")
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    word_count = len(re.findall(r"\b\w+\b", text))
    char_count = len(text)

    if progress_callback:
        progress_callback("准备蒸馏提示词", 20)
    if log_callback:
        log_callback("提示词已生成，准备向模型发送请求")
    system_prompt = build_system_prompt(title)
    user_prompt = build_user_prompt(text, title, input_path.name)

    if progress_callback:
        progress_callback("调用模型进行蒸馏", 45)
    if log_callback:
        log_callback("正在调用模型，请稍候...")
    raw_output = call_chat_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    if progress_callback:
        progress_callback("解析模型输出", 70)
    archive_data = parse_model_output(raw_output)

    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    write_file(source_dir / input_path.name, text)

    prompts_dir = output_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    write_file(prompts_dir / "main_prompt.md", build_main_prompt_file(title, input_path.name, word_count, char_count))

    archive_dir = output_dir / "distillation_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    for section_name, content in archive_data.items():
        filename = SECTION_FILES[section_name]
        write_file(archive_dir / filename, content)

    metadata = {
        "title": title,
        "source_file": input_path.name,
        "word_count": word_count,
        "char_count": char_count,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_file(output_dir / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

    readme_content = f"""# {title}

本目录由长篇网文蒸馏器自动生成。

- 输入文件：{input_path.name}
- 词数：{word_count}
- 字符数：{char_count}
- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请查看 `prompts/main_prompt.md` 和 `distillation_archive/` 中的内容，然后根据需要继续人工润色或继续调用模型补全。
"""
    write_file(output_dir / "README.md", readme_content)

    if progress_callback:
        progress_callback("写入结果文件", 95)
    if log_callback:
        log_callback("结果文件已生成")
    if progress_callback:
        progress_callback("完成", 100)
    return archive_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use an OpenAI-compatible API to distill a novel text file")
    parser.add_argument("--input", required=True, help="Path to the input text file")
    parser.add_argument("--output", required=True, help="Directory to store the distillation archive")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="Base URL for the OpenAI-compatible API")
    parser.add_argument("--model", default="gpt-4.1-mini", help="Model name")
    parser.add_argument("--title", default=None, help="Optional title for the archive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    title = args.title or input_path.stem
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    distill_text_file(
        input_path=input_path,
        output_dir=output_dir,
        title=title,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
    )
    print(f"Archive generated at {output_dir}")


if __name__ == "__main__":
    main()
