<template>
  <div class="welcome">
    <HeaderBar />

    <div class="operation-bar">
      <h2 class="page-title">{{ $t('templateQuickConfig.title') }}</h2>
    </div>

    <div class="main-wrapper">
      <div class="content-panel">
        <div class="content-area">
          <el-card class="config-card" shadow="never">
              <div class="config-header">
              <!-- 使用角色配置页面相同的彩色图标效果 -->
              <div class="header-icon">
                <img loading="lazy" src="@/assets/home/setting-user.png" alt="">
              </div>
              <span class="header-title">{{ form.agentName }}</span>
              <div class="header-actions">
                <el-button type="primary" class="save-btn" @click="saveConfig">{{ $t('templateQuickConfig.saveConfig') }}</el-button>
                <el-button class="reset-btn" @click="resetConfig">{{ $t('templateQuickConfig.resetConfig') }}</el-button>
                <button class="custom-close-btn" @click="goToHome">
                  ×
                </button>
              </div>
            </div>
            <div class="divider"></div>

            <el-form ref="form" :model="form" label-width="72px" class="full-height-form">
              <!-- 助手昵称 -->
              <el-form-item :label="$t('templateQuickConfig.agentSettings.agentName')" prop="agentName" class="nickname-item">
                <el-input
                  v-model="form.agentName"
                  :placeholder="$t('templateQuickConfig.agentSettings.agentNamePlaceholder')"
                  :validate-event="false"
                  class="form-input"
                />
              </el-form-item>
              
              <!-- 角色介绍 -->
              <el-form-item :label="$t('templateQuickConfig.agentSettings.systemPrompt')" prop="systemPrompt" class="description-item">
                <el-input
                  v-model="form.systemPrompt"
                  type="textarea"
                  :placeholder="$t('templateQuickConfig.agentSettings.systemPromptPlaceholder')"
                  :validate-event="false"
                  show-word-limit
                  maxlength="2000"
                />
              </el-form-item>

              <div class="role-package-grid">
                <el-form-item label="角色标识" prop="roleCode">
                  <el-input v-model="form.roleCode" placeholder="pet_expert_shilang" />
                </el-form-item>
                <el-form-item label="资源版本" prop="roleAssetVersion">
                  <el-input v-model="form.roleAssetVersion" placeholder="2026.08.16.1" />
                </el-form-item>
                <el-form-item label="预览图" prop="roleAvatarUrl">
                  <el-input v-model="form.roleAvatarUrl" placeholder="https://.../avatar.png" />
                </el-form-item>
                <el-form-item label="分发级别" prop="roleDistribution">
                  <el-select v-model="form.roleDistribution">
                    <el-option label="公开可分发" value="public" />
                    <el-option label="仅内部原型" value="internal-only" />
                  </el-select>
                </el-form-item>
                <el-form-item label="资源包" prop="roleAssetUrl" class="role-package-wide">
                  <el-input v-model="form.roleAssetUrl" placeholder="https://.../role-assets.bin" />
                </el-form-item>
                <el-form-item label="SHA-256" prop="roleAssetSha256" class="role-package-wide">
                  <el-input v-model="form.roleAssetSha256" maxlength="64" />
                </el-form-item>
                <el-form-item label="包字节数" prop="roleAssetSize">
                  <el-input-number v-model="form.roleAssetSize" :min="0" :max="8388608" :controls="false" />
                </el-form-item>
                <el-form-item label="唤醒模式" prop="roleWakeMode">
                  <el-select v-model="form.roleWakeMode" clearable placeholder="未配置">
                    <el-option label="高可靠 WakeNet" value="trained" />
                    <el-option label="动态 MultiNet" value="dynamic" />
                  </el-select>
                </el-form-item>
                <el-form-item label="实际唤醒词" prop="roleWakeWord">
                  <el-input v-model="form.roleWakeWord" placeholder="你好四郎" maxlength="32" />
                </el-form-item>
                <el-form-item label="识别模型" prop="roleWakeModel">
                  <el-input v-model="form.roleWakeModel" :placeholder="form.roleWakeMode === 'dynamic' ? 'mn5q8_cn' : 'wn9_nihaoxiaozhi_tts'" maxlength="96" />
                </el-form-item>
                <el-form-item v-if="form.roleWakeMode === 'dynamic'" label="识别语言" prop="roleWakeLanguage">
                  <el-select v-model="form.roleWakeLanguage">
                    <el-option label="中文" value="cn" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="form.roleWakeMode === 'dynamic'" label="声学命令" prop="roleWakeCommand" class="role-package-wide">
                  <el-input v-model="form.roleWakeCommand" placeholder="ni hao si lang" maxlength="160" />
                </el-form-item>
                <el-form-item v-if="form.roleWakeMode === 'dynamic'" label="检测阈值" prop="roleWakeThreshold">
                  <el-input-number v-model="form.roleWakeThreshold" :min="0.05" :max="0.95" :step="0.01" :precision="3" />
                </el-form-item>
                <el-form-item v-if="form.roleWakeMode" label="配置版本" prop="roleWakeConfigVersion">
                  <el-input-number v-model="form.roleWakeConfigVersion" :min="1" :max="4294967295" :step="1" :precision="0" />
                </el-form-item>
                <el-form-item label="主题JSON" prop="roleThemeJson" class="role-package-wide">
                  <el-input v-model="form.roleThemeJson" type="textarea" :rows="2" placeholder='{"accent":"#4CCC70"}' />
                </el-form-item>
              </div>
            </el-form>
          </el-card>
        </div>
      </div>
    </div>
    <el-footer>
      <version-footer />
    </el-footer>
  </div>
