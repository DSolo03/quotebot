from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

def font_has_glyph(font: TTFont, character: str) -> bool:
    cmap = font['cmap']
    for table in cmap.tables: # type: ignore
        if table.isUnicode():
            if ord(character) in table.cmap:
                return True
    return False

def character_filter(font: TTFont, text: str) -> str:
    out = []
    for character in text:
        if font_has_glyph(font, character) or character == "\n":
            out.append(character) 
    return "".join(out)

def get_bounding_font(
        draw: ImageDraw.ImageDraw, 
        text: str, 
        font_path: Path, 
        bounding_box: tuple[int, int, int, int]
    ) -> FreeTypeFont:
    x1, y1, x2, y2 = bounding_box
    box_width = abs(x1 - x2)
    box_height = abs(y1 - y2)

    low, high = 1, 100
    size = low

    while low <= high:
        mid = (low + high) // 2

        font = ImageFont.truetype(font_path, mid)
        wrapped_text = wrap_text(draw, text, font, box_width)
        box = draw.multiline_textbbox((0,0), wrapped_text, font = font)
        text_width = abs(box[2] - box[0])
        text_height = abs(box[1] - box[3])

        if text_width > box_width or text_height > box_height:
            high = mid - 1
        else:
            size = mid
            low = mid + 1

    return ImageFont.truetype(font_path, size)

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: FreeTypeFont, max_width: int) -> str:
    lines = []
    for original_line in text.split("\n"):
        words = original_line.split(" ")
        current = ""
        for word in words:
            test = word if current == "" else current + " " + word
            width = draw.textbbox((0, 0), test, font=font)[2]
            if width <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return "\n".join(lines)

def bound_text(
        image: Image.Image, 
        text: str, 
        bounding_box: tuple[int, int, int, int], 
        font: Path, 
        font_color: str
    ):
    x1, y1, x2, y2 = bounding_box
    size = (
        abs(x1 - x2),
        abs(y1 - y2)
    )
    center = (
        size[0] / 2 + x1,
        size[1] / 2 + y1
    )
    draw = ImageDraw.Draw(image)
    text_font = get_bounding_font(draw, text, font, bounding_box)
    text = wrap_text(draw, text, text_font, size[0])
    draw.multiline_text(center, text, font_color, text_font, "mm")