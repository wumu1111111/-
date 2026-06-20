import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "main_prompt.md"


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def count_chars(text: str) -> int:
    return len(text)


def length_bucket(word_count: int) -> str:
    if word_count < 50000:
        return "短篇/中篇级"
    if word_count < 200000:
        return "中长篇级"
    return "超长篇级"


def short_summary(text: str) -> str:
    preview = re.sub(r"\s+", " ", text.strip())
    if len(preview) <= 220:
        return preview
    return preview[:217].rstrip() + "..."


def mood_summary(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["悬疑", "诡异", "阴谋", "秘密", "危机"]):
        return "偏悬疑/压迫感，适合强节奏推进与反转制造。"
    if any(k in lowered for k in ["爽", "强者", "修炼", "升级", "系统"]):
        return "偏爽文/成长型，强调升级、冲突和资源推进。"
    if any(k in lowered for k in ["爱情", "感情", "相爱", "心动"]):
        return "偏情感线驱动，人物关系与情绪推进尤为重要。"
    return "待进一步分析；建议由模型根据原文补充情绪基调与气质。"


def render_template(template_text: str, context: Dict[str, str]) -> str:
    result = template_text
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", value)
    return result


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_archive(input_path: Path, output_dir: Path, title: str) -> None:
    text = read_text(input_path)
    word_count = count_words(text)
    char_count = count_chars(text)
    bucket = length_bucket(word_count)
    summary = short_summary(text)
    mood = mood_summary(text)

    context = {
        "WORK_TITLE": title,
        "SOURCE_FILE": input_path.name,
        "WORD_COUNT": str(word_count),
        "CHAR_COUNT": str(char_count),
        "LENGTH_BUCKET": bucket,
        "SHORT_SUMMARY": summary,
        "MOOD": mood,
        "FOCUS_1": "人物关系与成长线",
        "FOCUS_2": "世界规则与设定基础",
        "FOCUS_3": "情绪节奏与章节收束",
        "ROLE_BASIC": "待提取：身份、位置、资源背景",
        "ROLE_APPEARANCE": "待提取：外貌与标志性物品",
        "ROLE_PERSONALITY": "待提取：性格核心与行为倾向",
        "ROLE_VOICE": "待提取：说话习惯与口头禅",
        "ROLE_PSYCHOLOGY": "待提取：表层动机、深层欲望与恐惧点",
        "ROLE_RELATIONSHIP": "待提取：与主角、敌对者、同盟者的关系变化",
        "ROLE_ARC": "待提取：成长弧线与主要转折",
        "ROLE_CONSTRAINT": "待提取：续写时不得丢失的底线特征",
        "WORLD_BACKGROUND": "待提取：世界观背景、时代与核心冲突",
        "WORLD_GEOGRAPHY": "待提取：地理与场景结构",
        "WORLD_POWER": "待提取：权力结构与组织关系",
        "WORLD_RULES": "待提取：能力、修炼、规则体系与资源逻辑",
        "WORLD_CULTURE": "待提取：社会常识、语言风格与文化特征",
        "HARD_RULES": "待补充：必须遵守的设定约束",
        "SOFT_RULES": "待补充：可保持风格一致但可调整的规则",
        "STORY_MAINLINE": "待提取：主线推进脉络",
        "STORY_TURNS": "待提取：关键转折点与爆点",
        "STORY_FORESHADOW": "待提取：伏笔与回收设计",
        "STORY_CLIMAX": "待提取：高潮与结局方向",
        "STORY_CAUSAL": "待提取：事件因果链",
        "FORESHADOW_LIST": "待提取：每条伏笔的出现位置��作用",
        "RETRIEVAL_POINTS": "待提取：回收点与回收方式",
        "TURNING_POINTS": "待提取：最重要的转折节点",
        "CLUE_LOOP": "待提取：线索是否形成闭环",
        "STYLE_PERSPECTIVE": "待提取：叙事视角与叙述距离",
        "STYLE_SENTENCE": "待提取：句式偏好与节奏控制",
        "STYLE_DESCRIPTION": "待提取：环境、动作、心理、对话的描写偏好",
        "STYLE_EMOTION": "待提取：情绪表达方式与强弱节奏",
        "STYLE_TONE": "待提取：语言气质与关键词特征",
        "STYLE_TEMPLATE": "待提取：续写时适合复用的句式与段落模式",
        "CONTINUATION_PRINCIPLES": "保留人物底线；维持设定一致性；确保情绪与节奏连续",
        "CHARACTER_BASELINE": "待提取：角色在续写中不得丢失的底层特征",
        "SETTING_CONSTRAINTS": "待提取：世界规则与设定硬约束",
        "NEXT_STEP": "待提取：当前剧情最自然的下一步推进方向",
        "EMOTION_RHYTHM": "待提取：适合接续的情绪区间与节奏区间",
        "COMMON_ERRORS": "概括失真、设定漂移、人物行为失真、情绪节奏断裂",
        "CONTINUATION_PROMPT": "请基于当前档案，继续生成与原作风格一致的下一个章节或连续段落。",
        "CHECK_FACT": "每条关键结论必须能追溯到原文证据。",
        "CHECK_SPECULATION": "所有推测必须标注为“待确认/推测/低置信度”。",
        "CHECK_CHARACTER": "人物行为是否符合其性格、关系和成长轨迹。",
        "CHECK_WORLD_RULES": "世界规则是否保持一致，硬规则是否被误改。",
        "CHECK_CONTINUATION": "续写是否能自然接上当前剧情并保持节奏。",
        "CHECK_RISK": "是否存在设定漂移、情绪断裂或逻辑漏洞。",
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, source_dir / input_path.name)

    prompts_dir = output_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    prompt_text = render_template(PROMPT_TEMPLATE.read_text(encoding="utf-8"), context)
    write_file(prompts_dir / "main_prompt.md", prompt_text)

    archive_dir = output_dir / "distillation_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for template_path in sorted(TEMPLATES_DIR.glob("*.md")):
        template_text = template_path.read_text(encoding="utf-8")
        output_path = archive_dir / template_path.name
        write_file(output_path, render_template(template_text, context))

    write_file(output_dir / "README.md", f"""# {title}\n\n这是由长篇网文蒸馏项目生成的工作目录。\n\n- 输入文件：{input_path.name}\n- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n- 字数：{word_count}\n- 字符数：{char_count}\n- 估计长度：{bucket}\n\n请先查看 `prompts/main_prompt.md` 和 `distillation_archive/` 中的文件，然后把它们交给模型或人工继续补全。\n""")

    metadata = {
        "title": title,
        "source_file": input_path.name,
        "word_count": word_count,
        "char_count": char_count,
        "length_bucket": bucket,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_file(output_dir / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a distillation archive from a novel text file")
    parser.add_argument("--input", required=True, help="Path to the input text file")
    parser.add_argument("--output", required=True, help="Directory where the distillation archive will be written")
    parser.add_argument("--title", default=None, help="Optional title for the archive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    title = args.title or input_path.stem
    build_archive(input_path, output_dir, title)
    print(f"Distillation archive generated at: {output_dir}")


if __name__ == "__main__":
    main()
