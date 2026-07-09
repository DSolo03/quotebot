from dataclasses import dataclass
from pathlib import Path

import yaml
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from text import bound_text

@dataclass
class BoundingBox:
    left_top: tuple[int, int]
    right_bottom: tuple[int, int]
    def unpack(self) -> tuple[int, int, int, int]:
        return self.left_top + self.right_bottom

@dataclass
class Quote:
    text: str = ""
    username: str = ""
    userpic: Path | None = None

class Skin:
    background: Path
    background_box: BoundingBox
    userpic_default: Path
    userpic_location: tuple[int, int]
    userpic_radius: int
    userpic_border_radius: int
    userpic_border_color: tuple[int, int, int, int]
    username_align: str
    username_color: str
    font: Path
    font_obj: TTFont
    font_color: str

    def __validate_path__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(path)

    def __init__(self, path: Path):
        config = dict()

        path = Path(path)

        config_file = path / "config.yaml"
        self.__validate_path__(config_file)
        
        with config_file.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        self.background = path / config["background"]["filename"]
        self.__validate_path__(self.background)
        
        left_top = tuple(config["background"]["left_top"])
        right_bottom = tuple(config["background"]["right_bottom"])
        self.background_box = BoundingBox(left_top, right_bottom)

        self.userpic_default = path / config["userpic"]["filename"]
        self.__validate_path__(self.userpic_default)
        
        self.userpic_location = tuple(config["userpic"]["location"])
        self.userpic_radius = config["userpic"]["radius"]
        self.userpic_border_radius = config["userpic"]["border_radius"]
        self.userpic_border_color = tuple(config["userpic"]["border_color"])

        self.username_color = config["username"]["color"]
        self.username_align = config["username"]["align"]

        self.font = path / config["font"]["filename"]
        self.__validate_path__(self.font)
        self.font_obj = TTFont(self.font)

        self.font_color = config["font"]["color"]

    def round_userpic(self, userpic: Image.Image) -> Image.Image:
        avatar = userpic.resize((2 * self.userpic_radius, 2 * self.userpic_radius), Image.Resampling.LANCZOS)
        mask = Image.new("L", (8 * self.userpic_radius, 8 * self.userpic_radius), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 8 * self.userpic_radius, 8 * self.userpic_radius), fill = 255)
        mask = mask.resize((2 * self.userpic_radius, 2 * self.userpic_radius), Image.Resampling.LANCZOS)
        avatar.putalpha(mask)

        return avatar
    
    def smooth_circle(self, radius, color = (0, 0, 0, 255), scale = 4) -> Image.Image:
        size = radius * 2
        big_size = size * scale
        img = Image.new("RGBA", (big_size, big_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse(
            (0, 0, big_size - 1, big_size - 1),
            fill=color
        )
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        return img

    def render_quote(self, quote: Quote, hide_userpic = False):
        canvas = Image.open(self.background).convert("RGBA")
        draw = ImageDraw.Draw(canvas)

        if not hide_userpic:
            if not quote.userpic:
                quote.userpic = self.userpic_default
            avatar_center = (
                self.userpic_location[0] + self.userpic_radius, 
                self.userpic_location[1] + self.userpic_radius
            )
            border_location = (
                self.userpic_location[0] - self.userpic_border_radius, 
                self.userpic_location[1] - self.userpic_border_radius
            )

            try:
                with Image.open(quote.userpic) as userpic:
                    avatar = self.round_userpic(userpic.convert("RGBA"))
            except UnidentifiedImageError: # Last stand
                with Image.open(self.userpic_default) as userpic:
                    avatar = self.round_userpic(userpic.convert("RGBA"))
            
            border = self.smooth_circle(
                self.userpic_radius + self.userpic_border_radius, 
                color = self.userpic_border_color
            )
            
            canvas.paste(border, border_location, border)
            canvas.paste(avatar, self.userpic_location, avatar)
            
            anchor = "lm"
            name_location = (avatar_center[0] - self.userpic_radius - 20, avatar_center[1])

            match self.username_align:
                case "left":
                    anchor = "rm"
                    name = f"{quote.username} ©"
                    name_location = (avatar_center[0] - self.userpic_radius - 20, avatar_center[1])
                case "right":
                    anchor = "lm"
                    name = f"© {quote.username}"
                    name_location = (avatar_center[0] + self.userpic_radius + 20, avatar_center[1])
                case _:
                    raise NotImplementedError(self.username_align)
                
            stroke = "black"

            match self.username_color:
                case "white":
                    stroke = "black"
                case "black":
                    stroke = "white"

            name_font = ImageFont.truetype(self.font, size = 53)

            draw.text(
                name_location, 
                name, 
                self.username_color, 
                name_font, 
                anchor = anchor, 
                stroke_width = 3, 
                stroke_fill = stroke
            )
                
        bound_text(canvas, quote.text, self.background_box.unpack(), self.font, self.font_color)

        return canvas