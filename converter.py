import pdfplumber

def is_bold(fontname: str) -> bool:
    return "Bold" in fontname or "bold" in fontname

def is_italic(fontname: str) -> bool:
    return "Italic" in fontname or "Oblique" in fontname or "italic" in fontname or "oblique" in fontname

def wrap_markdown(text: str, bold: bool, italic: bool) -> str:
    if bold and italic:
        return f"***{text}***"
    elif bold:
        return f"**{text}**"
    elif italic:
        return f"*{text}*"
    else:
        return text

def extract_paragraphs_from_pdf(pdf_path: str, line_gap_threshold: float = 5.0) -> list[str]:
    paragraphs = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = []
            for block in page.extract_words(
                use_text_flow=True, 
                keep_blank_chars=True, 
                extra_attrs=["top", "bottom", "fontname", "size"]):
                words.append(block)

            words.sort(key=lambda x: (x["top"], x["x0"]))

            paragraph = ""
            prev_bottom = None

            for word in words:
                text = word["text"].strip()
                if not text:
                    continue

                top = word["top"]
                font = word.get("fontname", "")
                bold = is_bold(font)
                italic = is_italic(font)
                styled_text = wrap_markdown(text, bold, italic)

                if prev_bottom is not None:
                    gap = top - prev_bottom
                    if gap > line_gap_threshold:
                        if paragraph:
                            paragraphs.append(paragraph.strip())
                            paragraph = ""

                paragraph += " " + styled_text
                prev_bottom = word["bottom"]

            if paragraph:
                paragraphs.append(paragraph.strip())

    return paragraphs

def convert_to_markdown(paragraphs: list[str]) -> str:
    return "\n\n".join(paragraphs)

def save_markdown(markdown_text: str, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

if __name__ == "__main__":
    input_pdf = "input.pdf"
    output_md = "output.md"

    paragraphs = extract_paragraphs_from_pdf(input_pdf, line_gap_threshold=7.0)
    markdown = convert_to_markdown(paragraphs)
    save_markdown(markdown, output_md)
    print(f"Zapisano {len(paragraphs)} paragrafów do pliku: {output_md}")
