import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration

load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

translate_function = FunctionDeclaration(
    name="store_translation",
    description="Translate Armenian text to French and return structured result.",
    parameters={
        "type": "object",
        "properties": {
            "translation": {
                "type": "string",
                "description": "The translated French version of the input text",
            }
        },
        "required": ["translation"],
    },
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[translate_function],
    tool_config={"function_calling_config": {"mode": "any"}},
)


def translate_paragraph(text: str) -> str:
    response = model.generate_content(
        [f"Translate the following Armenian text into French.\n\n{text}"]
    )

    try:
        return response.candidates[0].content.parts[0].function_call.args["translation"]
    except Exception as e:
        print("❌ Structured generation failed. Raw output:\n", response.text)
        return "[PARSE ERROR]"


def translate_folder(input_dir: Path, output_dir: Path, min_length: int = 200):
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_file in sorted(input_dir.glob("page_*.json")):
        page_id = json_file.stem  # e.g. "page_0"
        output_file = output_dir / f"{page_id}.json"

        if output_file.exists():
            print(f"✅ Skipping {page_id} — already translated.")
            continue

        with json_file.open(encoding="utf-8") as f:
            data = json.load(f)

        translated = {"metadata": data["metadata"], "paragraphs": []}

        for para in data["paragraphs"]:
            if para["length"] >= min_length:
                print(f"Translating paragraph {para['bbox']} on {page_id}")
                fr_text = translate_paragraph(para["text"])
                translated["paragraphs"].append(
                    {
                        "bbox": para["bbox"],
                        "original": para["text"],
                        "translated": fr_text,
                    }
                )

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
