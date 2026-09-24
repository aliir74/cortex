# elevenlabs-voice preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/elevenlabs-voice.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty uses the default listed in the skill's preferences table.

## voice_id
<!-- TTS voice id from /v1/voices or the Voice Library. -->
voice_id:

## tts_model
<!-- e.g. eleven_v3, eleven_multilingual_v2, eleven_flash_v2_5 -->
tts_model:

## output_format
<!-- e.g. opus_48000_64, mp3_44100_128, pcm_16000 -->
output_format:

## speed
<!-- 0.7 to 1.2 -->
speed:

## stability
<!-- 0.0 to 1.0 -->
stability:

## stt_model
<!-- scribe_v2 or scribe_v1 -->
stt_model:

## api_key_file
<!-- Path to a chmod 600 file holding only the API key. Ignored when $ELEVENLABS_API_KEY is set. -->
api_key_file:
