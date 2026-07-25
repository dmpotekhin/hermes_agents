# FFmpeg audio overlay — filter graphs and patterns

## overlay_audio (music + original)

```
Inputs:
  0:v — video stream from concat
  0:a — original audio from clips
  1:a — music file (looped with -stream_loop -1)

Filter complex:
  [1:a]volume=0.25,afade=t=in:d=1.5,afade=t=out:st={dur-2}:d=2[music]
  [0:a]volume=0.8[orig]
  [orig][music]amix=inputs=2:duration=first:dropout_transition=2[audio]

Output:
  -map 0:v (video, copy codec)
  -map [audio] (mixed audio, aac 192k)
  -shortest -t {duration}
```

## normalize_audio (loudnorm)

```
  -af loudnorm=I=-14:TP=-1.0:LRA=11
  -c:v copy
  -c:a aac -b:a 192k
```

Target: -14 LUFS (integrated), -1.0 dBTP (true peak), 11 LU (loudness range).
Matches YouTube/TikTok/Instagram loudness standards.

## overlay_text (drawtext)

```
  -vf drawtext=text='{escaped_text}':
      fontsize=28:
      fontcolor=white:
      box=1:
      boxcolor=black@0.5:
      boxborderw=8:
      x=(w-text_w)/2:
      y=h-th-60:
      line_spacing=6
  -c:v libx264 -preset fast -crf 23
  -c:a copy
```

### Character escaping (order matters!)
1. `\` → `\\\\` (backslash first!)
2. `:` → `\\:`
3. `'` → `\\'`  
4. `%` → `\\\\%`

The Python helper `_escape_drawtext()` applies these in correct order.

### Position presets
- `"bottom"`: `y=h-th-60` (lower third, 60px from bottom)
- `"top"`: `y=40` (40px from top)
- `"center"`: `y=(h-th)/2` (vertical center)

## Volume presets for short-form video

| Name | music_volume | original_volume | Use case |
|------|-------------|-----------------|----------|
| Voice-over | 0.12 | 0.8 | Narration primary, music barely there |
| Balanced | 0.25 | 0.8 | Standard reel/tiktok (default) |
| Music first | 0.45 | 0.8 | Slideshow/montage, no speech |

## Full render pipeline with music + captions

```
For each clip:
  1. trim_video(source, clip_start, clip_duration) → clip_N.mp4
  2. IF captions: overlay_text(clip_N.mp4, caption_text) → clip_N_text.mp4

3. concat_videos([all clips]) → concat_temp.mp4 (or export_path if no music)

4. IF music:
     overlay_audio(concat_temp.mp4, music_path) → with_music.mp4
     normalize_audio(with_music.mp4) → export_path
   ELSE:
     normalize_audio(concat_temp.mp4) → normalized.mp4
     rename → export_path
```
