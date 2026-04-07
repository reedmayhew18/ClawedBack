---
name: oc-voice
description: "Handle voice message processing. Use internally when the router encounters a voice-type message. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Bash(python*)"
---

# Voice Coordinator

Handles voice messages received through the web chat. By the time you see them, the audio has already been transcribed by Whisper.

## How Voice Messages Arrive

The web UI records audio → uploads to `/api/voice` → Python server transcribes with `whisper --model turbo` → queues the transcribed text as type `voice`.

The message in the queue looks like:
```json
{
  "type": "voice",
  "content": "hey can you check if the tests pass",
  "metadata": "{\"audio_file\": \"voice_abc123.webm\", \"language\": \"en\"}"
}
```

## Processing

1. The transcribed text in `content` IS the user's message — process it like any text message
2. If the transcription looks like garbage (random characters, empty, very short single words), respond asking the user to repeat or type it instead
3. Note in your response that this came from a voice message if relevant (e.g., "I heard: '...' — is that right?") — but only if the transcription seems uncertain

## Quality Signals

Good transcription:
- Complete sentences or clear phrases
- Makes sense in context
- Language field matches expected language

Bad transcription (ask user to repeat):
- Content is empty or just punctuation
- Random unrelated words
- Very short (1-2 characters) unless it's a clear command like "yes" or "no"

## Audio File Location

The original audio is saved at `data/uploads/<audio_file>` if you need to reference it. You cannot re-transcribe it, but you can note its existence.
