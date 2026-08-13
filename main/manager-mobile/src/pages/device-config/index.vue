<script setup lang="ts">
import { onMounted } from 'vue'
import { t } from '@/i18n'

function showProvisionTips() {
  uni.showModal({
    title: t('deviceConfig.provisionTipsTitle'),
    content: t('deviceConfig.provisionTipsContent'),
    showCancel: false,
  })
}

function goBindPage() {
  uni.navigateTo({
    url: '/pages/device/index',
  })
}

onMounted(() => {
  uni.setNavigationBarTitle({
    title: t('deviceConfig.pageTitle'),
  })
})
</script>

<template>
  <view class="min-h-screen bg-[#f5f7fb]">
    <wd-navbar :title="t('deviceConfig.pageTitle')" safe-area-inset-top />

    <view class="box-border px-[20rpx] py-[20rpx]">
      <view class="mb-[24rpx] border border-[#eeeeee] rounded-[20rpx] bg-[#fbfbfb] p-[24rpx]">
        <view class="text-[32rpx] text-[#232338] font-bold">
          {{ t('deviceConfig.initializationFlowTitle') }}
        </view>
        <view class="mt-[20rpx] flex flex-col gap-[12rpx] text-[26rpx] text-[#65686f] leading-[1.6]">
          <text>{{ t('deviceConfig.initializationStep1') }}</text>
          <text>{{ t('deviceConfig.initializationStep2') }}</text>
          <text>{{ t('deviceConfig.initializationStep3') }}</text>
          <text>{{ t('deviceConfig.initializationStep4') }}</text>
        </view>
      </view>

      <view class="mb-[24rpx] border border-[#eeeeee] rounded-[20rpx] bg-[#fbfbfb] p-[24rpx]">
        <view class="text-[28rpx] text-[#232338] font-medium">
          {{ t('deviceConfig.initializationNoteTitle') }}
        </view>
        <view class="mt-[12rpx] text-[24rpx] text-[#65686f] leading-[1.6]">
          {{ t('deviceConfig.initializationNote') }}
        </view>
      </view>

      <view class="flex flex-col gap-[16rpx]">
        <wd-button type="info" size="large" block @click="showProvisionTips">
          {{ t('deviceConfig.viewSystemProvisioning') }}
        </wd-button>
        <wd-button type="primary" size="large" block @click="goBindPage">
          {{ t('deviceConfig.goToDeviceBinding') }}
        </wd-button>
      </view>
    </view>
  </view>
</template>

<route lang="jsonc" type="page">
{
  "style": {
    "navigationBarTitleText": "",
    "navigationStyle": "custom"
  }
}
</route>