</template>

<script>
import HeaderBar from "@/components/HeaderBar.vue";
import agentApi from '@/apis/module/agent';
import VersionFooter from "@/components/VersionFooter.vue";
import { validateRolePackage } from "@/utils/rolePackage";

// 默认模型配置常量
const DEFAULT_MODEL_CONFIG = {
  ttsModelId: "TTS_EdgeTTS",
  vadModelId: "VAD_SileroVAD",
  asrModelId: "ASR_FunASR",
  llmModelId: "LLM_ChatGLMLLM",
  vllmModelId: "VLLM_ChatGLMVLLM",
  memModelId: "Memory_nomem",
  intentModelId: "Intent_function_call"
};

export default {
  name: 'TemplateQuickConfig',
  components: { HeaderBar, VersionFooter },
  data() {
    return {
      form: {
        agentCode: "小智",
        agentName: "",
        systemPrompt: "",
        roleCode: "",
        roleAvatarUrl: "",
        roleThemeJson: "{}",
        roleAssetVersion: "",
        roleAssetUrl: "",
        roleAssetSha256: "",
        roleAssetSize: 0,
        roleDistribution: "public",
        roleWakeWord: "",
        roleWakeModel: "",
        roleWakeMode: "",
        roleWakeCommand: "",
        roleWakeLanguage: "",
        roleWakeThreshold: null,
        roleWakeConfigVersion: null,
        sort: 0,
        model: { ...DEFAULT_MODEL_CONFIG }
      },
      templateId: '',
      originalForm: null
    };
  },
  methods: {
    // 返回模板管理页面
    goToHome() {
      this.$router.push('/agent-template-management');
    },
    
    // 保存配置
    saveConfig() {
      const roleError = validateRolePackage(this.form);
      if (roleError) {
        this.$message.error({ message: roleError, showClose: true });
        return;
      }
      const configData = this.prepareConfigData();
      
      if (this.templateId) {
        this.updateExistingTemplate(configData);
      } else {
        this.createNewTemplate(configData);
      }
    },
    
    // 准备配置数据
    prepareConfigData() {
      return {
        id: this.templateId || '',
        agentCode: this.form.agentCode,
        agentName: this.form.agentName,
        systemPrompt: this.form.systemPrompt,
        roleCode: this.form.roleCode,
        roleAvatarUrl: this.form.roleAvatarUrl,
        roleThemeJson: this.form.roleThemeJson,
        roleAssetVersion: this.form.roleAssetVersion,
        roleAssetUrl: this.form.roleAssetUrl,
        roleAssetSha256: this.form.roleAssetSha256,
        roleAssetSize: this.form.roleAssetSize,
        roleDistribution: this.form.roleDistribution,
        roleWakeWord: this.form.roleWakeWord,
        roleWakeModel: this.form.roleWakeModel,
        roleWakeMode: this.form.roleWakeMode,
        roleWakeCommand: this.form.roleWakeCommand,
        roleWakeLanguage: this.form.roleWakeLanguage,
        roleWakeThreshold: this.form.roleWakeThreshold,
        roleWakeConfigVersion: this.form.roleWakeConfigVersion,
        sort: this.form.sort,
        functions: [],
        // 包含必要的模型字段以确保API调用成功
        ...this.form.model
      };
    },
    
    // 更新现有模板
    updateExistingTemplate(configData) {
      agentApi.updateAgentTemplate(configData, (res) => {
        if (res && res.data && res.data.code === 0) {
          this.$message.success({ 
            message: this.$t('templateQuickConfig.saveSuccess'), 
            showClose: true 
          });
          this.originalForm = JSON.parse(JSON.stringify(this.form));
        } else {
          this.$message.error({ 
            message: res?.data?.msg || this.$t('templateQuickConfig.saveFailed'), 
            showClose: true 
          });
        }
      });
    },
    
    // 创建新模板
    createNewTemplate(configData) {
      agentApi.addAgentTemplate(configData, (res) => {
        if (res && res.data && res.data.code === 0) {
          this.$message.success({ 
            message: this.$t('templateQuickConfig.saveSuccess'), 
            showClose: true 
          });
          this.goToHome();
        } else {
          this.$message.error({ 
            message: res?.data?.msg || this.$t('templateQuickConfig.saveFailed'), 
            showClose: true 
          });
        }
      });
    },
    
    // 重置配置
    resetConfig() {
      this.$confirm(
        this.$t('templateQuickConfig.confirmReset'), 
        this.$t('common.tip'), 
        {
          confirmButtonText: this.$t('common.confirm'),
          cancelButtonText: this.$t('common.cancel'),
          type: 'warning'
        }
      ).then(() => {
        if (this.originalForm) {
          this.form = JSON.parse(JSON.stringify(this.originalForm));
        }
        this.$message.success({ 
          message: this.$t('templateQuickConfig.resetSuccess'), 
          showClose: true 
        });
      }).catch(() => {});
    },
    
    // 根据ID获取模板
    fetchTemplateById(templateId) {
      agentApi.getAgentTemplateById(templateId, (res) => {
        if (res && res.data && res.data.code === 0 && res.data.data) {
          const template = res.data.data;
          this.applyTemplateData(template);
          this.templateId = templateId;
          this.originalForm = JSON.parse(JSON.stringify(this.form));
        } else {
          this.$message.error(res?.data?.msg || this.$t('templateQuickConfig.templateNotFound'));
        }
      });
    },
    
    // 应用模板数据
    applyTemplateData(templateData) {
      this.form = {
        ...this.form,
        agentName: templateData.agentName || this.form.agentName,
        agentCode: templateData.agentCode || this.form.agentCode,
        systemPrompt: templateData.systemPrompt || this.form.systemPrompt,
        roleCode: templateData.roleCode || "",
        roleAvatarUrl: templateData.roleAvatarUrl || "",
        roleThemeJson: templateData.roleThemeJson || "{}",
        roleAssetVersion: templateData.roleAssetVersion || "",
        roleAssetUrl: templateData.roleAssetUrl || "",
        roleAssetSha256: templateData.roleAssetSha256 || "",
        roleAssetSize: templateData.roleAssetSize || 0,
        roleDistribution: templateData.roleDistribution || "public",
        roleWakeWord: templateData.roleWakeWord || "",
        roleWakeModel: templateData.roleWakeModel || "",
        roleWakeMode: templateData.roleWakeMode || (templateData.roleWakeWord ? "trained" : ""),
        roleWakeCommand: templateData.roleWakeCommand || "",
        roleWakeLanguage: templateData.roleWakeLanguage || "",
        roleWakeThreshold: templateData.roleWakeThreshold ?? null,
        roleWakeConfigVersion: templateData.roleWakeConfigVersion || (templateData.roleWakeWord ? 1 : null),
        sort: templateData.sort || this.form.sort,
        model: {
          ttsModelId: templateData.ttsModelId || this.form.model.ttsModelId,
          vadModelId: templateData.vadModelId || this.form.model.vadModelId,
          asrModelId: templateData.asrModelId || this.form.model.asrModelId,
          llmModelId: templateData.llmModelId || this.form.model.llmModelId,
          vllmModelId: templateData.vllmModelId || this.form.model.vllmModelId,
          memModelId: templateData.memModelId || this.form.model.memModelId,
          intentModelId: templateData.intentModelId || this.form.model.intentModelId
        }
      };
    },
    
    // 设置默认模板值
    setDefaultTemplateValues() {
      this.form = {
        ...this.form,
        agentName: this.$t('templateQuickConfig.newTemplate'),
        agentCode: '小智',
        systemPrompt: '',
        roleCode: '',
        roleAvatarUrl: '',
        roleThemeJson: '{}',
        roleAssetVersion: '',
        roleAssetUrl: '',
        roleAssetSha256: '',
        roleAssetSize: 0,
        roleDistribution: 'public',
        roleWakeWord: '',
        roleWakeModel: '',
        roleWakeMode: '',
        roleWakeCommand: '',
        roleWakeLanguage: '',
        roleWakeThreshold: null,
        roleWakeConfigVersion: null,
        sort: 1
      };
      
      this.originalForm = JSON.parse(JSON.stringify(this.form));
    },
    
    // 获取模板列表并设置排序号
    fetchTemplateListForSort() {
      agentApi.getAgentTemplate((res) => {
        if (res && res.data && res.data.code === 0) {
          const templateList = res.data.data || [];
          if (templateList.length > 0) {
            const maxSort = Math.max(...templateList.map(t => t.sort || 0));
            this.form.sort = maxSort + 1;
          } else {
            this.form.sort = 1;
          }
        } else {
          this.form.sort = 1;
        }
        
        this.originalForm = JSON.parse(JSON.stringify(this.form));
      });
    }
  },
  
  // 组件挂载时执行初始化
  mounted() {
    const templateId = this.$route.query.templateId;
    
    if (templateId) {
      // 编辑模式：加载现有模板
      this.fetchTemplateById(templateId);
    } else {
      // 新建模式：设置默认值并获取排序号
      this.form.agentName = this.$t('templateQuickConfig.newTemplate');
      this.fetchTemplateListForSort();
    }
  }
};
</script>

