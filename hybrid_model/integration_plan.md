# Integration Plan: VerseCrafter + WAN + Sora-2-Clone

## Goal
Stand up a single trainable stack that can learn from `(project files, final video)` pairs.

## Order of integration
1. Load VerseCrafter as base temporal generator/backbone.
2. Attach latest WAN components in replace-or-augment mode for conditioning/diffusion blocks.
3. Attach Sora-2-clone branch as auxiliary temporal/alignment module.
4. Fuse via gated routing and shared file-condition encoder.

## Training contract
- Input batch:
  - raw file payloads (text and bytes as available)
  - file metadata (small and optional)
  - target final video
- Output:
  - predicted video
- Optimization:
  - reconstruction + temporal consistency as primary losses

## Practical notes
- Keep ingestion paired-only right now.
- Do not block on generation features.
- Keep module wrappers isolated so each upstream component can be upgraded independently.
