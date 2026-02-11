import fitz
import shutil
from pathlib import Path

PAPERS_DIR = Path("pdfs")
OUTPUT_DIR = Path("corpus")
CONVERTED_DIR = PAPERS_DIR / "converted"

def convert_pdf_to_txt(pdf_path: Path, output_dir: Path):
    doc = fitz.open(pdf_path)
    txt_content = []

    for page_num, page in enumerate(doc, 1):
        txt_content.append(f"# Page {page_num}\n")
        txt_content.append(page.get_text())
        txt_content.append("\n---\n")

    doc.close()

    output_path = output_dir / pdf_path.with_suffix(".txt").name

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_content))

    print(f"Converted: {pdf_path} -> {output_path}")
    return output_path

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = [f for f in PAPERS_DIR.glob("*.pdf") if f.is_file()]
    print(f"Found {len(pdf_files)} PDF files to convert")

    for pdf_path in pdf_files:
        convert_pdf_to_txt(pdf_path, OUTPUT_DIR)
        dest = CONVERTED_DIR / pdf_path.name
        shutil.move(str(pdf_path), str(dest))
        print(f"Moved: {pdf_path} -> {dest}")

if __name__ == "__main__":
    main()
