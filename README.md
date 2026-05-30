# 琪琪绘本管线 (Picture Book Pipeline)

> **管线版本**: v1.0
> **技术栈**: Flux schnell T2I + Ken Burns + Edge TTS/Qwen3-TTS + ASS字幕
> **GitHub**: https://github.com/vincentlau2046-sudo/picture-book-pipeline
> **最后更新**: 2026-05-30

---

## 目录结构

```
qiqi-opc/
├── scripts/                    # 管线脚本
│   ├── pipeline.py             # 主管线编排
│   ├── gen_scenes.py           # Flux schnell 批量生成场景图
│   ├── stage_cover.py          # 封面生成
│   ├── stage_kenburns.py       # 场景动画 (Ken Burns / 静态帧)
│   ├── stage_xfade.py          # 片段串联
│   ├── stage_audio_sub.py      # 音频 + 字幕合成
│   ├── tts.py                  # TTS 合成 (Edge TTS)
│   ├── srt_to_ass.py           # SRT → ASS 字幕转换
│   ├── cover_text_overlay.py   # 封面文字叠加
│   └── generate_video.py       # 单集完整生成
│
├── S02E01/                     # 各集工作目录
│   ├── input/                  # 输入: TTS脚本, 场景规划
│   ├── scenes/                 # 场景图 (PNG)
│   ├── output/                 # 最终产出 (MP4)
│   ├── narration_cn.wav        # TTS音频
│   ├── subtitles_cn.ass        # ASS字幕
│   └── scene_prompts.json      # 场景Prompt
│
├── .gitignore                  # 排除大文件
└── README.md                   # 本文件
```

---

## 管线流程

```
┌────────────────────────────────────────────────────────────┐
│                    琪琪绘本管线 v1.0                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [1] 策划 ──→ [2] 资产 ──→ [3] 合成 ──→ [4] 产出          │
│                                                            │
│  剧本/TTS脚本   场景图PNG    Ken Burns     MP4              │
│  scene_prompts  Flux schnell  xfade        + TTS            │
│                 封面          音频字幕      + ASS字幕         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Stage 1: 策划
- 输入: Obsidian 系列大纲
- 输出: `input/tts_script_cn.txt`, `input/tts_script_en.txt`

### Stage 2: 资产生成
- `gen_scenes.py` — Flux schnell 生成场景图 (1920×1080)
- `stage_cover.py` — 封面生成

### Stage 3: 合成
- `stage_kenburns.py` — 静态帧 → 视频片段 (无缩放)
- `stage_xfade.py` — 片段串联 (concat demuxer)
- `tts.py` — TTS 合成 (Edge TTS)

### Stage 4: 最终产出
- `stage_audio_sub.py` — 音频 + ASS字幕合成
- `srt_to_ass.py` — SRT → ASS 格式转换

---

## 使用方式

### 单集完整生成

```bash
cd S03E02
python3 ../scripts/pipeline.py input/tts_script_cn.txt zh
python3 ../scripts/pipeline.py input/tts_script_en.txt en
```

### 手动分步执行

```bash
cd S03E02

# 1. 生成场景图
python3 ../scripts/gen_scenes.py --prompts input/scene_prompts.json --output-dir ./scenes/

# 2. 静态帧 → 视频片段
python3 ../scripts/stage_kenburns.py 1920 1080

# 3. 串联
python3 ../scripts/stage_xfade.py 1.0

# 4. TTS (如果音频不存在)
python3 ../scripts/tts.py input/tts_script_cn.txt zh narration_cn.wav

# 5. SRT → ASS
python3 ../scripts/srt_to_ass.py narration_cn.srt subtitles_cn.ass

# 6. 合成最终视频
python3 ../scripts/stage_audio_sub.py --video video_noaudio.mp4 --audio narration_cn.wav --ass subtitles_cn.ass --output output/S03E02_cn.mp4
```

---

## Obsidian 集成

- Obsidian vault: `~/文档/Obsidian vault/零壹日记本/01-工作/琪琪OPC项目/`
- **Obsidian 是唯一文本资产总成平台**
- 剧本/系列大纲/分镜在 Obsidian 维护
- 代码/脚本在 `~/Videos/qiqi-opc/` 维护
- Git 同步: 代码/配置/文本/脚本

---

## 同步策略

- **入 git**: 脚本, 配置, TTS脚本, SRT/ASS, 分镜
- **不入 git**: 场景图PNG, TTS音频WAV, 最终视频MP4 (本地管理)
