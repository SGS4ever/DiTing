# 谛听（DiTing）- 智能资讯聚合助手

谛听（DiTing）是一个基于Python的智能资讯聚合系统，它能够自动获取和处理多个RSS源的资讯，利用通义千问大模型生成每日新闻摘要，并通过邮件定时推送给用户。项目名称"谛听"源自佛教传说中的神兽，寓意着敏锐的洞察力和信息收集能力。

## 功能特性

- 多源RSS订阅内容自动聚合
- 基于规则的内容处理和过滤
- 使用通义千问大模型生成智能摘要
- 支持自定义时间的邮件定时推送
- 完善的日志记录系统
- 灵活的YAML配置管理

## 技术栈

- Python 3.8+
- python-dotenv：环境变量管理
- PyYAML：配置文件解析
- schedule：定时任务调度
- dashscope：通义千问API接口
- smtplib：邮件发送服务

## 快速开始

1. 克隆项目并安装依赖：
```bash
git clone [项目地址]
cd DiTing
pip install -r requirements.txt
```

2. 创建并配置环境变量文件：
```bash
cp .env.example .env
# 编辑.env文件，填入必要的环境变量
```

3. 配置系统：
   - 编辑 `config/config.yaml` 配置系统参数：
     - dashscope API密钥
     - 邮件服务器设置
     - 日志配置
     - 定时任务时间
   - 编辑 `config/sources.yaml` 配置RSS信息源

4. 运行服务：
```bash
python src/main.py
```

## 配置文件说明

### config.yaml 示例
```yaml
dashscope:
  api_key: "your-api-key"

email:
  smtp_server: "smtp.example.com"
  smtp_port: 587
  username: "your-email@example.com"
  password: "your-password"
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"

logging:
  level: "INFO"
  file: "logs/diting.log"

schedule:
  daily_report: "08:00"
```

### sources.yaml 示例
```yaml
sources:
  - name: "科技新闻"
    url: "http://example.com/rss"
    type: "text"
rules:
  keywords:
    include: ["技术", "创新"]
    exclude: ["广告", "推广"]
```

## 项目结构

```
DiTing/
├── src/
│   ├── __init__.py
│   ├── main.py          # 主程序入口
│   ├── rss_parser.py    # RSS解析模块
│   ├── content_processor.py  # 内容处理模块
│   ├── summarizer.py    # 摘要生成模块
│   └── mailer.py        # 邮件发送模块
├── config/
│   ├── config.yaml      # 系统配置
│   └── sources.yaml     # 信息源配置
├── logs/                # 日志目录
├── .env                 # 环境变量
├── requirements.txt     # 依赖清单
└── README.md
```

## 日志系统

系统使用Python的logging模块进行日志管理，所有操作日志都会被记录到配置文件指定的日志文件中，同时也会在控制台输出。日志级别可在配置文件中调整。 