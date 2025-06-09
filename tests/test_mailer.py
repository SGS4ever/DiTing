#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mailer import Mailer

class TestMailer(unittest.TestCase):
    """邮件发送功能测试"""
    
    def setUp(self):
        """测试前准备"""
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        # 测试配置
        self.test_config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@test.com',
            'password': 'test_password',
            'recipients': ['recipient1@test.com', 'recipient2@test.com'],
            'subject_template': '谛听日报 - {date}'
        }
        
        # 创建Mailer实例
        self.mailer = Mailer(self.test_config)
        
        # 测试内容
        self.test_content = """
## 科技新闻

1. 测试新闻标题1
   - 来源：测试来源1
   - 内容：测试内容1

2. 测试新闻标题2
   - 来源：测试来源2
   - 内容：测试内容2
"""
        
    def test_format_html_content(self):
        """测试HTML内容格式化"""
        formatted_content = self.mailer._format_html_content(self.test_content)
        
        # 验证基本结构
        self.assertIn('<!DOCTYPE html>', formatted_content)
        self.assertIn('<html>', formatted_content)
        self.assertIn('</html>', formatted_content)
        
        # 验证内容
        self.assertIn(self.test_content.strip(), formatted_content)
        self.assertIn('谛听日报', formatted_content)
        self.assertIn(datetime.now().strftime('%Y-%m-%d'), formatted_content)
        self.assertIn('本邮件由谛听自动生成发送', formatted_content)
        
    @patch('smtplib.SMTP')
    def test_send_daily_report(self, mock_smtp):
        """测试发送每日报告"""
        # 配置SMTP模拟对象
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # 执行测试
        result = self.mailer.send_daily_report(
            self.test_content,
            datetime.now().strftime('%Y-%m-%d')
        )
        
        # 验证SMTP调用
        self.assertTrue(result)
        mock_smtp.assert_called_once_with(
            self.test_config['smtp_server'],
            self.test_config['smtp_port']
        )
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with(
            self.test_config['username'],
            self.test_config['password']
        )
        mock_smtp_instance.send_message.assert_called_once()
        
    def test_attach_images(self):
        """测试图片附件添加"""
        from email.mime.multipart import MIMEMultipart
        
        # 创建临时图片目录和文件
        test_image_dir = 'media/images'
        os.makedirs(test_image_dir, exist_ok=True)
        
        test_images = {
            'test1.jpg': b'fake jpg data',
            'test2.png': b'fake png data',
            'test3.gif': b'fake gif data'
        }
        
        try:
            # 创建测试图片
            for filename, data in test_images.items():
                with open(os.path.join(test_image_dir, filename), 'wb') as f:
                    f.write(data)
            
            # 测试附件添加
            msg = MIMEMultipart('alternative')
            self.mailer._attach_images(msg)
            
            # 验证图片是否被添加
            attachments = [part for part in msg.walk() if part.get_content_type().startswith('image/')]
            self.assertEqual(len(attachments), len(test_images))
            
            # 验证每个图片的MIME类型
            mime_types = {
                '.jpg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif'
            }
            
            for attachment in attachments:
                filename = attachment.get_filename()
                ext = os.path.splitext(filename)[1].lower()
                self.assertEqual(attachment.get_content_type(), mime_types[ext])
            
        finally:
            # 清理测试文件
            for filename in test_images.keys():
                path = os.path.join(test_image_dir, filename)
                if os.path.exists(path):
                    os.remove(path)
            if os.path.exists(test_image_dir):
                os.rmdir(test_image_dir)
                
    def test_get_default_template(self):
        """测试默认模板获取"""
        template = self.mailer._get_default_template()
        
        # 验证模板结构
        self.assertIn('<!DOCTYPE html>', template)
        self.assertIn('<style>', template)
        self.assertIn('{content}', template)
        self.assertIn('{date}', template)
        self.assertIn('{footer_text}', template)
        
        # 验证基本样式
        self.assertIn('font-family', template)
        self.assertIn('line-height', template)
        self.assertIn('max-width', template)
        
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的SMTP配置
        invalid_config = self.test_config.copy()
        invalid_config['smtp_server'] = 'invalid.server'
        
        mailer = Mailer(invalid_config)
        result = mailer.send_daily_report(
            self.test_content,
            datetime.now().strftime('%Y-%m-%d')
        )
        
        self.assertFalse(result)
        
if __name__ == '__main__':
    unittest.main() 