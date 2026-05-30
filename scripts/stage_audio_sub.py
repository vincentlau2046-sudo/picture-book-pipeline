#!/usr/bin/env python3
"""
Stage 4: 添加音频 + ASS 字幕
输入：无音频视频 + 音频文件 + ASS 字幕文件
输出：带音频和字幕的最终视频
"""
import argparse
import os
import re
import subprocess
import sys

FFMPEG = os.path.expanduser("~/bin/ffmpeg")


def get_duration(path):
    result = subprocess.run(
        [FFMPEG, '-i', path, '-f', 'null', '-'],
        capture_output=True, text=True
    )
    m = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', result.stderr)
    if m:
        h, mn, s, ms = m.groups()
        return int(h)*3600 + int(mn)*60 + int(s) + int(ms)/100
    return 0


def main():
    p = argparse.ArgumentParser(description="Stage 4: 添加音频 + ASS 字幕")
    p.add_argument("--video", required=True, help="输入视频（无音频）")
    p.add_argument("--audio", required=True, help="旁白音频文件")
    p.add_argument("--ass", required=True, help="ASS 字幕文件")
    p.add_argument("--output", required=True, help="输出最终视频")
    p.add_argument("--video-bitrate", default="2500k", help="视频码率")
    p.add_argument("--audio-bitrate", default="192k", help="音频码率")
    args = p.parse_args()

    # ASS 文件路径需要转义（ffmpeg ass 滤镜特殊处理）
    ass_path = os.path.abspath(args.ass)
    
    vf = f"ass='{ass_path}'"
    
    # 获取音频和视频时长
    audio_dur = get_duration(args.audio)
    video_dur = get_duration(args.video)
    
    # 修复: 确保音频完整保留
    # 如果视频比音频短，先用黑帧延长视频到音频长度
    if video_dur < audio_dur:
        padding = audio_dur - video_dur + 1.0  # 额外1s安全余量
        print(f"⚠️ 视频比音频短 {padding:.1f}s，正在用黑帧延长...")
        padded_video = os.path.join(os.path.dirname(args.output), "_padded_video.mp4")
        subprocess.run([
            FFMPEG, '-y',
            '-i', args.video,
            '-f', 'lavfi', '-i', f'color=c=black:s=1920x1080:r=30:d={padding}',
            '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0',
            '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            padded_video
        ], capture_output=True)
        video_input = padded_video
        print(f"✅ 延长后视频: {get_duration(padded_video):.1f}s")
    else:
        video_input = args.video
    
    print(f"🎵 Adding audio: {args.audio}")
    print(f"📝 Adding subtitles: {args.ass}")
    
    cmd = [
        FFMPEG, '-y',
        '-i', video_input,
        '-i', args.audio,
        '-vf', vf,
        '-c:v', 'libx264', '-b:v', args.video_bitrate,
        '-preset', 'medium', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', args.audio_bitrate,
        '-map', '0:v:0', '-map', '1:a:0',
        '-t', str(audio_dur + 0.5),  # 确保音频完整，+0.5s 安全余量
        '-movflags', '+faststart',
        args.output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg error:\n{result.stderr[-800:]}", file=sys.stderr)
        sys.exit(1)

    sz = os.path.getsize(args.output)
    dur = get_duration(args.output)
    print(f"✅ Final: {args.output} ({sz/1024/1024:.1f}MB, {dur:.0f}s)")


if __name__ == "__main__":
    main()
