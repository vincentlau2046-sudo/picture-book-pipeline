#!/usr/bin/env python3
"""
stage_kenburns.py v2.0 — 静态画面 (取消 Ken Burns 缩放/移动)

将单张场景图直接作为视频片段，保持静态，不缩放不移动。
每个场景输出一个 1920x1080, 25fps 的 mp4，时长=duration_s。

用法: python3 stage_kenburns.py 1920 1080

输入: input/scene_prompts.json (scene, scene_id, duration_s)
输出: scenes/scene_*.mp4 (静态画面, 无缩放)
"""

import json, subprocess, sys, os

WIDTH, HEIGHT = 1920, 1080
if len(sys.argv) >= 3:
    WIDTH = int(sys.argv[1])
    HEIGHT = int(sys.argv[2])

# 查找 scene_prompts.json
for p in ['input/scene_prompts.json', '../input/scene_prompts.json']:
    if os.path.isfile(p):
        prompt_path = p
        break
else:
    print("ERROR: scene_prompts.json not found")
    sys.exit(1)

with open(prompt_path, encoding='utf-8') as f:
    prompts = json.load(f)

scenes = []
for p in prompts:
    # 兼容 scene_id 和 scene 字段
    sid = p.get('scene_id') or p.get('scene', '')
    dur = p.get('duration_s', 10.0)
    if sid:
        scenes.append((sid, dur))

print(f"[stage_kenburns] {len(scenes)} scenes, resolution={WIDTH}x{HEIGHT} (static, no zoom)")

for sid, duration in scenes:
    scene_png = f"scenes/scene_{sid}.png"
    scene_mp4 = f"scenes/scene_{sid}.mp4"

    if not os.path.isfile(scene_png):
        print(f"  SKIP {sid}: {scene_png} not found")
        continue

    print(f"  [{sid}] {duration:.1f}s static frame → {scene_mp4}")
    cmd = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", scene_png,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=disable",
        "-r", "25",
        "-preset", "medium",
        "-crf", "18",
        scene_mp4,
    ]
    subprocess.run(cmd, check=True)
    print(f"  → {scene_mp4}")

print(f"[stage_kenburns] Done. {len(scenes)} static clips generated.")
