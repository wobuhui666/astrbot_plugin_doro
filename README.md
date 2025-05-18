# Doro 表情包插件

一个基于 [AstrBot](https://github.com/Astronmancer/astrbot) 的插件，用于获取随机的 Doro 表情包，并带有冷却限制，防止过于频繁调用 API。

## 📦 插件信息

- **名称**: doro
- **别名**: shingetsu
- **描述**: 随机 doro 表情包
- **版本**: 0.0.1

## ✨ 功能说明

本插件注册了一个指令 `/doro`，用于从 [https://www.doro.asia/api/random-sticker](https://www.doro.asia/api/random-sticker) 获取一张随机的 Doro 表情包图片，并发送至聊天中。

> 注意：该指令有 5 秒冷却时间，防止频繁请求 API。

## 🛠 安装方法

将插件文件放入 AstrBot 插件目录中（如 `plugins/`），AstrBot 会在启动时自动加载。

## 🧪 使用方法

### 指令列表

| 指令 | 描述 |
|------|------|
| `/doro` | 获取一张随机 Doro 表情包 |

## 🔧 示例效果

用户输入：
/doro

机器人回复：
- 一张图片（从 doro.asia 获取）

若冷却中则回复：
请稍等，距离下一次获取随机Doro表情包还有 X 秒。

## ⚠️ 注意事项

- 使用了 `httpx.AsyncClient` 进行异步 HTTP 请求。
- 对 API 请求做了错误处理，包括网络错误、状态码异常、API 返回失败等。
- 冷却机制基于 `time.time()` 实现，防止频繁触发请求。

## 📄 License

MIT（如未指定请自行补充）

---

欢迎提交 Issues 或 PR 来帮助改进本插件。
