# 舆情审核AI机器人 (AI-Opinion-Audit)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-green.svg)](https://deepseek.com/)
[![飞书](https://img.shields.io/badge/飞书-Webhook-orange.svg)](https://open.feishu.cn/)
[![DailyHotApi](https://img.shields.io/badge/DailyHotApi-多平台-purple.svg)](https://github.com/imsyy/DailyHotApi)

> 基于 DeepSeek 大模型的全网热点监控与智能审核系统，支持微博、知乎、B站、抖音、贴吧、澎湃新闻、新浪新闻等多个平台，实现三级自动预警（红/黄/绿），实时推送至飞书。

---

## 🎯 项目背景

面对海量的社交媒体信息，人工舆情监控效率低、响应慢、审核标准不统一。本项目通过 **关键词规则 + AI 大模型判断** 的方式，实现舆情的自动化识别、分级预警和审核标准生成，帮助审核团队快速响应风险事件。

---

## ✨ 核心功能

| 预警级别 | 触发条件 | 功能说明 |
|:---:|---------|----------|
| 🔴 **红色警报** | 命中 `RED_KEYWORDS` 关键词（如地震、火灾、爆炸、举报等） | 判断是否为境外事件：<br>• **境外** → 推送“境外新闻，不进行审核”<br>• **国内** → 生成 **“通过/拦截/人工复核”** 三档审核标准，推送飞书 |
| 🟡 **黄色警报** | 命中 `YELLOW_PEOPLE` 人物名单 | 轻量级提醒，推送事件标题和热度值，用于公众人物舆情追踪 |
| 🟢 **绿色警报** | 到达 `GREEN_DATES` 设定日期前后 3 天 | 自动计算倒计时/已过天数，每日推送一次，用于重要日期提醒 |

---

## 📊 支持平台

| 平台 | 路由名 | 说明 |
|------|--------|------|
| 知乎 | `zhihu` | 知乎热榜 |
| B站 | `bilibili` | B站热门 |
| 抖音 | `douyin` | 抖音热点 |
| 百度贴吧 | `tieba` | 贴吧热议 |
| 澎湃新闻 | `thepaper` | 澎湃新闻热榜 |
| 新浪新闻 | `sina-news` | 新浪新闻热榜 |
| 微博（备用） | `weibo` | 原有接口，作为降级备用 |

> 可根据需要增删平台，修改 `PLATFORMS` 列表即可。

---

## ⚙️ 技术特色

- **多平台聚合**：接入 DailyHotApi，支持 60+ 平台热点数据
- **关键词热加载**：修改 `config.json` 即可更新关键词，无需重启服务
- **3 天去重机制**：红/黄警报 3 天内不重复推送，避免消息轰炸
- **智能地域识别**：AI 判断是否为境外事件，**境外不审核，节省 API 调用**
- **日志自动轮转**：按天分割，保留 30 天，错误日志独立存储
- **7×24 小时运行**：部署于云服务器（Ubuntu + systemd），异常自动重启

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.10 | 主开发语言 |
| DeepSeek API | 大模型推理（审核标准生成 + 地域判断） |
| DailyHotApi | 多平台热点数据聚合 |
| 飞书 Webhook | 消息推送 |
| schedule | 定时任务调度 |
| systemd | 服务守护（开机自启 + 崩溃重启） |
| TimedRotatingFileHandler | 日志分割与自动清理 |

---

## 📁 项目结构

```
shenhe-bot/
├── SHbot.py                 # 主程序
├── config.json.example      # 配置文件示例（复制为 config.json 后使用）
├── .env.example             # 环境变量示例（复制为 .env 后使用）
├── requirements.txt         # Python 依赖
├── .gitignore               # Git 忽略文件
└── README.md                # 项目说明
```

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/hxgame2002-coder/Al-opinion-audit.git
cd Al-opinion-audit
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 部署 DailyHotApi（多平台数据源）

```bash
docker run --restart always -p 6688:6688 -d imsyy/dailyhot-api:latest
```

验证：`curl http://localhost:6688/zhihu`

### 4. 配置密钥

复制示例文件并填入真实密钥：

```bash
cp .env.example .env
cp config.json.example config.json
```

#### `.env` 文件（必填）

```env
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/你的hook
JIEKOU_ID=你的接口ID
JIEKOU_KEY=你的接口KEY
DEEPSEEK_API_KEY=sk-你的DeepSeek密钥
```

#### `config.json` 文件（必填）

```json
{
    "RED_KEYWORDS": ["地震", "火灾", "爆炸", "举报"],
    "YELLOW_PEOPLE": ["张三", "李四"],
    "GREEN_DATES": ["2026-10-01", "2027-01-01"]
}
```

### 5. 运行程序

```bash
python SHbot.py
```

### 6. 部署到云服务器（可选）

```bash
# 上传文件到 /opt/shenhe-bot/
# 配置 systemd 服务
sudo systemctl enable shenhe-bot
sudo systemctl start shenhe-bot
```

---

## 📊 效果演示

| 警报类型 | 飞书推送示例 |
|---------|-------------|
| 🔴 红色（境外） | `🔴 红色警报【境外新闻】` + 事件标题 + `🌍 境外事件，不进行内容审核` |
| 🔴 红色（国内） | `🔴 红色警报【舆情动态】` + 事件标题 + AI审核标准（通过/拦截/人工复核） |
| 🟡 黄色 | `🟡 黄色警报【舆情动态】` + 事件标题 + 热度值 |
| 🟢 绿色 | `🟢 绿色警报【日期提醒】` + 倒计时/已过天数 |

---

## 📌 配置说明

| 配置文件 | 用途 | 是否上传 Git |
|---------|------|:---:|
| `.env` | 存储密钥（飞书 Webhook、DeepSeek Key 等） | ❌ |
| `config.json` | 存储关键词、人名、日期列表 | ❌ |
| `.env.example` | 密钥模板，供用户参考 | ✅ |
| `config.json.example` | 配置模板，供用户参考 | ✅ |

---

## 🔧 平台列表配置

在 `SHbot.py` 中修改 `PLATFORMS` 列表即可增删平台：

```python
PLATFORMS = ["zhihu", "bilibili", "douyin", "tieba", "thepaper", "sina-news"]
```

---

## 📝 维护指南

### 修改关键词

1. 用 WinSCP（或 nano）打开 `/opt/shenhe-bot/config.json`
2. 在 `RED_KEYWORDS` 列表中增删改关键词
3. 保存文件，**无需重启服务**（热加载自动生效）

### 查看日志

```bash
tail -f /opt/shenhe-bot/bot.log     # 主日志
tail -f /opt/shenhe-bot/error.log   # 错误日志
```

---

## 👤 作者

**hxgame2002-coder**

- GitHub: [hxgame2002-coder](https://github.com/hxgame2002-coder)
- 项目链接: [Al-opinion-audit](https://github.com/hxgame2002-coder/Al-opinion-audit)

---

## 📄 许可证

本项目仅供学习交流使用，未经授权不得用于商业用途。

---

## 🙏 致谢

- [DeepSeek](https://deepseek.com/) 提供大模型 API
- [飞书](https://open.feishu.cn/) 提供 Webhook 推送能力
- [DailyHotApi](https://github.com/imsyy/DailyHotApi) 提供多平台热点数据聚合
- [接口盒子](https://cn.apihz.cn/) 提供微博热点数据（备用）