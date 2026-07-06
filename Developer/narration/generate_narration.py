import asyncio
import edge_tts
from pathlib import Path

SCRIPT_FILE = Path("Developer/video/audio/scripts/INTRO_NARRATION.txt")
OUTPUT_FILE = Path("Developer/video/audio/generated/INTRO_TAKE01.mp3")

text = SCRIPT_FILE.read_text(encoding="utf-8")

VOICE = "en-US-GuyNeural"

async def main():
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(OUTPUT_FILE))

asyncio.run(main())

print(f"Generated: {OUTPUT_FILE}")