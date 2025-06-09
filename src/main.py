#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import schedule
import time
from datetime import datetime
import yaml
from dotenv import load_dotenv

from src.rss_parser import RSSParser
from src.content_processor import ContentProcessor
from src.summarizer import Summarizer
from src.mailer import Mailer

# 加载环境变量
load_dotenv()

class DiTing:
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
        
        # 初始化组件
        self.rss_parser = RSSParser()
        self.content_processor = ContentProcessor()
        self.summarizer = Summarizer(self.config['dashscope']['api_key'])
        self.mailer = Mailer(self.config['email'])
        
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join('config', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config['logging']
        os.makedirs(os.path.dirname(log_config['file']), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def process_daily_news(self):
        """处理每日新闻"""
        try:
            self.logger.info("开始处理每日新闻")
            
            # 获取RSS源配置
            sources_path = os.path.join('config', 'sources.yaml')
            with open(sources_path, 'r', encoding='utf-8') as f:
                sources_config = yaml.safe_load(f)
            
            # 获取所有新闻
            all_news = []
            for source in sources_config['sources']:
                try:
                    news_items = self.rss_parser.parse(source)
                    processed_items = self.content_processor.process(
                        news_items,
                        source['type'],
                        sources_config['rules']
                    )
                    all_news.extend(processed_items)
                except Exception as e:
                    self.logger.error(f"处理源 {source['name']} 时出错: {str(e)}")
            
            # 生成摘要
            summary = self.summarizer.generate_summary(all_news)
            
            # 发送邮件
            date_str = datetime.now().strftime('%Y-%m-%d')
            self.mailer.send_daily_report(summary, date_str)
            
            self.logger.info("每日新闻处理完成")
            
        except Exception as e:
            self.logger.error(f"处理每日新闻时发生错误: {str(e)}")
            
    def run(self):
        """运行服务"""
        # 设置定时任务
        schedule_time = self.config['schedule']['daily_report']
        schedule.every().day.at(schedule_time).do(self.process_daily_news)
        
        self.logger.info(f"谛听服务已启动，将在每天 {schedule_time} 推送资讯摘要")
        
        # 立即执行一次
        self.process_daily_news()
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    diting = DiTing()
    diting.run() 