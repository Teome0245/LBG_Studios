#!/usr/bin/env python3
"""
tools/build_clip_khor_un_val_kyra.py
Génère le clip musical complet 60s (1080x1920) pour Khor-un Val-Kyra / Nexura Diva.
Synchronisé avec la bande son khor_un_val_kyra.mp3.
"""
import os
import subprocess
import shutil

BRAIN_DIR = "/home/lbg/.gemini/antigravity/brain/7f9bb620-d304-4077-9c8d-5e9eefd16a6b"
AUDIO_PATH = os.path.join(BRAIN_DIR, "khor_un_val_kyra.mp3")
OUT_CLIP = os.path.join(BRAIN_DIR, "clip_khor_un_val_kyra_60s.mp4")
TMP_DIR = "/tmp/clip_assembly"

os.makedirs(TMP_DIR, exist_ok=True)

# Sources
kling_vid = os.path.join(BRAIN_DIR, "kling_singing_raw.mp4")
img_live = os.path.join(BRAIN_DIR, "cyber_singer_live_concert_1794436231531.jpg")
img_closeup = os.path.join(BRAIN_DIR, "cyber_singer_epic_closeup_1794436460892.jpg")
img_drop1 = os.path.join(BRAIN_DIR, "cyber_singer_dynamic_drop_action_1794436481438.jpg")
img_eyes = os.path.join(BRAIN_DIR, "cyber_singer_live_concert_glowing_eyes_1794436251128.jpg")
img_drop2 = os.path.join(BRAIN_DIR, "cyber_singer_drop_action_shot_1794436441286.jpg")

print("[1/8] Rendu Plan 1 : Kling AI Singing Close-up (0.0 - 5.0s)...")
s1_out = os.path.join(TMP_DIR, "seg1.mp4")
cmd1 = [
    "ffmpeg", "-y", "-ss", "0", "-t", "5.0", "-i", kling_vid,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s1_out
]
subprocess.run(cmd1, check=True)

print("[2/8] Rendu Plan 2 : Scène Live Concert Zoom In (5.0 - 12.5s = 7.5s)...")
s2_out = os.path.join(TMP_DIR, "seg2.mp4")
cmd2 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "7.5", "-i", img_live,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0008,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s2_out
]
subprocess.run(cmd2, check=True)

print("[3/8] Rendu Plan 3 : Couplet Diva Micro Pan Up (12.5 - 22.0s = 9.5s)...")
s3_out = os.path.join(TMP_DIR, "seg3.mp4")
cmd3 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "9.5", "-i", img_closeup,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0007,1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+0.3*on':s=1080x1920:fps=30,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s3_out
]
subprocess.run(cmd3, check=True)

print("[4/8] Rendu Plan 4 : Premier Drop Dynamique (22.0 - 34.0s = 12.0s)...")
s4_out = os.path.join(TMP_DIR, "seg4.mp4")
cmd4 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "12.0", "-i", img_drop1,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0010,1.20)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s4_out
]
subprocess.run(cmd4, check=True)

print("[5/8] Rendu Plan 5 : Ambiance Électro & Glowing Eyes (34.0 - 45.0s = 11.0s)...")
s5_out = os.path.join(TMP_DIR, "seg5.mp4")
cmd5 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "11.0", "-i", img_eyes,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0006,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-0.2*on':s=1080x1920:fps=30,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s5_out
]
subprocess.run(cmd5, check=True)

print("[6/8] Rendu Plan 6 : Second Drop & Climax Performance (45.0 - 55.0s = 10.0s)...")
s6_out = os.path.join(TMP_DIR, "seg6.mp4")
cmd6 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "10.0", "-i", img_drop2,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0009,1.18)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s6_out
]
subprocess.run(cmd6, check=True)

print("[7/8] Rendu Plan 7 : Outro Triomphale & Fade to Black (55.0 - 60.0s = 5.0s)...")
s7_out = os.path.join(TMP_DIR, "seg7.mp4")
cmd7 = [
    "ffmpeg", "-y", "-loop", "1", "-t", "5.0", "-i", img_closeup,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='max(1.15-0.001*on,1.0)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,fade=t=out:st=3.8:d=1.2,setsar=1",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", s7_out
]
subprocess.run(cmd7, check=True)

# Concaténation des 7 plans
print("[8/8] Assemblage et mixage avec la bande son Khor-un Val-Kyra...")
concat_list = os.path.join(TMP_DIR, "concat.txt")
with open(concat_list, "w") as f:
    for seg in [s1_out, s2_out, s3_out, s4_out, s5_out, s6_out, s7_out]:
        f.write(f"file '{seg}'\n")

raw_video = os.path.join(TMP_DIR, "video_60s_raw.mp4")
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
    "-c", "copy", raw_video
], check=True)

# Muxing audio avec fondu audio final à 58.5s
subprocess.run([
    "ffmpeg", "-y", "-i", raw_video, "-ss", "0", "-t", "60.0", "-i", AUDIO_PATH,
    "-af", "afade=t=out:st=58.5:d=1.5",
    "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
    OUT_CLIP
], check=True)

sz_mb = round(os.path.getsize(OUT_CLIP) / (1024 * 1024), 2)
print(f"[✔] Clip musical 60s généré avec succès : {OUT_CLIP} ({sz_mb} Mo)")
shutil.rmtree(TMP_DIR, ignore_errors=True)
