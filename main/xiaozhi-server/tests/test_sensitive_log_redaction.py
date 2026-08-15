import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SensitiveLogRedactionTest(unittest.TestCase):
    def test_binding_code_is_not_interpolated_into_error_log(self):
        source = (ROOT / "core/handle/receiveAudioHandle.py").read_text()
        self.assertIn('error("无效的绑定码格式")', source)
        self.assertNotIn('error(f"无效的绑定码格式:', source)

    def test_binding_code_is_not_embedded_in_exception_text(self):
        source = (ROOT / "config/manage_api_client.py").read_text()
        self.assertIn('super().__init__("设备需要绑定")', source)
        self.assertNotIn('super().__init__(f"设备绑定异常，绑定码:', source)

    def test_ota_request_headers_and_body_are_not_logged(self):
        source = (ROOT / "core/api/ota_handler.py").read_text()
        self.assertNotIn("OTA请求头:", source)
        self.assertNotIn("OTA请求数据:", source)

    def test_websocket_and_provider_headers_are_not_logged(self):
        connection = (ROOT / "core/connection.py").read_text()
        doubao = (ROOT / "core/providers/asr/doubao_stream.py").read_text()
        self.assertNotIn("conn - Headers:", connection)
        self.assertNotIn("headers: {headers}", doubao)
        self.assertNotIn("发送初始化请求: {request_params}", doubao)
        self.assertNotIn("构造请求参数:", doubao)
        self.assertNotIn("建立ASR连接失败: {str(e)}", doubao)
        self.assertNotIn("错误原因: {str(e.__cause__)}", doubao)
        self.assertNotIn("原始响应数据:", doubao)

    def test_device_identifiers_are_not_interpolated_into_operational_logs(self):
        prompt_manager = (ROOT / "core/utils/prompt_manager.py").read_text()
        report_handler = (ROOT / "core/handle/reportHandle.py").read_text()
        self.assertNotIn("设备 {device_id}", prompt_manager)
        self.assertNotIn("{conn.device_id}", report_handler)


if __name__ == "__main__":
    unittest.main()
