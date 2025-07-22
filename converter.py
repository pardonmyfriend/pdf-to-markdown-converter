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
    
def detect_font_sizes(pdf_path: str) -> list[float]:
    sizes = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for word in page.extract_words(extra_attrs=["size"]):
                sizes.add(round(word["size"], 1))
    return sorted(sizes, reverse=True)

def map_font_sizes_to_headings(sizes: list[float]) -> tuple[dict[float, str], float]:
    size_to_heading = {size: f'{"#" * (i + 1)}' for i, size in enumerate(sizes[:-1])}
    smallest_size = sizes[-1]
    return size_to_heading, smallest_size

def extract_text_with_style(pdf_path: str, line_gap_threshold: float = 5.0) -> list[str]:
    font_sizes = detect_font_sizes(pdf_path)
    size_to_heading, smallest_size = map_font_sizes_to_headings(font_sizes)

    paragraphs = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=True,
                keep_blank_chars=True,
                extra_attrs=["top", "bottom", "fontname", "size"]
            )

            words.sort(key=lambda x: (x["top"], x["x0"]))

            paragraph = ""
            prev_bottom = None
            current_line_top = None
            current_line_size = None

            for word in words:
                text = word["text"].strip()
                if not text:
                    continue

                top = word["top"]
                bottom = word["bottom"]
                font = word.get("fontname", "")
                size = round(word.get("size", smallest_size), 1)

                bold = is_bold(font)
                italic = is_italic(font)
                styled_text = wrap_markdown(text, bold, italic)

                if prev_bottom is not None:
                    gap = top - prev_bottom
                    if gap > line_gap_threshold:
                        if paragraph:
                            if current_line_size in size_to_heading:
                                heading_md = size_to_heading[current_line_size]
                                paragraphs.append(f"{heading_md} {paragraph.strip()}")
                            else:
                                paragraphs.append(paragraph.strip())
                            paragraph = ""

                if current_line_top is None or abs(top - current_line_top) > 0.1:
                    current_line_top = top
                    current_line_size = size
                            
                paragraph += " " + styled_text
                prev_bottom = word["bottom"]

            if paragraph:
                if current_line_size in size_to_heading:
                    heading_md = size_to_heading[current_line_size]
                    paragraphs.append(f"{heading_md} {paragraph.strip()}")
                else:
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

    paragraphs = extract_text_with_style(input_pdf, line_gap_threshold=7.0)
    markdown = convert_to_markdown(paragraphs)
    save_markdown(markdown, output_md)
    print(f"Zapisano {len(paragraphs)} paragrafów do pliku: {output_md}")
