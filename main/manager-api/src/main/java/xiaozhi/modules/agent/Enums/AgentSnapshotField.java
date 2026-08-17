package xiaozhi.modules.agent.Enums;

import java.util.Arrays;
import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Function;

import lombok.Getter;
import xiaozhi.modules.agent.dto.AgentSnapshotDataDTO;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;

@Getter
public enum AgentSnapshotField {
    AGENT_CODE("agentCode", AgentSnapshotDataDTO::getAgentCode, AgentUpdateDTO::getAgentCode,
            (agent, data) -> agent.setAgentCode(data.getAgentCode())),
    AGENT_NAME("agentName", AgentSnapshotDataDTO::getAgentName, AgentUpdateDTO::getAgentName,
            (agent, data) -> agent.setAgentName(data.getAgentName())),
    ASR_MODEL_ID("asrModelId", AgentSnapshotDataDTO::getAsrModelId, AgentUpdateDTO::getAsrModelId,
            (agent, data) -> agent.setAsrModelId(data.getAsrModelId())),
    VAD_MODEL_ID("vadModelId", AgentSnapshotDataDTO::getVadModelId, AgentUpdateDTO::getVadModelId,
            (agent, data) -> agent.setVadModelId(data.getVadModelId())),
    LLM_MODEL_ID("llmModelId", AgentSnapshotDataDTO::getLlmModelId, AgentUpdateDTO::getLlmModelId,
            (agent, data) -> agent.setLlmModelId(data.getLlmModelId())),
    SLM_MODEL_ID("slmModelId", AgentSnapshotDataDTO::getSlmModelId, AgentUpdateDTO::getSlmModelId,
            (agent, data) -> agent.setSlmModelId(data.getSlmModelId())),
    VLLM_MODEL_ID("vllmModelId", AgentSnapshotDataDTO::getVllmModelId, AgentUpdateDTO::getVllmModelId,
            (agent, data) -> agent.setVllmModelId(data.getVllmModelId())),
    TTS_MODEL_ID("ttsModelId", AgentSnapshotDataDTO::getTtsModelId, AgentUpdateDTO::getTtsModelId,
            (agent, data) -> agent.setTtsModelId(data.getTtsModelId())),
    TTS_VOICE_ID("ttsVoiceId", AgentSnapshotDataDTO::getTtsVoiceId, AgentUpdateDTO::getTtsVoiceId,
            (agent, data) -> agent.setTtsVoiceId(data.getTtsVoiceId())),
    TTS_LANGUAGE("ttsLanguage", AgentSnapshotDataDTO::getTtsLanguage, AgentUpdateDTO::getTtsLanguage,
            (agent, data) -> agent.setTtsLanguage(data.getTtsLanguage())),
    TTS_VOLUME("ttsVolume", AgentSnapshotDataDTO::getTtsVolume, AgentUpdateDTO::getTtsVolume,
            (agent, data) -> agent.setTtsVolume(data.getTtsVolume())),
    TTS_RATE("ttsRate", AgentSnapshotDataDTO::getTtsRate, AgentUpdateDTO::getTtsRate,
            (agent, data) -> agent.setTtsRate(data.getTtsRate())),
    TTS_PITCH("ttsPitch", AgentSnapshotDataDTO::getTtsPitch, AgentUpdateDTO::getTtsPitch,
            (agent, data) -> agent.setTtsPitch(data.getTtsPitch())),
    MEM_MODEL_ID("memModelId", AgentSnapshotDataDTO::getMemModelId, AgentUpdateDTO::getMemModelId,
            (agent, data) -> agent.setMemModelId(data.getMemModelId())),
    INTENT_MODEL_ID("intentModelId", AgentSnapshotDataDTO::getIntentModelId, AgentUpdateDTO::getIntentModelId,
            (agent, data) -> agent.setIntentModelId(data.getIntentModelId())),
    CHAT_HISTORY_CONF("chatHistoryConf", AgentSnapshotDataDTO::getChatHistoryConf, AgentUpdateDTO::getChatHistoryConf,
            (agent, data) -> agent.setChatHistoryConf(data.getChatHistoryConf())),
    SYSTEM_PROMPT("systemPrompt", AgentSnapshotDataDTO::getSystemPrompt, AgentUpdateDTO::getSystemPrompt,
            (agent, data) -> agent.setSystemPrompt(data.getSystemPrompt())),
    ROLE_CODE("roleCode", AgentSnapshotDataDTO::getRoleCode, AgentUpdateDTO::getRoleCode,
            (agent, data) -> agent.setRoleCode(data.getRoleCode())),
    ROLE_AVATAR_URL("roleAvatarUrl", AgentSnapshotDataDTO::getRoleAvatarUrl, AgentUpdateDTO::getRoleAvatarUrl,
            (agent, data) -> agent.setRoleAvatarUrl(data.getRoleAvatarUrl())),
    ROLE_THEME_JSON("roleThemeJson", AgentSnapshotDataDTO::getRoleThemeJson, AgentUpdateDTO::getRoleThemeJson,
            (agent, data) -> agent.setRoleThemeJson(data.getRoleThemeJson())),
    ROLE_ASSET_VERSION("roleAssetVersion", AgentSnapshotDataDTO::getRoleAssetVersion,
            AgentUpdateDTO::getRoleAssetVersion,
            (agent, data) -> agent.setRoleAssetVersion(data.getRoleAssetVersion())),
    ROLE_ASSET_URL("roleAssetUrl", AgentSnapshotDataDTO::getRoleAssetUrl, AgentUpdateDTO::getRoleAssetUrl,
            (agent, data) -> agent.setRoleAssetUrl(data.getRoleAssetUrl())),
    ROLE_ASSET_SHA256("roleAssetSha256", AgentSnapshotDataDTO::getRoleAssetSha256,
            AgentUpdateDTO::getRoleAssetSha256,
            (agent, data) -> agent.setRoleAssetSha256(data.getRoleAssetSha256())),
    ROLE_ASSET_SIZE("roleAssetSize", AgentSnapshotDataDTO::getRoleAssetSize, AgentUpdateDTO::getRoleAssetSize,
            (agent, data) -> agent.setRoleAssetSize(data.getRoleAssetSize())),
    ROLE_DISTRIBUTION("roleDistribution", AgentSnapshotDataDTO::getRoleDistribution,
            AgentUpdateDTO::getRoleDistribution,
            (agent, data) -> agent.setRoleDistribution(data.getRoleDistribution())),
    ROLE_WAKE_WORD("roleWakeWord", AgentSnapshotDataDTO::getRoleWakeWord, AgentUpdateDTO::getRoleWakeWord,
            (agent, data) -> agent.setRoleWakeWord(data.getRoleWakeWord())),
    ROLE_WAKE_MODEL("roleWakeModel", AgentSnapshotDataDTO::getRoleWakeModel, AgentUpdateDTO::getRoleWakeModel,
            (agent, data) -> agent.setRoleWakeModel(data.getRoleWakeModel())),
    ROLE_WAKE_MODE("roleWakeMode", AgentSnapshotDataDTO::getRoleWakeMode, AgentUpdateDTO::getRoleWakeMode,
            (agent, data) -> agent.setRoleWakeMode(data.getRoleWakeMode())),
    ROLE_WAKE_COMMAND("roleWakeCommand", AgentSnapshotDataDTO::getRoleWakeCommand,
            AgentUpdateDTO::getRoleWakeCommand,
            (agent, data) -> agent.setRoleWakeCommand(data.getRoleWakeCommand())),
    ROLE_WAKE_LANGUAGE("roleWakeLanguage", AgentSnapshotDataDTO::getRoleWakeLanguage,
            AgentUpdateDTO::getRoleWakeLanguage,
            (agent, data) -> agent.setRoleWakeLanguage(data.getRoleWakeLanguage())),
    ROLE_WAKE_THRESHOLD("roleWakeThreshold", AgentSnapshotDataDTO::getRoleWakeThreshold,
            AgentUpdateDTO::getRoleWakeThreshold,
            (agent, data) -> agent.setRoleWakeThreshold(data.getRoleWakeThreshold())),
    ROLE_WAKE_CONFIG_VERSION("roleWakeConfigVersion", AgentSnapshotDataDTO::getRoleWakeConfigVersion,
            AgentUpdateDTO::getRoleWakeConfigVersion,
            (agent, data) -> agent.setRoleWakeConfigVersion(data.getRoleWakeConfigVersion())),
    SUMMARY_MEMORY("summaryMemory", AgentSnapshotDataDTO::getSummaryMemory, AgentUpdateDTO::getSummaryMemory,
            (agent, data) -> agent.setSummaryMemory(data.getSummaryMemory())),
    LANG_CODE("langCode", AgentSnapshotDataDTO::getLangCode, AgentUpdateDTO::getLangCode,
            (agent, data) -> agent.setLangCode(data.getLangCode())),
    LANGUAGE("language", AgentSnapshotDataDTO::getLanguage, AgentUpdateDTO::getLanguage,
            (agent, data) -> agent.setLanguage(data.getLanguage())),
    SORT("sort", AgentSnapshotDataDTO::getSort, AgentUpdateDTO::getSort,
            (agent, data) -> agent.setSort(data.getSort())),
    FUNCTIONS("functions", AgentSnapshotDataDTO::getFunctions, AgentUpdateDTO::getFunctions, null),
    CONTEXT_PROVIDERS("contextProviders", AgentSnapshotDataDTO::getContextProviders,
            AgentUpdateDTO::getContextProviders, null),
    CORRECT_WORD_FILE_IDS("correctWordFileIds", AgentSnapshotDataDTO::getCorrectWordFileIds,
            AgentUpdateDTO::getCorrectWordFileIds, null),
    TAG_NAMES("tagNames", AgentSnapshotDataDTO::getTagNames, AgentUpdateDTO::getTagNames, null);

