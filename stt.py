import whisper

model = whisper.load_model("large-v2")

result = model.transcribe(
    audio="vidssave.com Give me 54 Seconds and I’ll Make you Dangerously Motivated 240P",
    language="hi",
    task="translate"
)

print(result["text"])