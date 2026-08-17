# 宠业家四郎 MCP 与插件审计（2026-08-18）

## 结论

- PolarSearch 已仅绑定到 `pet_expert_shilang`，本机 Retrieval Runtime 健康，真实函数调用可返回内部商品与公开知识结果。
- 当前没有启用任何服务端远程 MCP：运行时缺少 `data/.mcp_server_settings.json`。现有能力主要来自 12 个服务端函数插件和 8 个设备端 MCP 工具。
- 联网搜索、天气、导航的推荐组合是百炼 WebSearch MCP + 百炼托管 Amap Maps MCP。两者复用现有百炼通用 API Key；Amap Maps 试用不要求另填高德 Key。
- 当前百炼 Key 对两个 Streamable HTTP 地址的初始化探测均返回 HTTP 405。官方故障说明把“未开通或未升级”列为首要原因，因此在百炼 MCP 广场完成一次开通/升级前不应写入运行配置，以免每次设备连接增加超时。
- 现有秘塔和和风天气插件不应继续作为默认路径：秘塔探测返回供应商错误码 `2005`，而现代码会把它误报为“未找到”；和风天气在真实设备连接时返回鉴权失败。

## 当前运行能力

| 能力 | 类型 | 当前状态 | 新账号/Key | 费用判断 | 处置 |
|---|---|---|---|---|---|
| PolarSearch | 智能体函数插件 | 已绑定四郎，Runtime healthy，真实检索通过 | 不需要，复用现有 CYJ 数据凭据 | 现有阿里云检索与模型资源成本 | 保留 |
| 秘塔联网搜索 | 智能体函数插件 | 已配置但供应商返回 `errCode=2005`；代码还使用旧响应契约 | 需要独立秘塔账号/Key | 供应商计费 | 百炼 WebSearch 可用后替换 |
| 和风天气 | 智能体函数插件 | 已配置但运行态返回 Authentication failed | 需要独立和风账号/Key/Host | 有免费额度和付费档，仍需单独开户 | 用 Amap Maps 天气替换 |
| 中国新闻网 RSS | 智能体函数插件 | HTTP 200 | 不需要 | 免费 | 保留为新闻兜底 |
| NewsNow | 智能体函数插件 | 当前端点 HTTP 403 | 不需要 | 免费 | 停用或更换可达源 |
| Home Assistant | 智能体函数插件 | 容器无法解析 `homeassistant.local` | 需要本地 HA 长期令牌，不需要第三方付费账号 | 自托管成本 | 待有 HA 可达地址后恢复 |
| 本地音乐、退出、农历 | 本地函数 | 可注册 | 不需要 | 免费；音乐内容另受版权与资源约束 | 保留 |
| 设备状态、音量、亮度、角色、Wi-Fi | 设备 MCP | 设备上报 8 个工具 | 不需要 | 免费 | 保留 |
| 服务端远程 MCP | 标准 MCP | 当前 0 个 | 视供应商而定 | 视供应商而定 | 等百炼服务开通后启用 |

## 推荐接入顺序

1. 在百炼 MCP 广场开通或升级 WebSearch MCP。
2. 在同一广场开通 Amap Maps MCP；先使用百炼托管试用，不申请独立高德 Key。
3. 通过 `authorization_token_file` 从只读 Docker 密钥卷加载现有百炼通用 API Key，不把 Key 写入 `.mcp_server_settings.json`。
4. 先做工具列表与无计费连接验收，再各做一次联网、天气和路线小流量调用。
5. 验收通过后从四郎配置中移除和风天气与秘塔搜索，避免模型选择到坏工具。

## 平台选择

- 百炼优先：当前主 LLM 已使用百炼通用 API Key，WebSearch 和 Amap Maps 都能在同一账号完成；接入路径最短。
- 火山作为备选：火山方舟有联网内容插件，但语音 TTS 2.0 Key 不等于方舟模型 Key。虽然可以复用现有火山账号，仍可能需要开通方舟服务并创建方舟 Key，不如百炼直接。
- 不推荐新增 Tavily、直接高德或新的天气供应商账号：都会增加独立注册、Key 和账单管理。

## 验证记录

- Retrieval Runtime：容器健康、零重启；四郎私有配置包含 `retrieve_from_cyjdata`，真实函数调用成功。
- MCP 密钥边界：`authorization_token_file` 的 3 项安全测试通过；现有百炼 Key 已进入只读 `xiaozhi-mcp-secrets` 卷并完成容器可读性验证，未写入仓库或 JSON。
- 百炼 WebSearch/Amap Maps：现有通用 Key、正确 Endpoint、MCP initialize 探测均为 HTTP 405；未产生工具调用费用。
- 秘塔：一次最小结果探测 HTTP 200，但正文仅有 `errCode/errMsg`，`errCode=2005`。
- 和风天气：设备连接初始化时返回 `Authentication failed, check your KEY/Token or Host.`。
- 中国新闻网 RSS：HTTP 200；NewsNow：HTTP 403；Home Assistant：容器 DNS 解析失败。

## 参考

- 百炼 WebSearch MCP：https://help.aliyun.com/zh/model-studio/web-search-for-coding-plan
- 百炼外部调用 MCP（含 Amap Maps）：https://help.aliyun.com/zh/model-studio/mcp-external-calls
- 火山方舟联网内容插件：https://docs.volcengine.com/docs/82379/1359519?lang=zh
