#!/usr/bin/env python3
"""
Stage 1: 封面生成 v4.0 — Flux 底图 + 文字叠加

流程：
1. 调用 ComfyUI Flux 生成绘本风底图（无文字）
2. 在底图上叠加文字（右侧对齐，标题最大）

用法（独立调用）:
  python3 stage_cover.py --output cover.png --title "回到星星" --episode-id "S02E09"

管线调用时自动检测已有底图，避免重复生成。
"""
import argparse
import json
import os
import sys
import time
import urllib.request

# ─── 配置 ───
COMFYUI_URL = "http://127.0.0.1:8188"
DEFAULT_QIQI = os.path.expanduser("~/.openclaw/workspace/characters/qiqi_default.png")

# 每集 Flux prompt 模板
FLUX_PROMPT_TEMPLATE = (
    "watercolor children's book illustration, "
    "a cute little girl named Qiqi with round face, big bright eyes, "
    "wearing a pink dress and a star-shaped hairpin, "
    "sitting on a tiny asteroid planet, "
    "meeting a little prince with blonde hair and green coat and red scarf, "
    "{scene_description}"
    "warm sunset sky with orange pink yellow gradient, "
    "soft dreamy atmosphere, magical stars in background, "
    "gentle and tender pastel colors, "
    "wide 1920x1080 composition, space on the right for text"
)

# 各集场景描述
SCENE_DESCRIPTIONS = {
    "S02E09": "the little prince saying goodbye to Qiqi under the starry sky, "
              "golden wheat field, one red rose on the tiny planet, "
              "tears of love and farewell, bittersweet mood, ",
    "S02E10": "Qiqi drawing a picture of the little prince and the rose in her star journal, "
              "glowing stars around her, warm candlelight, "
              "peaceful and nostalgic, ",
    "default": "the little prince and Qiqi looking at a single red rose "
               "under a glass dome on a tiny planet, "
               "friendship and wonder, "
}


def find_font(weight, size):
    font_paths = {
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
    from PIL import ImageFont
    for fp in font_paths.get(weight, font_paths['regular']):
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_flux_base(episode_id, output_path, scene_desc=""):
    """用 Flux 生成封面底图"""
    if not scene_desc:
        scene_desc = SCENE_DESCRIPTIONS.get(episode_id, SCENE_DESCRIPTIONS["default"])

    prompt = FLUX_PROMPT_TEMPLATE.format(scene_description=scene_desc)

    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "flux1-schnell.safetensors", "weight_dtype": "default"}
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "t5xxl_fp16.safetensors",
                "clip_name2": "clip_l.safetensors",
                "type": "flux",
                "device": "default"
            }
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "ae.safetensors"}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": prompt}
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": "text, words, letters, watermark, logo, signature, ugly, deformed, blurry, photorealistic"}
        },
        "6": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": 1920, "height": 1080, "batch_size": 1}
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": hash(episode_id) % 10000 + 1,
                "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                "scheduler": "normal", "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"vae": ["3", 0], "samples": ["7", 0]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"cover_base/{episode_id}_base",
                "images": ["8", 0]
            }
        }
    }

    print("  🎨 生成 Flux 底图...")
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        prompt_id = result.get("prompt_id")

        for _ in range(60):
            time.sleep(5)
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10) as h_resp:
                history = json.loads(h_resp.read())
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_out in outputs.items():
                        if "images" in node_out:
                            for img in node_out["images"]:
                                dl_url = f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type=output"
                                with urllib.request.urlopen(dl_url, timeout=60) as dl_resp:
                                    img_data = dl_resp.read()
                                    with open(output_path, "wb") as f:
                                        f.write(img_data)
                                    print(f"  ✅ 底图: {output_path} ({len(img_data)/1024:.0f} KB)")
                                    return True
    print("  ❌ 底图生成超时")
    return False


def add_text_overlay(base_img_path, output_path, series_name, episode_id, title,
                     education="", brand="琪琪的魔法故事屋"):
    """在底图上叠加文字"""
    from PIL import Image, ImageDraw

    img = Image.open(base_img_path).convert('RGBA')
    W, H = img.size
    draw = ImageDraw.Draw(img)

    font_title = find_font('bold', 120)
    font_series = find_font('bold', 56)
    font_ep = find_font('bold', 42)
    font_edu = find_font('medium', 36)
    font_brand = find_font('bold', 48)

    text_x = W - 80
    y_start = 80
    lg = 100

    DEEP_SPACE = (20, 10, 50)
    WHITE = (255, 255, 255)

    def draw_styled(text, x, y, font, fill_color, outline_color=WHITE, outline_width=10, anchor="rm"):
        for step in range(-outline_width, outline_width + 1, 3):
            for dy_step in range(-outline_width, outline_width + 1, 3):
                if step * step + dy_step * dy_step <= outline_width * outline_width:
                    draw.text((x + step, y + dy_step), text,
                              fill=outline_color, font=font, anchor=anchor)
        draw.text((x, y), text, fill=fill_color, font=font, anchor=anchor)

    # 右侧文字
    draw_styled(series_name, text_x, y_start, font_series, WHITE, DEEP_SPACE, 6, "rm")
    draw_styled(episode_id, text_x, y_start + lg * 1.2, font_ep, (220, 210, 240), DEEP_SPACE, 5, "rm")
    draw_styled(title, text_x, y_start + lg * 2.2, font_title, WHITE, DEEP_SPACE, 12, "rm")
    if education:
        draw_styled(education, text_x, y_start + lg * 3.5, font_edu, (210, 200, 230), DEEP_SPACE, 5, "rm")

    # 左下角品牌
    tw = draw.textlength(brand, font=font_brand)
    brand_x = 80
    bar_y = H - 55
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [brand_x - 15, bar_y - 20, brand_x + tw + 15, bar_y + 28],
        radius=12, fill=(20, 10, 50, 180))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    draw_styled(brand, brand_x, bar_y + 2, font_brand, WHITE, DEEP_SPACE, 4, "lm")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    img.convert('RGB').save(output_path, quality=95)
    print(f"  ✅ 封面: {output_path}")


def main():
    p = argparse.ArgumentParser(description="Stage 1: 封面 v4.0")
    p.add_argument("--output", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", default="琪琪遇见小王子")
    p.add_argument("--episode-id", default="S02E09")
    p.add_argument("--brand", default="琪琪的魔法故事屋")
    p.add_argument("--education", default="")
    p.add_argument("--base", default=None, help="已有底图路径（跳过 Flux 生成）")
    p.add_argument("--width", type=int, default=1920, help=argparse.SUPPRESS)
    p.add_argument("--height", type=int, default=1080, help=argparse.SUPPRESS)
    p.add_argument("--qiqi", default=None, help=argparse.SUPPRESS)
    args = p.parse_args()

    # 底图路径
    if args.base and os.path.exists(args.base):
        base_path = args.base
        print(f"  📂 使用已有底图: {base_path}")
    else:
        # 检查是否有缓存底图
        cache_dir = os.path.expanduser("~/.openclaw/workspace/cover_bases/")
        os.makedirs(cache_dir, exist_ok=True)
        base_path = os.path.join(cache_dir, f"{args.episode_id}_base.png")

        if not os.path.exists(base_path):
            if not generate_flux_base(args.episode_id, base_path):
                print("  ❌ Flux 底图生成失败")
                sys.exit(1)
        else:
            print(f"  📂 使用缓存底图: {base_path}")

    # 叠加文字
    add_text_overlay(
        base_path, args.output,
        args.subtitle, args.episode_id, args.title,
        args.education, args.brand
    )


if __name__ == "__main__":
    main()
