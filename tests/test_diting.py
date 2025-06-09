#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import yaml
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

# 导入主要类
from src.main import DiTing
from src.rss_parser import RSSParser
from src.content_processor import ContentProcessor
from src.summarizer import Summarizer
from src.mailer import Mailer

class TestDiTing(unittest.TestCase):
    def setUp(self):
        """测试前准备工作"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        self.sources_path = os.path.join(self.temp_dir, 'sources.yaml')
        
        # 创建测试配置
        self.test_config = {
            'email': {
                'smtp_server': 'test.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'test_password',
                'recipients': ['recipient@example.com'],
                'subject_template': '谛听日报 - {date}'
            },
            'dashscope': {
                'api_key': 'test_api_key'
            },
            'schedule': {
                'daily_report': '08:00'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/test.log'
            }
        }
        
        self.test_sources = {
            'sources': [
                {
                    'name': '测试RSS源',
                    'url': 'http://test.com/rss',
                    'type': 'text',
                    'category': 'test'
                }
            ],
            'rules': {
                'content_filters': [
                    {'pattern': '广告', 'action': 'exclude'}
                ],
                'content_extractors': {
                    'title': {'max_length': 100},
                    'summary': {'max_length': 500}
                },
                'image_processing': {
                    'max_width': 800,
                    'max_height': 600,
                    'format': 'JPEG',
                    'quality': 85
                }
            }
        }
        
        # 写入测试配置文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_config, f)
        with open(self.sources_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.test_sources, f)
            
    def tearDown(self):
        """测试后清理工作"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    @patch('src.rss_parser.requests.get')
    @patch('src.summarizer.Generation.call')
    @patch('src.mailer.smtplib.SMTP')
    def test_end_to_end(self, mock_smtp, mock_generation, mock_requests):
        """端到端测试"""
        # 模拟RSS响应
        mock_requests.return_value.content = """
        <?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
            <title>测试RSS</title>
            <item>
                <title>测试新闻标题</title>
                <link>http://test.com/news/1</link>
                <description>这是一条测试新闻</description>
                <pubDate>Thu, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
        </rss>
        """
        
        # 模拟通义千问API响应
        mock_generation.return_value = MagicMock(
            status_code=200,
            output=MagicMock(text="## 测试分类\n\n这是测试摘要内容")
        )
        
        # 模拟SMTP服务器
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # 创建DiTing实例并运行
        diting = DiTing()
        diting.process_daily_news()
        
        # 验证是否调用了所有必要的服务
        mock_requests.assert_called()
        mock_generation.assert_called()
        mock_smtp_instance.send_message.assert_called()
        
    def test_rss_parser(self):
        """测试RSS解析器"""
        parser = RSSParser()
        source = self.test_sources['sources'][0]
        
        with patch('src.rss_parser.requests.get') as mock_get:
            mock_get.return_value.content = """
            <?xml version="1.0" encoding="UTF-8" ?>
            <rss version="2.0">
            <channel>
                <title>测试RSS</title>
                <item>
                    <title>测试新闻标题</title>
                    <link>http://test.com/news/1</link>
                    <description>这是一条测试新闻</description>
                    <pubDate>Thu, 01 Jan 2024 00:00:00 GMT</pubDate>
                </item>
            </channel>
            </rss>
            """
            
            news_items = parser.parse(source)
            self.assertEqual(len(news_items), 1)
            self.assertEqual(news_items[0]['title'], '测试新闻标题')
            
    def test_content_processor(self):
        """测试内容处理器"""
        processor = ContentProcessor()
        items = [{
            'title': '测试标题'*20,  # 超过最大长度
            'content': '测试内容'*100,  # 超过最大长度
            'media': {'images': [], 'videos': []}
        }]
        
        processed_items = processor.process(
            items,
            'text',
            self.test_sources['rules']
        )
        
        self.assertEqual(len(processed_items), 1)
        self.assertLessEqual(
            len(processed_items[0]['title']),
            self.test_sources['rules']['content_extractors']['title']['max_length']
        )
        
    def test_summarizer(self):
        """测试摘要生成器"""
        summarizer = Summarizer('test_api_key')
        news_items = [{
            'title': '测试新闻',
            'content': '测试内容',
            'source_name': '测试源',
            'category': 'test',
            'media': {'images': [], 'videos': []}
        }]
        
        with patch('src.summarizer.Generation.call') as mock_call:
            mock_call.return_value = MagicMock(
                status_code=200,
                output=MagicMock(text="测试摘要")
            )
            
            summary = summarizer.generate_summary(news_items)
            self.assertIsNotNone(summary)
            mock_call.assert_called_once()
            
    def test_mailer(self):
        """测试邮件发送器"""
        mailer = Mailer(self.test_config['email'])
        content = "测试邮件内容"
        date = datetime.now().strftime('%Y-%m-%d')
        
        with patch('src.mailer.smtplib.SMTP') as mock_smtp:
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
            
            success = mailer.send_daily_report(content, date)
            self.assertTrue(success)
            mock_smtp_instance.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main() 