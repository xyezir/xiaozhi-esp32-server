import asyncio
import base64
import os
import uuid
from typing import List, Optional, Tuple

import requests

from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType


TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    """Volcengine large-model flash file transcription using the new API Key."""

    API_URL = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"
    RESOURCE_ID = "volc.bigasr.auc_turbo"
    SUCCESS_CODE = "20000000"
    MAX_AUDIO_BYTES = 20 * 1024 * 1024

    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.NON_STREAM

        self.api_key = str(config.get("api_key") or "").strip()
        if not self.api_key:
            raise ValueError("豆包极速语音识别需要配置 api_key")

        self.resource_id = str(
            config.get("resource_id") or self.RESOURCE_ID
        ).strip()
        if self.resource_id != self.RESOURCE_ID:
            raise ValueError(f"豆包极速语音识别 resource_id 必须为 {self.RESOURCE_ID}")

        self.request_timeout = float(config.get("request_timeout", 20))
        if self.request_timeout <= 0:
            raise ValueError("豆包极速语音识别 request_timeout 必须大于 0")

        self.enable_itn = self._as_bool(config.get("enable_itn", True))
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in {"false", "0", "no", "off"}
        return bool(value)

    def prefers_temp_file(self) -> bool:
        return True

    def requires_file(self) -> bool:
        return True

    @staticmethod
    def _extract_text(payload: dict) -> str:
        result = payload.get("result")
        if isinstance(result, dict):
            text = result.get("text")
            if isinstance(text, str):
                return text.strip()
        text = payload.get("text")
        return text.strip() if isinstance(text, str) else ""

    def _transcribe_file(self, temp_file_path: str) -> str:
        audio_size = os.path.getsize(temp_file_path)
        if audio_size <= 0:
            return ""
        if audio_size > self.MAX_AUDIO_BYTES:
            raise ValueError("audio file exceeds the 20 MiB safety limit")

        with open(temp_file_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode("ascii")

        headers = {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "X-Api-Sequence": "-1",
            "Content-Type": "application/json",
        }
        body = {
            "user": {"uid": "xiaozhi-server"},
            "audio": {"data": audio_data, "format": "wav"},
            "request": {
                "model_name": "bigmodel",
                "enable_itn": self.enable_itn,
            },
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=body,
            timeout=self.request_timeout,
        )
        response.raise_for_status()

        provider_code = str(response.headers.get("X-Api-Status-Code", ""))
        if provider_code != self.SUCCESS_CODE:
            raise RuntimeError(
                f"Volcengine ASR rejected request with provider code {provider_code or 'missing'}"
            )

        text = self._extract_text(response.json())
        if not text:
            raise RuntimeError("Volcengine ASR returned an empty transcript")
        return text

    async def speech_to_text(
        self,
        opus_data: List[bytes],
        session_id: str,
        artifacts: Optional[ASRProviderBase.AudioArtifacts] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        file_path = artifacts.file_path if artifacts else None
        if artifacts is None or not artifacts.temp_path:
            return "", file_path

        try:
            text = await asyncio.wait_for(
                asyncio.to_thread(self._transcribe_file, artifacts.temp_path),
                timeout=self.request_timeout + 1,
            )
            return text, file_path
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).error("豆包极速语音识别超时")
        except Exception as exc:
            # Provider responses and request headers may contain credentials.
            logger.bind(tag=TAG).error(
                f"豆包极速语音识别失败: {type(exc).__name__}"
            )
        return "", file_path
