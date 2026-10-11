# 在自己的电脑上复现

## 1. 安装与下载

安装 [ComfyUI](https://comfy.org/download) 和 [FFmpeg](https://ffmpeg.org/download.html)。按 [H3 原生工作流文档](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native) 下载模型，并核对本仓库 [模型清单](../site/archive/ComfyUI留存-v11/模型清单.json)。不必为历史超分对照安装 4x-UltraSharp。

| 目录（相对 ComfyUI 的 models） | 文件 |
|---|---|
| diffusion_models | minimax_h3_fl2va_pruned_int8_convrot.safetensors |
| diffusion_models | minimax_h3_ref2va_pruned_int8_convrot.safetensors |
| text_encoders | qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors |
| vae | minimax_h3_video_vae_int8_convrot.safetensors |
| vae | minimax_h3_audio_vae_fp32.safetensors |
| loras | minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors |
| loras/FeishengStyleV11 | h3-realism-people-t2v-i2v-r2v.safetensors |
| loras/FeishengStyleV11 | minimax_h3_looping_sketch_anime_v1.safetensors |

两个风格 LoRA 的来源、固定 revision、完整 SHA256 在清单中。部分已有大权重没有完整哈希，不把头部校验说成整文件校验。安装新版 ComfyUI 时，先与工作流节点参数对照。

## 2. 准备参考图和工作流

在仓库根目录运行：

```sh
python scripts/fetch_media.py --inputs
python scripts/prepare_comfy.py --comfy-root /path/to/ComfyUI --dry-run
python scripts/prepare_comfy.py --comfy-root /path/to/ComfyUI
```

Windows 示例：`--comfy-root "D:/ComfyUI"`。可选包提供 75 张原始输入图。历史运动参考视频 `05-motion.mp4` 不随包分发；依赖它的工作流需换成自己的运动参考视频。脚本只复制输入图和工作流；遇到不同内容的同名文件会停止，不覆盖。不会启动 ComfyUI、修改显卡设置、下载大模型或提交队列。

在 ComfyUI 中打开 `user/default/workflows/Ascension/风格-v11/16-C.json`，或把相应原生 JSON 拖入画布。使用 `API/` 下的 JSON 时需通过 ComfyUI API 提交，不是同一种文件格式。

## 3. 先运行一个试片

先核对模型下拉框、输入图和输出目录，再点击 ComfyUI 的运行按钮。使用单任务队列，先测试 v11 的 8 步风格试片，再考虑 v10 的 25 步高清镜头。网站上的 720p 试片可能由较低原生分辨率裁切缩放得到，不等同于原生 720p。

当时的显存参数如下；仅在当前安装版本支持对应参数时使用：

```text
--enable-dynamic-vram --fast-disk --disable-pinned-memory
--vram-headroom 2.5 --cache-ram 6 8 --preview-method none
```

不要同时启动多个模型进程争抢 8GB 显存。任务完成后检查人物、道具、手部、运动方向与背景变化。历史执行成功只能说明模型完成了计算，不能证明每一帧都可用。

## 4. 进度与记录

网页队列显示当前采样进度；`history/` 保存历史运行快照。68 份原生工作流中，67 份使用留存后端支持的节点，早期 Image Studio 的一份历史工作流需另行解决自定义节点兼容性。它没有作为“开箱即用”示例。

`production-scripts/` 是脱敏历史代码：原绝对路径已替换为占位符，保留实现供阅读，不可直接宣称在新机器上无修改运行。推荐先用原生 ComfyUI 画布跑通单镜头，再适配历史批处理脚本。
