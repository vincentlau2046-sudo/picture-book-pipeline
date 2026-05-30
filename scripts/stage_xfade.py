#!/usr/bin/env python3
"""
stage_xfade.py v2.0 — 静态画面串联

将多个 mp4 片段用 xfade 淡入淡出串联成一个完整视频。

用法: python3 stage_xfade.py [xfade_duration]

输入: scenes/scene_S*.mp4
输出: video_noaudio.mp4
"""

import json, subprocess, sys, os

FFMPEG = os.path.expanduser("~/bin/ffmpeg")
XF_DURATION = 1.0
if len(sys.argv) >= 2:
    XF_DURATION = float(sys.argv[1])

# 找到 scene_prompts.json
for p in ['input/scene_prompts.json', '../input/scene_prompts.json']:
    if os.path.isfile(p):
        prompt_path = p
        break
else:
    print("ERROR: scene_prompts.json not found")
    sys.exit(1)

with open(prompt_path, encoding='utf-8') as f:
    prompts = json.load(f)

# 兼容 scene_id / scene 字段
clips = []
for s in prompts:
    sid = s.get('scene_id') or s.get('scene', '')
    if sid:
        c = f"scenes/scene_{sid}.mp4"
        if os.path.isfile(c):
            clips.append(c)

print(f"[stage_xfade] {len(clips)} clips, xfade={XF_DURATION}s")

if not clips:
    print("ERROR: no clips found")
    sys.exit(1)

if len(clips) == 1:
    subprocess.run(["cp", "-v", clips[0], "video_noaudio.mp4"], check=True)
    print("[stage_xfade] Single clip, copied.")
    sys.exit(0)

# 获取每个clip时长 (用 ffmpeg 替代 ffprobe)
def get_duration(path):
    result = subprocess.run(
        [FFMPEG, "-i", path],
        capture_output=True, text=True
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 10.0

# 构建 xfade filter
inputs = []
for c in clips:
    inputs.extend(["-i", c])

durations = [get_duration(c) for c in clips]
n = len(clips)
offset = 0
filter_parts = []
for i in range(n - 1):
    filter_parts.append(f"[{i}][{i+1}]xfade=transition=fade:duration={XF_DURATION}:offset={offset}")
    offset += durations[i] - XF_DURATION

filter_parts.append(f"[{n-1}]format=yuv420p[outv]")
full_filter = ";".join(filter_parts)

cmd = [FFMPEG, "-y"] + inputs + [
    "-filter_complex", full_filter,
    "-map", "[outv]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "video_noaudio.mp4",
]
print(f"[stage_xfade] Building xfade with {n} clips...")
subprocess.run(cmd, check=True)
print("[stage_xfade] Done → video_noaudio.mp4")
