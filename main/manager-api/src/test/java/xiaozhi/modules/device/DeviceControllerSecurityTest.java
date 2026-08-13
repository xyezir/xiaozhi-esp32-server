package xiaozhi.modules.device;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.springframework.context.support.StaticMessageSource;
import org.springframework.test.util.ReflectionTestUtils;

import xiaozhi.common.utils.MessageUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.device.controller.DeviceController;
import xiaozhi.modules.device.controller.OTAController;
import xiaozhi.modules.device.dto.DeviceRegisterDTO;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.sys.service.SysParamsService;

class DeviceControllerSecurityTest {

    @Test
    void registrationReservesCodeAtomicallyForTenMinutes() {
        RedisUtils redisUtils = mock(RedisUtils.class);
        when(redisUtils.setIfAbsent(anyString(), eq("00:11:22:33:44:55"), eq(600L)))
                .thenReturn(false, true);
        DeviceController controller = new DeviceController(mock(DeviceService.class), redisUtils);
        DeviceRegisterDTO request = new DeviceRegisterDTO();
        request.setMacAddress("00:11:22:33:44:55");

        Result<String> result = controller.registerDevice(request);

        assertEquals(0, result.getCode());
        assertTrue(result.getData().matches("\\d{6}"));
        verify(redisUtils, times(2))
                .setIfAbsent(anyString(), eq("00:11:22:33:44:55"), eq(600L));
    }

    @Test
    void registrationFailsClosedAfterRepeatedCodeCollisions() {
        StaticMessageSource messages = new StaticMessageSource();
        messages.addMessage(
                String.valueOf(xiaozhi.common.exception.ErrorCode.REDIS_ERROR),
                java.util.Locale.ENGLISH,
                "redis error");
        ReflectionTestUtils.setField(MessageUtils.class, "messageSource", messages);
        RedisUtils redisUtils = mock(RedisUtils.class);
        when(redisUtils.setIfAbsent(anyString(), eq("00:11:22:33:44:55"), eq(600L)))
                .thenReturn(false);
        DeviceController controller = new DeviceController(mock(DeviceService.class), redisUtils);
        DeviceRegisterDTO request = new DeviceRegisterDTO();
        request.setMacAddress("00:11:22:33:44:55");

        Result<String> result = controller.registerDevice(request);

        assertEquals(xiaozhi.common.exception.ErrorCode.REDIS_ERROR, result.getCode());
        verify(redisUtils, times(20))
                .setIfAbsent(anyString(), eq("00:11:22:33:44:55"), eq(600L));
    }

    @Test
    void otaHealthAcceptsWebsocketOnlyTransport() {
        SysParamsService params = mock(SysParamsService.class);
        when(params.getValue(Constant.SERVER_MQTT_GATEWAY, false)).thenReturn("");
        when(params.getValue(Constant.SERVER_WEBSOCKET, true)).thenReturn("ws://manager.example/xiaozhi/v1/");
        when(params.getValue(Constant.SERVER_OTA, true)).thenReturn("http://manager.example/xiaozhi/ota/");
        OTAController controller = new OTAController(mock(DeviceService.class), params);

        String body = controller.getOTA().getBody();

        assertTrue(body != null && body.contains("OTA接口运行正常"));
        assertTrue(body.contains("mqtt_gateway：未配置"));
    }
}
