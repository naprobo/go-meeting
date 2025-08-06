import whisper
import tempfile

# 初始化模型（可设为 global 复用）
model = whisper.load_model("base")  # 可改为 "small" / "medium" / "large" 看需求

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    # 将音频写入临时文件
    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{filename.split('.')[-1]}") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()

        # Whisper 会自动处理格式、解码
        result = model.transcribe(tmp.name, language="ja")
        return result.get("text", "")