<style scoped>
.welcome {
  min-width: 900px;
  height: 100vh;
  display: flex;
  position: relative;
  flex-direction: column;
  background: #eff4ff;
  background-size: cover;
  -webkit-background-size: cover;
  -o-background-size: cover;
  overflow: hidden;
}

.operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: #2c3e50;
}

.main-wrapper {
  height: calc(100vh - 63px - 35px - 60px);
  margin: 0 22px;
  border-radius: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: relative;
  background: rgba(237, 242, 255, 0.5);
  display: flex;
  flex-direction: column;
  padding: 0 !important;
}

.role-package-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 18px;
}

.role-package-wide {
  grid-column: 1 / -1;
}

.content-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
  border-radius: 15px;
  background: transparent;
  border: 1px solid #fff;
}

.content-area {
  flex: 1;
  height: 100%;
  overflow: auto;
  background-color: white;
  display: flex;
  flex-direction: column;
}

.config-card {
  background: white !important;
  border-radius: 15px !important;
  overflow: hidden !important;
  height: 100% !important;
  margin: 0 !important;
  border: none !important;
  box-shadow: none !important;
}

.full-height-form {
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
  height: calc(100% - 120px);
}

.nickname-item {
  margin-bottom: 0 !important;
}

.description-item {
  margin-bottom: 0 !important;
  display: flex;
  flex-direction: column;
}

