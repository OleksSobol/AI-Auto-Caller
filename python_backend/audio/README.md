# Audio Files

Drop MP3 files here for music mode in the scambaiter.

Expected filenames:
- `rickroll.mp3`    — Never Gonna Give You Up
- `hold_music.mp3` — Corporate hold music loop
- `custom.mp3`     — Your own custom audio

Any audio file served here will be streamed to the scammer during the call
via the `/audio/<filename>` endpoint.

> **Tip:** Keep files under 10 MB for fast streaming.
> Use a looping MP3 so Twilio's `<Play loop="0">` keeps them on the line indefinitely.
