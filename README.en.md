# Ascension

**One RTX 4060 Ti. Zero additional video API fees. Four days. Let imagination rise.**

[Watch the film and visual archive](https://art.zzh.app) · [Media downloads](https://github.com/ZetaZeroHub/ascension/releases/tag/v1.0.0) · [中文](README.md)

A visual music concept MV by Zhang Hao, with an open production archive. The author supplied direction and revisions through prompts. AI performed production using a combination of MCP, scripts, APIs and UI control.

“Zero cost” describes additional API spending for locally generated video. Existing hardware, AI subscriptions and electricity are excluded; some storyboard reference images were made using an AI image service. The author reports one day for concept/storyboards, two for generation and one for automated editing. This is a project record, not a universal benchmark.

## Included

- 26 browsable historical pages, including character development, storyboards, grading comparisons and style studies.
- 68 native ComfyUI workflows and 68 API configurations.
- 76 input assets, 61 execution snapshots and nine model records.
- Editable timeline/manifests, original and derived footage, and cut-point review sheets.
- Historical production scripts, portable setup tools and project-specific creative skills.

Large media is distributed through Releases, not Git history. Download all `ascension-media-*.zip` archives and extract them into this repository, preserving their `site/` paths. Model weights are not redistributed.

## Local preview

```sh
git clone https://github.com/ZetaZeroHub/ascension.git
cd ascension
python scripts/fetch_media.py
python -m http.server 8080 --directory site --bind 127.0.0.1
```

Open `http://127.0.0.1:8080`. No frontend build or JavaScript dependencies are required.

## Recorded hardware and settings

RTX 4060 Ti 8GB, 32GB RAM, NVMe storage and Windows. ComfyUI 0.37.4, Python 3.12.9, PyTorch 2.9.1+cu130. This is a tested configuration, not a proven minimum.

H3 FL2VA/REF2VA INT8, Qwen3-VL 32B NVFP4/AWQ, dynamic VRAM, NVMe offloading, disabled pinned memory, 2.5GB VRAM headroom and one shot at a time made generation manageable. See [reproduction instructions](docs/REPRODUCE.md).

V11 style studies used 640×384, 73 frames at 24fps and eight Turbo steps: 2.50–3.58 minutes per clip, median 2.69 minutes. V10 HD shots used 1280×736 and 25 steps, then cropped to 720p; those timings are not interchangeable.

## A story before a pipeline

A courier in red steals a seed of light to awaken a frozen city. Pursuit leads her to a broken bridge, where she chooses to leap. Her decision reverses gravity and restores the city. A short bob, red coat, gold wrist thread and light seed anchor her identity across shots.

The workflow moves from concept and image-based storyboards to local video generation, clip review and music-led editing in Jianying using a community MCP server. It preserves mistakes as well as successful images. See [the process](docs/PROCESS.md), [skills](docs/SKILLS.md) and [editing portability](docs/EDITING.md).

The featured export is approximately 93.762 seconds at 1280×720/24fps. The earlier validated master is 95.083 seconds. Checks attached to that master do not automatically validate later exports. Sanitization changes paths and media metadata, so release hashes supersede historical asset hashes for download verification.

## License

Original code: [MIT](LICENSE). Original creative assets: [CC BY 4.0](LICENSE-ASSETS.md), to the extent of the author's rights. Third-party models, skills, software and trademarks retain their own terms and are not relicensed here. See [attribution](THIRD_PARTY_NOTICES.md).
