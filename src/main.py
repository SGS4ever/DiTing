#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import schedule
import time
from datetime import datetime
import yaml
from dotenv import load_dotenv
import argparse
import sys

from .rss_parser import RSSParser
from .content_processor import ContentProcessor
from .summarizer import Summarizer
from .mailer import Mailer

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
            raise  # 重新抛出异常，确保错误状态能被捕获
            
    def run_service(self):
        """以服务模式运行（用于systemd）"""
        # 设置定时任务
        schedule_time = self.config['schedule']['daily_report']
        schedule.every().day.at(schedule_time).do(self.process_daily_news)
        
        self.logger.info(f"谛听服务已启动，将在每天 {schedule_time} 推送资讯摘要")
        
        # 立即执行一次
        try:
            self.process_daily_news()
        except Exception as e:
            self.logger.error(f"初始执行失败: {str(e)}")
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    def run_once(self):
        """执行一次任务（用于crontab）"""
        self.logger.info("开始执行单次任务")
        try:
            self.process_daily_news()
            self.logger.info("单次任务执行完成")
            return True
        except Exception as e:
            self.logger.error(f"单次任务执行失败: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='DiTing RSS聚合器')
    parser.add_argument('--mode', choices=['service', 'once'], default='once',
                      help='运行模式：service（服务模式）或once（单次执行）')
    args = parser.parse_args()
    
    try:
        diting = DiTing()
        if args.mode == 'service':
            diting.run_service()
        else:
            success = diting.run_once()
            sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"程序执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