::v-deep .description-item .el-textarea {
  height: 300px;
  min-height: 200px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

::v-deep .description-item .el-textarea__inner {
  height: 100% !important;
  min-height: 200px !important;
  max-height: 400px !important;
  resize: vertical !important;
  line-height: 1.6;
  font-size: 14px;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  color: #303133;
}

::v-deep .el-form-item__label {
  font-size: 12px !important;
  color: #3d4566 !important;
  font-weight: 400;
  line-height: 22px;
  padding-bottom: 2px;
}

::v-deep .el-textarea .el-input__count {
  color: #909399;
  background: rgba(255, 255, 255, 0.8);
  position: absolute;
  font-size: 12px;
  right: 10px;
  bottom: 10px;
  padding: 2px 5px;
  border-radius: 3px;
}

.config-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  background: #f8f9ff;
  position: relative;
}

.header-icon {
  width: 37px;
  height: 37px;
  background: #5778ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon img {
  width: 19px;
  height: 19px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.custom-close-btn {
  position: absolute;
  top: 25%;
  right: 0;
  transform: translateY(-50%);
  width: 35px;
  height: 35px;
  border-radius: 50%;
  border: 2px solid #cfcfcf;
  background: none;
  font-size: 30px;
  font-weight: lighter;
  color: #cfcfcf;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  padding: 0;
  outline: none;
}

.custom-close-btn:hover {
  color: #409EFF;
  border-color: #409EFF;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.header-actions .save-btn {
  background: #5778ff;
  color: white;
  border: none;
  border-radius: 18px;
  padding: 8px 16px;
  height: 32px;
  font-size: 14px;
}

.header-actions .reset-btn {
  background: #e6ebff;
  color: #5778ff;
  border: 1px solid #adbdff;
  border-radius: 18px;
  padding: 8px 16px;
  height: 32px;
}

.header-actions .custom-close-btn {
  position: static;
  transform: none;
  width: 32px;
  height: 32px;
  margin-left: 8px;
}
</style>
