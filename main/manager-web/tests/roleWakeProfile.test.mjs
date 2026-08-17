import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(
  new URL('../src/utils/rolePackage.js', import.meta.url),
  'utf8',
);
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const { validateRolePackage } = await import(moduleUrl);

function validRole(overrides = {}) {
  return {
    roleCode: 'pet_expert_shilang',
    roleThemeJson: '{}',
    roleAssetVersion: '2026.08.16.2',
    roleAssetUrl: 'https://assets.example/shilang.bin',
    roleAssetSha256: 'a'.repeat(64),
    roleAssetSize: 3_456_789,
    roleDistribution: 'public',
    roleWakeWord: '你好小智',
    roleWakeModel: 'wn9_nihaoxiaozhi_tts',
    roleWakeMode: 'trained',
    roleWakeCommand: '',
    roleWakeLanguage: '',
    roleWakeThreshold: null,
    roleWakeConfigVersion: 1,
    ...overrides,
  };
}

test('accepts a complete actual wake profile and legacy empty pair', () => {
  assert.equal(validateRolePackage(validRole()), null);
  assert.equal(validateRolePackage(validRole({
    roleWakeWord: '', roleWakeModel: '', roleWakeMode: '', roleWakeConfigVersion: null,
  })), null);
  assert.equal(validateRolePackage(validRole({
    roleWakeWord: '你好四郎',
    roleWakeModel: 'mn5q8_cn',
    roleWakeMode: 'dynamic',
    roleWakeCommand: 'ni hao si lang',
    roleWakeLanguage: 'cn',
    roleWakeThreshold: 0.2,
    roleWakeConfigVersion: 2,
  })), null);
});

test('rejects half configured or unsafe wake profiles', () => {
  assert.match(validateRolePackage(validRole({ roleWakeModel: '' })), /必须同时配置/);
  assert.match(validateRolePackage(validRole({ roleWakeWord: '' })), /必须同时配置/);
  assert.match(validateRolePackage(validRole({ roleWakeWord: '你好\n四郎' })), /控制字符/);
  assert.match(validateRolePackage(validRole({ roleWakeModel: 'bad model' })), /模型标识/);
  assert.match(validateRolePackage(validRole({
    roleWakeMode: 'dynamic', roleWakeModel: 'wn9_test', roleWakeCommand: 'ni hao si lang',
    roleWakeLanguage: 'cn', roleWakeThreshold: 0.2,
  })), /mn5q8_cn/);
  assert.match(validateRolePackage(validRole({
    roleWakeMode: 'dynamic', roleWakeModel: 'mn5q8_cn', roleWakeCommand: 'Hey 起司',
    roleWakeLanguage: 'cn', roleWakeThreshold: 0.2,
  })), /小写拼音/);
  assert.match(validateRolePackage(validRole({
    roleWakeMode: 'dynamic', roleWakeModel: 'mn5q8_en', roleWakeCommand: 'hey cheese now',
    roleWakeLanguage: 'en', roleWakeThreshold: 0.2,
  })), /mn5q8_cn/);
  assert.equal(validateRolePackage(validRole({ roleWakeConfigVersion: 4294967295 })), null);
  assert.match(validateRolePackage(validRole({ roleWakeConfigVersion: 4294967296 })), /4294967295/);
  assert.match(validateRolePackage(validRole({ roleWakeConfigVersion: 0 })), /4294967295/);
});
