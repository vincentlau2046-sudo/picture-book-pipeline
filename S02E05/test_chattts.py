#!/usr/bin/env python3
"""
ChatTTS 本地 TTS 测试脚本
生成中文 + 英文语音，保存到 ~/Videos/qiqi-opc/S02E05/
"""
import sys
sys.path.insert(0, '/home/vincent/comfyui-venv/lib/python3.12/site-packages')

import ChatTTS
import torchaudio
import torch
import os

MODEL_DIR = os.path.expanduser('~/.cache/modelscope/hub/pzc163/chatTTS')

print("🔊 Loading ChatTTS model from local path...")
chat = ChatTTS.Chat()
chat.load(source="custom", custom_path=MODEL_DIR, compile=False)

# 设置随机种子确保音色一致
torch.manual_seed(42)

# 测试中文
cn_text = "嗨，小朋友们，我是琪琪。今天故事书里又有一个新故事哦~"
print(f"📝 CN: {cn_text}")
cn_wav = chat.infer(cn_text, skip_refine_text=True)
if cn_wav:
    torchaudio.save('/home/vincent/Videos/qiqi-opc/S02E05/test_cn.wav', cn_wav[0], 24000)
    print(f"✅ CN saved: {cn_wav[0].shape}, duration={cn_wav[0].shape[1]/24000:.2f}s")
else:
    print("❌ CN generation failed")

# 测试英文
en_text = "Hello kids, I'm Qiqi. Today we have a new story from the magic storybook~"
print(f"📝 EN: {en_text}")
en_wav = chat.infer(en_text, skip_refine_text=True)
if en_wav:
    torchaudio.save('/home/vincent/Videos/qiqi-opc/S02E05/test_en.wav', en_wav[0], 24000)
    print(f"✅ EN saved: {en_wav[0].shape}, duration={en_wav[0].shape[1]/24000:.2f}s")
else:
    print("❌ EN generation failed")

print("✅ ChatTTS test complete!")
