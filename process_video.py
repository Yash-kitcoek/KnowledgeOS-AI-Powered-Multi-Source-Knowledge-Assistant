import os
import subprocess

os.makedirs("audios", exist_ok=True)

for file in os.listdir("videos"):
    input_path = os.path.join("videos", file)

    # Skip non-video files
    if not file.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
        continue

    # Output filename (same name, .mp3)
    output_name = os.path.splitext(file)[0] + ".mp3"
    output_path = os.path.join("audios", output_name)

    print(f"Converting: {file}")

    subprocess.run([
        "ffmpeg",
        "-i", input_path,
        "-vn",                  # Ignore video
        "-acodec", "libmp3lame",
        "-q:a", "2",            # High-quality MP3
        output_path
    ])

print("All videos converted successfully!")