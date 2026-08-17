package xiaozhi.modules.agent.entity;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("ai_agent")
@Schema(description = "智能体信息")
public class AgentEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "智能体唯一标识")
    private String id;

    @Schema(description = "所属用户ID")
    private Long userId;

    @Schema(description = "智能体编码")
    private String agentCode;

    @Schema(description = "智能体名称")
    private String agentName;

    @Schema(description = "语音识别模型标识")
    private String asrModelId;

    @Schema(description = "语音活动检测标识")
    private String vadModelId;

    @Schema(description = "大语言模型标识")
    private String llmModelId;

    @Schema(description = "小模型标识")
    private String slmModelId;

    @Schema(description = "VLLM模型标识")
    private String vllmModelId;

    @Schema(description = "语音合成模型标识")
    private String ttsModelId;

    @Schema(description = "音色标识")
    private String ttsVoiceId;

    @Schema(description = "音色语言")
    private String ttsLanguage;

    @Schema(description = "TTS音量")
    private Integer ttsVolume;

    @Schema(description = "TTS语速")
    private Integer ttsRate;

    @Schema(description = "TTS音调")
    private Integer ttsPitch;

    @Schema(description = "记忆模型标识")
    private String memModelId;

    @Schema(description = "意图模型标识")
    private String intentModelId;

    @Schema(description = "聊天记录配置（0不记录 1仅记录文本 2记录文本和语音）")
    private Integer chatHistoryConf;

    @Schema(description = "角色设定参数")
    private String systemPrompt;

    @Schema(description = "设备角色稳定标识")
    private String roleCode;

    @Schema(description = "角色预览图")
    private String roleAvatarUrl;

    @Schema(description = "角色主题JSON")
    private String roleThemeJson;

    @Schema(description = "角色资源版本")
    private String roleAssetVersion;

    @Schema(description = "角色资源下载地址")
    private String roleAssetUrl;

    @Schema(description = "角色资源SHA-256")
    private String roleAssetSha256;

    @Schema(description = "角色资源字节数")
    private Long roleAssetSize;

    @Schema(description = "角色分发级别")
    private String roleDistribution;

    @Schema(description = "角色实际唤醒短语；必须与 WakeNet 模型同时配置")
    private String roleWakeWord;

    @Schema(description = "角色实际 WakeNet 模型标识；必须与唤醒短语同时配置")
    private String roleWakeModel;

    @Schema(description = "角色唤醒模式: trained/dynamic")
    private String roleWakeMode;

    @Schema(description = "动态唤醒声学命令；中文使用空格分隔的拼音")
    private String roleWakeCommand;

    @Schema(description = "动态唤醒语言: cn/en")
    private String roleWakeLanguage;

    @Schema(description = "动态唤醒检测阈值")
    private BigDecimal roleWakeThreshold;

    @Schema(description = "角色唤醒配置版本")
    private Long roleWakeConfigVersion;

    @Schema(description = "总结记忆", example = "构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹\n" +
            "根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;

    @Schema(description = "语言编码")
    private String langCode;

    @Schema(description = "交互语种")
    private String language;

    @Schema(description = "排序")
    private Integer sort;

    @Schema(description = "创建者")
    private Long creator;

    @Schema(description = "创建时间")
    private Date createdAt;

    @Schema(description = "更新者")
    private Long updater;

    @Schema(description = "更新时间")
    private Date updatedAt;
}
