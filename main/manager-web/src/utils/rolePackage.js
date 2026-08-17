export function validateRolePackage(role) {
  const configured = [
    role.roleCode,
    role.roleAssetVersion,
    role.roleAssetUrl,
    role.roleAssetSha256,
    role.roleWakeWord,
    role.roleWakeModel,
    role.roleWakeMode,
    role.roleWakeCommand,
    role.roleWakeLanguage,
  ].some((value) => typeof value === "string" && value.trim()) || Number(role.roleAssetSize) > 0;

  if (!configured) {
    return null;
  }
  if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test((role.roleCode || "").trim())) {
    return "角色标识只能使用小写字母、数字、下划线和短横线，且最长 64 位";
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test((role.roleAssetVersion || "").trim())) {
    return "资源版本只能使用字母、数字、点、下划线和短横线，且最长 64 位；内容变化时必须升级版本";
  }
  if (!/^[0-9a-f]{64}$/i.test((role.roleAssetSha256 || "").trim())) {
    return "角色资源 SHA-256 必须是 64 位十六进制字符串";
  }
  const size = Number(role.roleAssetSize);
  if (!Number.isInteger(size) || size <= 0 || size > 8 * 1024 * 1024) {
    return "角色资源包字节数必须在 1 到 8388608 之间";
  }
  if (!["public", "internal-only"].includes(role.roleDistribution)) {
    return "角色分发级别无效";
  }
  const wakeWord = (role.roleWakeWord || "").trim();
  const wakeModel = (role.roleWakeModel || "").trim();
  const wakeMode = (role.roleWakeMode || (wakeWord || wakeModel ? "trained" : "")).trim();
  const wakeCommand = (role.roleWakeCommand || "").trim().replace(/\s+/g, " ");
  const wakeLanguage = (role.roleWakeLanguage || "").trim();
  const wakeThreshold = role.roleWakeThreshold;
  const rawWakeVersion = role.roleWakeConfigVersion;
  const wakeVersion = Number(
    rawWakeVersion === null || rawWakeVersion === undefined || rawWakeVersion === ''
      ? (wakeWord ? 1 : 0)
      : rawWakeVersion,
  );
  if (Boolean(wakeWord) !== Boolean(wakeModel)) {
    return "唤醒短语和模型必须同时配置或同时清空";
  }
  if (wakeWord) {
    if ([...wakeWord].length > 32 || /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/u.test(wakeWord)) {
      return "唤醒短语最长 32 个字符，且不能包含控制字符";
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(wakeModel)) {
      return "唤醒模型标识只能使用字母、数字、点、下划线和短横线，且最长 96 位";
    }
    if (!["trained", "dynamic"].includes(wakeMode)) {
      return "唤醒模式只能是 trained 或 dynamic";
    }
    if (!Number.isSafeInteger(wakeVersion) || wakeVersion <= 0 || wakeVersion > 4294967295) {
      return "唤醒配置版本必须在 1 到 4294967295 之间";
    }
    if (wakeMode === "trained") {
      if (!wakeModel.startsWith("wn")) {
        return "trained 模式必须使用 WakeNet 模型";
      }
      const hasThreshold = wakeThreshold !== null && wakeThreshold !== undefined && wakeThreshold !== "";
      if (wakeCommand || wakeLanguage || hasThreshold) {
        return "trained 模式不能携带动态命令、语言或阈值";
      }
    } else {
      if (wakeModel !== "mn5q8_cn") {
        return "dynamic 模式当前只支持 mn5q8_cn 模型";
      }
      if (wakeLanguage !== "cn") {
        return "dynamic 模式当前只支持 cn 语言";
      }
      const commandPattern = /^[a-z]+(?: [a-z]+){2,7}$/;
      if (!commandPattern.test(wakeCommand) || wakeCommand.length > 160) {
        return "动态命令必须是 3 到 8 个小写拼音音节，不能包含数字或特殊字符";
      }
      const threshold = wakeThreshold === "" || wakeThreshold === null || wakeThreshold === undefined
        ? 0.2
        : Number(wakeThreshold);
      if (!Number.isFinite(threshold) || threshold < 0.05 || threshold > 0.95) {
        return "动态唤醒阈值必须在 0.050 到 0.950 之间";
      }
    }
  }
  try {
    const url = new URL(role.roleAssetUrl);
    if (!["http:", "https:"].includes(url.protocol) || !url.hostname || url.username || url.password) {
      return "角色资源包必须使用无账号信息的 HTTP(S) 绝对地址";
    }
  } catch (error) {
    return "角色资源包地址无效";
  }
  try {
    const theme = JSON.parse(role.roleThemeJson || "{}");
    if (!theme || Array.isArray(theme) || typeof theme !== "object") {
      return "角色主题必须是 JSON 对象";
    }
  } catch (error) {
    return "角色主题 JSON 格式无效";
  }
  return null;
}
