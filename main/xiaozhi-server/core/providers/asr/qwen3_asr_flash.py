import asyncio
import os
from typing import List, Optional, Tuple

import dashscope

from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType

tag = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        # 音频文件上传类型，流式文本识别输出
        self.interface_type = InterfaceType.NON_STREAM
        """Qwen3-ASR-Flash ASR初始化"""
        
        # 配置参数
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Qwen3-ASR-Flash 需要配置 api_key")
            
        self.model_name = config.get("model_name", "qwen3-asr-flash")
        self.output_dir = config.get("output_dir", "./audio_output")
        self.delete_audio_file = delete_audio_file
        self.request_timeout = float(config.get("request_timeout", 20))
        if self.request_timeout <= 0:
            raise ValueError("Qwen3-ASR-Flash request_timeout 必须大于 0")
        
        # ASR选项配置
        self.enable_lid = config.get("enable_lid", True)  # 自动语种检测
        self.enable_itn = config.get("enable_itn", True)  # 逆文本归一化
        self.language = config.get("language", None)  # 指定语种，默认自动检测
        self.context = config.get("context", "")  # 上下文信息，用于提高识别准确率
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def prefers_temp_file(self) -> bool:
        return True

    def requires_file(self) -> bool:
        return True

    def _transcribe_file(self, temp_file_path: str) -> str:
        """Run the synchronous DashScope request outside the event loop."""
        messages = [
            {
                "role": "user",
                "content": [{"audio": temp_file_path}],
            }
        ]

        if self.context:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": [{"text": self.context}],
                },
            )

        asr_options = {
            "enable_lid": self.enable_lid,
            "enable_itn": self.enable_itn,
        }
        if self.language:
            asr_options["language"] = self.language

        response = dashscope.MultiModalConversation.call(
            model=self.model_name,
            messages=messages,
            result_format="message",
            asr_options=asr_options,
            stream=True,
            api_key=self.api_key,
            request_timeout=self.request_timeout,
        )

        full_text = ""
        for chunk in response:
            try:
                text = chunk["output"]["choices"][0]["message"].content[0]["text"]
                full_text = text.strip()
            except (AttributeError, IndexError, KeyError, TypeError):
                continue
        return full_text

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, artifacts=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """将语音数据转换为文本"""
        file_path = None
        try:
            if artifacts is None:
                return "", None
            temp_file_path = artifacts.temp_path
            file_path = artifacts.file_path
            if not temp_file_path:
                return "", file_path

            full_text = await asyncio.wait_for(
                asyncio.to_thread(self._transcribe_file, temp_file_path),
                timeout=self.request_timeout,
            )
            return full_text, file_path

        except asyncio.TimeoutError:
            logger.bind(tag=tag).error("语音识别超时")
            return "", file_path
        except Exception as exc:
            logger.bind(tag=tag).error(f"语音识别失败: {type(exc).__name__}")
            return "", file_path
