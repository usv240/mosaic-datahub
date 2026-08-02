# Submission video

`mosaic-submission-demo.mp4` is the final narrated submission artifact. It uses eleven synchronized 16:9 scenes captured from the tested application: hero, lineage, four-case scorecard, cross-asset proof, measured result, agent boundary, attack refusal, generated PR, DataHub stack, external evidence, and production readiness.

- Duration: 169.88 seconds
- Video: H.264, 1280x720, 24 fps
- Audio: AAC, mono
- Size: 5,641,215 bytes
- SHA-256: `099920ad27f464237ada92194294bc63401f90510fc1a18f8963371e4c2e34d0`

`narration.txt` is the exact voice-over. `08-product-walkthrough.webm` remains the interactive source footage, and `media-manifest.json` contains hashes for all current captures. Rebuild reproducibly with `uv run --with imageio-ffmpeg python scripts/build_submission_video.py` after running the media-capture script.

The MP4 is upload-ready. The hackathon still requires a public YouTube or Vimeo URL; that external receipt must not be marked complete until an authenticated upload succeeds.
