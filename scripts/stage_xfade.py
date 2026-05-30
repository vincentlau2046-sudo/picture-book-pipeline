#!/usr/bin/env python3
"""
stage_xfade.py v2.0 — 静态画面串联 (concat demuxer)

将多个 mp4 片段用 ffmpeg concat demuxer 串联成一个完整视频。

用法: python3 stage_xfade.py [xfade_duration]

输入: scenes/scene_*.mp4 (scene_prompts.json 按顺序)
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
            clips.append((sid, c, s.get('duration_s', 10.0)))

print(f"[stage_xfade] {len(clips)} clips, concat demuxer")

if not clips:
    print("ERROR: no clips found")
    sys.exit(1)

if len(clips) == 1:
    subprocess.run(["cp", "-v", clips[0][1], "video_noaudio.mp4"], check=True)
    print("[stage_xfade] Single clip, copied.")
    sys.exit(0)

# 用 concat demuxer 串联 (简单可靠，适合静态画面)
concat_file = "concat_list.txt"
with open(concat_file, "w") as f:
    for i, (sid, clip_path, dur) in enumerate(clips):
        abs_path = os.path.abspath(clip_path)
        f.write(f"file '{abs_path}'\n")
        if i < len(clips) - 1:  # 最后一个clip不加outpoint
            f.write(f"outpoint {dur}\n")

cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
       "-c", "copy", "-avoid_negative_ts", "make_zero",
       "video_noaudio.mp4"]

print(f"[stage_xfade] Building concat with {len(clips)} clips...")
subprocess.run(cmd, check=True)
print("[stage_xfade] Done → video_noaudio.mp4")
