# Dataset Schema (Current + Extension)

## Current mode: file/video pairs
Each record represents one volunteer submission.

```json
{
  "example_id": "uuid",
  "mode": "file_video_pair",
  "project_files": [
    {
      "filename": "scene.blend",
      "stored_path": "uploads/<example_id>/scene.blend",
      "sha256": "...",
      "size_bytes": 12345
    }
  ],
  "video": {
    "filename": "render.mp4",
    "stored_path": "uploads/<example_id>/render.mp4",
    "sha256": "...",
    "size_bytes": 987654
  },
  "volunteer": {
    "display_name": "optional"
  },
  "feedback": [],
  "created_at": "ISO-8601"
}
```

## Later extension: prompt/video pairs
```json
{
  "example_id": "uuid",
  "mode": "prompt_video_pair",
  "prompt": "text prompt here",
  "video": {"...": "..."},
  "feedback": []
}
```

## Feedback entry format
```json
{
  "feedback_id": "uuid",
  "author": "optional",
  "comment": "what is wrong with this example",
  "labels": ["mismatch", "artifact", "wrong_motion"],
  "created_at": "ISO-8601"
}
```
