package xiaozhi.modules.device.service.impl;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.sys.service.SysParamsService;

class DeviceRolePackageTest {
    private AgentDao agentDao;
    private SysParamsService sysParamsService;
    private DeviceServiceImpl service;
    private DeviceEntity device;

    @BeforeEach
    void setUp() {
        agentDao = mock(AgentDao.class);
        sysParamsService = mock(SysParamsService.class);
        service = new DeviceServiceImpl(
                null, null, sysParamsService, null, null, null, agentDao);
        device = new DeviceEntity();
        device.setAgentId("agent-1");
    }

    @Test
    void completePublicRolePackageIsReturned() {
        when(agentDao.selectById("agent-1")).thenReturn(validRoleAgent());

        DeviceReportRespDTO.Role role = ReflectionTestUtils.invokeMethod(
                service, "buildRolePackage", device);

        assertNotNull(role);
        assertEquals("cheese_cat", role.getId());
        assertEquals("2026.08.16.1", role.getVersion());
        assertEquals(3_456_789L, role.getSize());
        assertEquals("你好小智", role.getWakeWord());
        assertEquals("wn9_nihaoxiaozhi_tts", role.getWakeModel());
        assertEquals("trained", role.getWakeMode());
        assertEquals(1L, role.getWakeConfigVersion());
    }

    @Test
    void invalidIdentityIntegrityUrlOrDistributionFailsClosed() {
        AgentEntity agent = validRoleAgent();
        when(agentDao.selectById("agent-1")).thenReturn(agent);

        agent.setRoleAssetSha256("invalid");
        assertNull(buildRolePackage());

        agent = validRoleAgent();
        agent.setRoleCode("Cheese Cat");
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());

        agent = validRoleAgent();
        agent.setRoleAssetVersion("2026.08.16.1\r\nX-Injected: true");
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());

        agent = validRoleAgent();
        agent.setRoleAssetUrl("https://user:secret@assets.example/cheese.bin");
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());

        agent = validRoleAgent();
        agent.setRoleDistribution("unknown");
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());
    }

    @Test
    void internalRoleRequiresExplicitServerOptIn() {
        AgentEntity agent = validRoleAgent();
        agent.setRoleDistribution("internal-only");
        when(agentDao.selectById("agent-1")).thenReturn(agent);

        assertNull(buildRolePackage());

        when(sysParamsService.getValue("role.internal.enabled", true)).thenReturn("true");
        assertNotNull(buildRolePackage());
    }

    @Test
    void halfConfiguredWakeProfileFailsClosed() {
        AgentEntity agent = validRoleAgent();
        agent.setRoleWakeModel(null);
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());

        agent = validRoleAgent();
        agent.setRoleWakeWord(null);
        when(agentDao.selectById("agent-1")).thenReturn(agent);
        assertNull(buildRolePackage());
    }

    @Test
    void legacyPackageWithoutWakeProfileRemainsAvailable() {
        AgentEntity agent = validRoleAgent();
        agent.setRoleWakeWord(null);
        agent.setRoleWakeModel(null);
        agent.setRoleWakeMode(null);
        agent.setRoleWakeConfigVersion(null);
        when(agentDao.selectById("agent-1")).thenReturn(agent);

        DeviceReportRespDTO.Role role = buildRolePackage();
        assertNotNull(role);
        assertNull(role.getWakeWord());
        assertNull(role.getWakeModel());
    }

    @Test
    void dynamicWakeProfileIsReturnedAtomically() {
        AgentEntity agent = validRoleAgent();
        agent.setRoleWakeMode("dynamic");
        agent.setRoleWakeWord("你好四郎");
        agent.setRoleWakeModel("mn5q8_cn");
        agent.setRoleWakeCommand("ni hao si lang");
        agent.setRoleWakeLanguage("cn");
        agent.setRoleWakeThreshold(new BigDecimal("0.225"));
        agent.setRoleWakeConfigVersion(4L);
        when(agentDao.selectById("agent-1")).thenReturn(agent);

        DeviceReportRespDTO.Role role = buildRolePackage();

        assertNotNull(role);
        assertEquals("dynamic", role.getWakeMode());
        assertEquals("你好四郎", role.getWakeWord());
        assertEquals("mn5q8_cn", role.getWakeModel());
        assertEquals("ni hao si lang", role.getWakeCommand());
        assertEquals("cn", role.getWakeLanguage());
        assertEquals(new BigDecimal("0.225"), role.getWakeThreshold());
        assertEquals(4L, role.getWakeConfigVersion());

        String json = JsonUtils.toJsonString(role);
        assertTrue(json.contains("\"wake_word\":\"你好四郎\""));
        assertTrue(json.contains("\"wake_model\":\"mn5q8_cn\""));
        assertTrue(json.contains("\"wake_mode\":\"dynamic\""));
        assertTrue(json.contains("\"wake_command\":\"ni hao si lang\""));
        assertTrue(json.contains("\"wake_language\":\"cn\""));
        assertTrue(json.contains("\"wake_threshold\":0.225"));
        assertTrue(json.contains("\"wake_config_version\":4"));
    }

    @Test
    void roleRuntimeCapabilityRequiresNewAppAndFixedModelPartition() {
        DeviceReportReqDTO report = compatibleDeviceReport();
        assertTrue(supportsDecoupledRoleRuntime(report));

        report.getApplication().setVersion("2.3.15");
        assertFalse(supportsDecoupledRoleRuntime(report));

        report = compatibleDeviceReport();
        report.setPartitionTable(List.of());
        assertFalse(supportsDecoupledRoleRuntime(report));

        report = compatibleDeviceReport();
        report.getPartitionTable().get(0).setSize(3 * 1024 * 1024 - 1);
        assertFalse(supportsDecoupledRoleRuntime(report));
    }

    private boolean supportsDecoupledRoleRuntime(DeviceReportReqDTO report) {
        return Boolean.TRUE.equals(ReflectionTestUtils.invokeMethod(
                service, "supportsDecoupledRoleRuntime", report));
    }

    private DeviceReportReqDTO compatibleDeviceReport() {
        DeviceReportReqDTO.Application application = new DeviceReportReqDTO.Application();
        application.setVersion("2.3.16");
        DeviceReportReqDTO.Partition model = new DeviceReportReqDTO.Partition();
        model.setLabel("model");
        model.setAddress(0x1000000);
        model.setSize(3 * 1024 * 1024);
        DeviceReportReqDTO report = new DeviceReportReqDTO();
        report.setApplication(application);
        report.setFlashSize(32 * 1024 * 1024);
        report.setPartitionTable(List.of(model));
        return report;
    }

    private DeviceReportRespDTO.Role buildRolePackage() {
        return ReflectionTestUtils.invokeMethod(service, "buildRolePackage", device);
    }

    private AgentEntity validRoleAgent() {
        AgentEntity agent = new AgentEntity();
        agent.setId("agent-1");
        agent.setRoleCode("cheese_cat");
        agent.setRoleAssetVersion("2026.08.16.1");
        agent.setRoleAssetUrl("https://assets.example/cheese.bin");
        agent.setRoleAssetSha256("a".repeat(64));
        agent.setRoleAssetSize(3_456_789L);
        agent.setRoleDistribution("public");
        agent.setRoleWakeWord("你好小智");
        agent.setRoleWakeModel("wn9_nihaoxiaozhi_tts");
        agent.setRoleWakeMode("trained");
        agent.setRoleWakeConfigVersion(1L);
        return agent;
    }
}