    private final String fieldName;
    private final Function<AgentSnapshotDataDTO, Object> snapshotGetter;
    private final Function<AgentUpdateDTO, Object> updateGetter;
    private final BiConsumer<AgentEntity, AgentSnapshotDataDTO> restoreApplier;

    AgentSnapshotField(String fieldName, Function<AgentSnapshotDataDTO, Object> snapshotGetter,
            Function<AgentUpdateDTO, Object> updateGetter,
            BiConsumer<AgentEntity, AgentSnapshotDataDTO> restoreApplier) {
        this.fieldName = fieldName;
        this.snapshotGetter = snapshotGetter;
        this.updateGetter = updateGetter;
        this.restoreApplier = restoreApplier;
    }

    public static List<String> names() {
        return Arrays.stream(values()).map(AgentSnapshotField::getFieldName).toList();
    }

    public static String canonicalName(String fieldName) {
        return "tags".equals(fieldName) ? TAG_NAMES.getFieldName() : fieldName;
    }

    public Object snapshotValue(AgentSnapshotDataDTO data) {
        return data == null ? null : snapshotGetter.apply(data);
    }

    public Object updateValue(AgentUpdateDTO data) {
        return data == null ? null : updateGetter.apply(data);
    }

    public boolean isRestorableAgentField() {
        return restoreApplier != null;
    }

    public void applyTo(AgentEntity agent, AgentSnapshotDataDTO data) {
        if (restoreApplier != null) {
            restoreApplier.accept(agent, data);
        }
    }
}
