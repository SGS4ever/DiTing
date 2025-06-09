# 谛听（DiTing）- 智能资讯聚合助手

谛听是一个智能资讯聚合系统，能够自动获取多个来源的资讯，并使用AI技术生成摘要，通过邮件定时推送给用户。

## 功能特性

- 自动获取多源RSS订阅内容
- 支持文本、图片、视频等多媒体内容
- 使用通义大模型生成智能摘要
- 邮件定时推送
- 灵活的信息源配置

## 技术栈

- Python 3.8+
- feedparser：RSS解析
- Pillow：图像处理
- moviepy：视频处理
- schedule：定时任务
- smtplib：邮件发送
- dashscope：通义千问API

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置信息源：
编辑 `config/sources.yaml` 文件，添加您需要订阅的RSS源。

3. 配置邮件和API：
编辑 `config/config.yaml` 文件，设置邮件服务器信息和通义千问API密钥。

4. 运行服务：
```bash
python src/main.py
```

## 配置说明

### RSS源配置示例
```yaml
sources:
  - name: "科技新闻"
    url: "http://example.com/rss"
    type: "text"
  - name: "图片新闻"
    url: "http://example.com/photo/rss"
    type: "image"
```

### 邮件配置示例
```yaml
email:
  smtp_server: "smtp.example.com"
  smtp_port: 587
  username: "your-email@example.com"
  password: "your-password"
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"
```

## 项目结构

```
DiTing/
├── src/
│   ├── main.py
│   ├── rss_parser.py
│   ├── content_processor.py
│   ├── summarizer.py
│   └── mailer.py
├── config/
│   ├── config.yaml
│   └── sources.yaml
├── tests/
│   └── test_*.py
├── requirements.txt
└── README.md
``` 