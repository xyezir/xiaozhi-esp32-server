package xiaozhi.modules.device;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.context.support.StaticMessageSource;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.HashMap;
import java.util.Map;

import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.utils.MessageUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.device.dao.DeviceDao;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.entity.OtaEntity;
import xiaozhi.modules.device.service.OtaService;
import xiaozhi.modules.device.service.impl.DeviceServiceImpl;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.service.SysUserUtilService;

class DeviceServiceSecurityTest {
    private DeviceDao deviceDao;
    private RedisUtils redisUtils;
    private AgentDao agentDao;
    private SysParamsService sysParamsService;
    private OtaService otaService;
    private DeviceServiceImpl service;

    @BeforeEach
    void setUp() {
        deviceDao = mock(DeviceDao.class);
        redisUtils = mock(RedisUtils.class);
        agentDao = mock(AgentDao.class);
        sysParamsService = mock(SysParamsService.class);
        otaService = mock(OtaService.class);
        service = new DeviceServiceImpl(
                deviceDao,
                mock(SysUserUtilService.class),
                sysParamsService,
                redisUtils,
                otaService,
                agentDao);
        ReflectionTestUtils.setField(service, "baseDao", deviceDao);
        StaticMessageSource messages = new StaticMessageSource();
        messages.addMessage(String.valueOf(ErrorCode.NO_PERMISSION), java.util.Locale.ENGLISH, "forbidden");
        ReflectionTestUtils.setField(MessageUtils.class, "messageSource", messages);
    }

    @Test
    void activationRejectsAgentOwnedByAnotherUserBeforeReadingCode() {
        AgentEntity agent = new AgentEntity();
        agent.setId("agent-1");
        agent.setUserId(99L);
        when(agentDao.selectById("agent-1")).thenReturn(agent);

        RenException error = assertThrows(
                RenException.class,
                () -> service.deviceActivation(7L, "agent-1", "123456"));

        assertEquals(ErrorCode.NO_PERMISSION, error.getCode());
        verify(redisUtils, never()).get(anyString());
    }

    @Test
    void manualAddRejectsAgentOwnedByAnotherUserBeforeWritingDevice() {
        AgentEntity agent = new AgentEntity();
        agent.setId("agent-1");
        agent.setUserId(99L);
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        DeviceManualAddDTO dto = new DeviceManualAddDTO();
        dto.setAgentId("agent-1");
        dto.setMacAddress("00:11:22:33:44:55");

        RenException error = assertThrows(
                RenException.class,
                () -> service.manualAddDevice(7L, dto));

        assertEquals(ErrorCode.NO_PERMISSION, error.getCode());
        verify(deviceDao, never()).insert(any(DeviceEntity.class));
    }

    @Test
    void manualAddAllowsAgentOwnedByCurrentUser() {
        AgentEntity agent = new AgentEntity();
        agent.setId("agent-1");
        agent.setUserId(7L);
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        when(deviceDao.selectOne(any())).thenReturn(null);
        when(deviceDao.insert(any(DeviceEntity.class))).thenReturn(1);
        DeviceManualAddDTO dto = new DeviceManualAddDTO();
        dto.setAgentId("agent-1");
        dto.setMacAddress("00:11:22:33:44:55");

        service.manualAddDevice(7L, dto);

        verify(deviceDao).insert(any(DeviceEntity.class));
    }

    @Test
    void activationAllowsOwnedAgentAndConsumesTheReservedCode() {
        String deviceId = "00:11:22:33:44:55";
        String activationCode = "123456";
        String codeKey = RedisKeys.getOtaActivationCode(activationCode);
        String dataKey = RedisKeys.getOtaDeviceActivationInfo("00_11_22_33_44_55");
        AgentEntity agent = new AgentEntity();
        agent.setId("agent-1");
        agent.setUserId(7L);
        Map<String, Object> activationData = new HashMap<>();
        activationData.put("activation_code", activationCode);
        activationData.put("board", "esp32-s3");
        activationData.put("app_version", "1.0.0");
        activationData.put("mac_address", deviceId);

        when(agentDao.selectById("agent-1")).thenReturn(agent);
        when(redisUtils.setIfAbsent(eq(codeKey + ":consume"), anyString(), eq(30L))).thenReturn(true);
        when(redisUtils.get(codeKey)).thenReturn(deviceId);
        when(redisUtils.get(dataKey)).thenReturn(activationData);
        when(deviceDao.selectById(deviceId)).thenReturn(null);
        when(deviceDao.insert(any(DeviceEntity.class))).thenReturn(1);

        assertEquals(true, service.deviceActivation(7L, "agent-1", activationCode));

        verify(deviceDao).insert(any(DeviceEntity.class));
        verify(redisUtils).compareAndDelete(eq(codeKey + ":consume"), anyString());
    }

    @Test
    void activationGenerationUsesAtomicReservationAndTenMinuteTtl() {
        String deviceId = "00:11:22:33:44:55";
        when(redisUtils.get(anyString())).thenReturn(null);
        when(redisUtils.setIfAbsent(anyString(), eq(deviceId), eq(600L))).thenReturn(true);
        when(sysParamsService.getValue(anyString(), eq(true))).thenReturn("http://manager.example");

        var activation = service.buildActivation(deviceId, null);

        assertEquals(6, activation.getCode().length());
        assertEquals(deviceId, activation.getChallenge());
        verify(redisUtils).setIfAbsent(anyString(), eq(deviceId), eq(600L));
        verify(redisUtils).set(anyString(), any(Map.class), eq(600L));
    }

    @Test
    void firmwareDownloadFailsClosedWhenTrustedOtaUrlIsMissing() {
        OtaEntity ota = new OtaEntity();
        ota.setId("ota-1");
        ota.setVersion("2.2.5");
        when(otaService.getLatestOta("esp32-s3-touch-amoled-1.75c")).thenReturn(ota);
        DeviceReportRespDTO.Firmware firmware = ReflectionTestUtils.invokeMethod(
                service,
                "buildFirmwareInfo",
                "esp32-s3-touch-amoled-1.75c",
                "2.2.4");

        assertEquals("2.2.4", firmware.getVersion());
        assertEquals("http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL",
                firmware.getUrl());
        verifyNoInteractions(redisUtils);
    }
}
