# 模型与鉴权基线

最后核验：2026-08-15

本页记录当前代码已经兼容、且由供应商官方文档确认存在的模型与鉴权参数。稳定别名优先于日期快照；仓库升级不会自动替换已有智能体的模型或发起计费调用。

| 能力 | 推荐配置 | 兼容性与边界 | 官方依据 |
| --- | --- | --- | --- |
| ASR | `qwen3-asr-flash` | 当前同步调用适配器支持的稳定别名；单文件不超过 10 MB / 5 分钟。需要真正实时识别时应另接 `qwen3-asr-flash-realtime` WebSocket 适配器 | [Qwen ASR 模型列表](https://help.aliyun.com/zh/model-studio/asr-model/) |
| LLM（低延迟） | `qwen3.5-flash` | 兼容当前 OpenAI Chat Completions 适配器，支持工具调用；`qwen3.6-flash` 的部分版本仅支持 Responses API，不作为本适配器默认值 | [千问模型列表](https://help.aliyun.com/zh/model-studio/models) |
| LLM（DeepSeek） | `deepseek-v4-flash` | Base URL 为 `https://api.deepseek.com`；旧别名 `deepseek-chat`、`deepseek-reasoner` 已于 2026-07-24 进入弃用节点 | [DeepSeek API 更新](https://api-docs.deepseek.com/updates/) |
| VLLM | `qwen3.5-flash` | 支持文本、图片和视频输入，兼容当前 OpenAI 风格视觉调用 | [Qwen 视觉模型](https://help.aliyun.com/zh/model-studio/vision-model/) |
| TTS（推荐） | `seed-tts-2.0` | WebSocket 为 `wss://openspeech.bytedance.com/api/v3/tts/bidirection`；当前豆包语音控制台使用 `api_key`，服务端发送 `X-Api-Key` | [豆包语音双向流式 API](https://www.volcengine.com/docs/6561/1329505) |
| TTS（旧版兼容） | `volc.service_type.10029` | 旧控制台使用 `appid` + `access_token`，服务端发送 `X-Api-App-Key` + `X-Api-Access-Key`；保留用于现有 Moon/BigTTS 音色 | [豆包语音控制台 FAQ](https://www.volcengine.com/docs/6561/196768) |

## 火山鉴权必须区分

- `火山方舟 API Key` 用于方舟 LLM/VLM 接口。
- `豆包语音 API Key` 来自新版豆包语音控制台，用于 OpenSpeech 语音接口。
- 旧版豆包语音应用才提供 `AppID` 与 `Access Token`。
- 管理端配置了 `api_key` 时优先使用新版鉴权；否则仅在 `appid` 和 `access_token` 都有效时使用旧版鉴权。占位值或缺失值会在发起网络连接前失败。

## 当前未自动启用

- `qwen3-asr-flash-realtime` 需要新的实时 WebSocket ASR 适配器，不能用现有同步 Qwen ASR 适配器冒充。
- `qwen3-tts-instruct-flash-realtime` 需要对应的 Qwen TTS 协议适配器；现有阿里流式 TTS 仍按其已实现协议工作。
- 模型升级可能改变价格、额度、区域和输出行为；管理员必须在对应供应商控制台开通后，按单设备灰度验证。
