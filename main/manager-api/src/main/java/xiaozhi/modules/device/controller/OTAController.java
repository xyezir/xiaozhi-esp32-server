package xiaozhi.modules.device.controller;

import java.nio.charset.StandardCharsets;

import org.apache.commons.lang3.StringUtils;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.swagger.v3.oas.annotations.Hidden;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.sys.service.SysParamsService;

@Tag(name = "设备管理", description = "OTA 相关接口")
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/ota/")
public class OTAController {
    private final DeviceService deviceService;
    private final SysParamsService sysParamsService;

    @Operation(summary = "OTA版本和设备激活状态检查")
    @PostMapping
    public ResponseEntity<String> checkOTAVersion(
            @RequestBody DeviceReportReqDTO deviceReportReqDTO,
            @Parameter(name = "Device-Id", description = "设备唯一标识", required = true, in = ParameterIn.HEADER) @RequestHeader("Device-Id") String deviceId,
            @Parameter(name = "Client-Id", description = "客户端标识", required = false, in = ParameterIn.HEADER) @RequestHeader(value = "Client-Id", required = false) String clientId) {
        if (StringUtils.isBlank(deviceId)) {
            return createResponse(DeviceReportRespDTO.createError("Device ID is required"));
        }
        if (StringUtils.isBlank(clientId)) {
            clientId = deviceId;
        }
        boolean macAddressValid = isMacAddressValid(deviceId);
        // 设备Id和Mac地址应是一致的, 并且必须需要application字段
        if (!macAddressValid) {
            return createResponse(DeviceReportRespDTO.createError("Invalid device ID"));
        }
        return createResponse(deviceService.checkDeviceActive(deviceId, clientId, deviceReportReqDTO));
    }

    @Operation(summary = "设备快速检查激活状态")
    @PostMapping("activate")
    public ResponseEntity<String> activateDevice(
            @Parameter(name = "Device-Id", description = "设备唯一标识", required = true, in = ParameterIn.HEADER) @RequestHeader("Device-Id") String deviceId,
            @Parameter(name = "Client-Id", description = "客户端标识", required = false, in = ParameterIn.HEADER) @RequestHeader(value = "Client-Id", required = false) String clientId) {
        if (StringUtils.isBlank(deviceId)) {
            log.warn("收到激活请求但Device-Id为空，返回202");
            return ResponseEntity.status(202).build();
        }
        DeviceEntity device = deviceService.getDeviceByMacAddress(deviceId);
        if (device == null) {
            log.warn("设备还未完成绑定，激活请求返回202");
            return ResponseEntity.status(202).build();
        }
        log.info("设备已完成绑定，activate 接口返回 success");
        return ResponseEntity.ok("success");
    }

    @GetMapping
    @Hidden
    public ResponseEntity<String> getOTA() {
        String mqttUdpConfig = sysParamsService.getValue(Constant.SERVER_MQTT_GATEWAY, false);
        String wsUrl = sysParamsService.getValue(Constant.SERVER_WEBSOCKET, true);
        boolean mqttConfigured = StringUtils.isNotBlank(mqttUdpConfig) && !"null".equals(mqttUdpConfig);
        boolean websocketConfigured = StringUtils.isNotBlank(wsUrl) && !"null".equals(wsUrl);
        if (!mqttConfigured && !websocketConfigured) {
            return ResponseEntity.ok("OTA接口不正常，mqtt_gateway和websocket至少需要配置一项");
        }
        String otaUrl = sysParamsService.getValue(Constant.SERVER_OTA, true);
        if (StringUtils.isBlank(otaUrl) || otaUrl.equals("null")) {
            return ResponseEntity.ok("OTA接口不正常，缺少ota地址，请登录智控台，在参数管理找到【server.ota】配置");
        }
        int websocketCount = websocketConfigured ? wsUrl.split(";").length : 0;
        return ResponseEntity.ok("OTA接口运行正常，websocket集群数量：" + websocketCount
                + "，mqtt_gateway：" + (mqttConfigured ? "已配置" : "未配置"));
    }

    @SneakyThrows
    private ResponseEntity<String> createResponse(DeviceReportRespDTO deviceReportRespDTO) {
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
        String json = objectMapper.writeValueAsString(deviceReportRespDTO);
        byte[] jsonBytes = json.getBytes(StandardCharsets.UTF_8);
        return ResponseEntity
                .ok()
                .contentType(MediaType.APPLICATION_JSON)
                .contentLength(jsonBytes.length)
                .body(json);
    }

    /**
     * 简单判断mac地址是否有效（非严格）
     * 
     * @param macAddress
     * @return
     */
    private boolean isMacAddressValid(String macAddress) {
        if (StringUtils.isBlank(macAddress)) {
            return false;
        }
        // MAC地址通常为12位十六进制数字，可以包含冒号或连字符分隔符
        String macPattern = "^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$";
        return macAddress.matches(macPattern);
    }
}
