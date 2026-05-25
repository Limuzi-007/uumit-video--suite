# 🎬 UUMit Video Suite

一站式 AI 视频剪辑 API 套装，上架 UUMit 市场按调用量赚钱。

## 🔧 9 大能力

| # | API | 说明 | 定价 (UT) |
|---|-----|------|-----------|
| 1 | **自动加字幕** | 上传视频 → 语音识别 → 生成 SRT/VTT 或直接嵌入 | 0.5/分钟 |
| 2 | **字幕翻译** | SRT 字幕 → 目标语言翻译 | 0.3/分钟 |
| 3 | **视频转文字** | 逐字稿 + 时间轴分段 | 0.3/分钟 |
| 4 | **去口播停顿** | 自动删除静音片段 | 0.5/分钟 |
| 5 | **高光提取** | 检测精彩片段 → 拼接精华视频 | 1.0/次 |
| 6 | **横转竖** | 9:16 / 4:5 / 1:1 竖屏裁剪 | 0.3/分钟 |
| 7 | **加水印/去水印** | 文字/图片水印 + AI 去水印 | 0.2/分钟 |
| 8 | **视频压缩** | H.264/H.265/VP9 压缩 | 0.3/分钟 |
| 9 | **视频拆帧** | 按帧率/间隔提取图片 | 0.2/百帧 |

## 🚀 快速部署

### 方案 A：Docker（推荐）

```bash
# 1. 克隆
git clone https://github.com/yourname/uumit-video-suite.git
cd uumit-video-suite

# 2. 配置
cp .env.example .env
# 编辑 .env 设置你的 API_KEYS

# 3. 启动
docker compose up -d

# 4. 验证
curl http://localhost:8000/health
```

### 方案 B：Render 一键部署

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork 这个仓库
2. 在 Render 创建 **Web Service**，连接你的 GitHub
3. 设置：
   - **Runtime**: Docker
   - **Env vars**: 复制 `.env.example` 内容
4. 部署 → 获取 `https://your-app.onrender.com`

### 方案 C：阿里云/腾讯云

```bash
# Ubuntu 24.04 实例
apt update && apt install -y docker.io docker-compose-v2
git clone https://github.com/yourname/uumit-video-suite.git
cd uumit-video-suite
docker compose up -d
```

## 📡 API 使用

### 生成字幕

```bash
curl -X POST https://your-api.com/v1/subtitle/generate \
  -H "Authorization: Bearer sk-your-key" \
  -F "file=@video.mp4" \
  -F "language=zh" \
  -F "srt_format=srt" \
  -F "burn_in=false"
```

### 视频转文字

```bash
curl -X POST https://your-api.com/v1/transcript \
  -H "Authorization: Bearer sk-your-key" \
  -F "file=@video.mp4" \
  -F "language=zh"
```

## 📤 上架 UUMit

### 方式 1：自动注册（推荐）

把下面这段话发给你的智能体（OpenClaw / Claude Code / Cursor）：

```
请阅读以下 Skill 描述文件，按照指引完成 UUMit 能力注册与上架：
https://oss.uumit.com/skills/SKILL.md

并按步骤完成：
1. 读取 Skill 描述文件
2. 帮我发起 UUMit 授权流程
3. 授权后获取授权码
```

### 方式 2：手动配置

参考 `uumit/agent-card.json`，在 UUMit 后台手动创建技能。

## 💰 盈利预期

按日均 1000 次调用估算：

| 能力 | 调用量/日 | UT/次 | 日收入 UT |
|------|----------|-------|----------|
| 加字幕 | 300 | 0.5 | 150 |
| 转文字 | 200 | 0.3 | 60 |
| 横转竖 | 150 | 0.3 | 45 |
| 去停顿 | 100 | 0.5 | 50 |
| 高光提取 | 80 | 1.0 | 80 |
| 加水印 | 70 | 0.2 | 14 |
| 压缩 | 60 | 0.3 | 18 |
| 拆帧 | 40 | 0.2 | 8 |
| **合计** | **1000** | | **425 UT/天** |

## 📋 项目结构

```
uumit-video-suite/
├── api/
│   ├── main.py          # 入口
│   ├── models.py        # 数据模型
│   ├── routers/         # 路由
│   │   ├── subtitle.py  # 字幕
│   │   ├── transcript.py# 转文字
│   │   ├── silence.py   # 去停顿
│   │   ├── highlight.py # 高光
│   │   ├── crop.py      # 横转竖
│   │   ├── watermark.py # 水印
│   │   ├── compress.py  # 压缩
│   │   └── frames.py    # 拆帧
│   ├── services/        # 业务逻辑
│   │   ├── ffmpeg_utils.py
│   │   ├── audio.py     # Whisper 语音识别
│   │   ├── video.py     # FFmpeg 视频处理
│   │   └── ai.py        # AI 翻译
│   └── utils/
│       ├── auth.py      # API Key 认证
│       └── file.py      # 文件处理
├── uumit/
│   └── agent-card.json  # UUMit 上架配置
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 📄 License

MIT
