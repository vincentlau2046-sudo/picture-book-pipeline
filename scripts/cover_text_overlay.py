#!/usr/bin/env python3
"""
封面文字叠加 v4 — 基于 Flux 生成的底图，文字在右侧
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

_FONT_PATHS = {
    'bold': [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc',
    ],
    'medium': [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc',
    ],
    'regular': [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ],
}

def find_font(weight, size):
    for fp in _FONT_PATHS.get(weight, _FONT_PATHS['regular']):
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_text_styled(draw, text, x, y, font, fill_color,
                     outline_color=(255, 255, 255), outline_width=10,
                     anchor="lm"):
    """白色描边 + 主色文字"""
    for step in range(-outline_width, outline_width + 1, 3):
        for dy_step in range(-outline_width, outline_width + 1, 3):
            if step * step + dy_step * dy_step <= outline_width * outline_width:
                draw.text((x + step, y + dy_step), text,
                          fill=outline_color, font=font, anchor=anchor)
    draw.text((x, y), text, fill=fill_color, font=font, anchor=anchor)

def main():
    p = argparse.ArgumentParser(description="封面文字叠加 v4")
    p.add_argument("--base", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--series", default="琪琪遇见小王子")
    p.add_argument("--episode-id", default="S02E09")
    p.add_argument("--title", required=True)
    p.add_argument("--education", default="")
    p.add_argument("--brand", default="琪琪的魔法故事屋")
    args = p.parse_args()

    img = Image.open(args.base).convert('RGBA')
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # 字号层级：标题 > 季名 > 集号 > 教育核心
    font_title = find_font('bold', 120)     # 本集标题（最大）
    font_series = find_font('bold', 56)     # 季名（第二）
    font_ep = find_font('bold', 42)         # 集号
    font_edu = find_font('medium', 36)      # 教育核心
    font_brand = find_font('bold', 48)      # 品牌

    # 右上角文字区域（人物在左侧）
    text_x = W - 80
    y_start = 80
    lg = 100  # 行间距

    # 颜色：深空蓝紫（和暖色底图互补）
    DEEP_SPACE = (20, 10, 50)
    WHITE = (255, 255, 255)

    # === 右上角：文字右对齐 ===
    draw_text_styled(draw, args.series,
                     text_x, y_start, font_series,
                     fill_color=WHITE, outline_color=DEEP_SPACE, outline_width=6,
                     anchor="rm")

    draw_text_styled(draw, args.episode_id,
                     text_x, y_start + lg * 1.2, font_ep,
                     fill_color=(220, 210, 240), outline_color=DEEP_SPACE, outline_width=5,
                     anchor="rm")

    draw_text_styled(draw, args.title,
                     text_x, y_start + lg * 2.2, font_title,
                     fill_color=WHITE, outline_color=DEEP_SPACE, outline_width=12,
                     anchor="rm")

    if args.education:
        draw_text_styled(draw, args.education,
                         text_x, y_start + lg * 3.5, font_edu,
                         fill_color=(210, 200, 230), outline_color=DEEP_SPACE, outline_width=5,
                         anchor="rm")

    # === 左下角：品牌 ===
    brand_text = args.brand
    brand_font = font_brand
    tw = draw.textlength(brand_text, font=brand_font)
    brand_x = 80
    bar_y = H - 55

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [brand_x - 15, bar_y - 20, brand_x + tw + 15, bar_y + 28],
        radius=12,
        fill=(20, 10, 50, 180)
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    draw_text_styled(draw, brand_text,
                     brand_x, bar_y + 2, brand_font,
                     fill_color=WHITE, outline_color=DEEP_SPACE, outline_width=4)

    img_rgb = img.convert('RGB')
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    img_rgb.save(args.output, quality=95)
    print(f"✅ 封面: {args.output}")

if __name__ == "__main__":
    main()
