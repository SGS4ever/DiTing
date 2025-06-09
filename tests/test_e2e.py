#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import yaml
from datetime import datetime
from src.main import DiTing

class TestDiTingE2E(unittest.TestCase):
    """谛听端到端测试"""
    
    def setUp(self):
        """测试前准备工作"""
        # 使用实际的配置文件
        self.config_path = os.path.join('config', 'config.yaml')
        self.sources_path = os.path.join('config', 'sources.yaml')
        
        # 确保配置文件存在
        self.assertTrue(os.path.exists(self.config_path), "配置文件不存在")
        self.assertTrue(os.path.exists(self.sources_path), "RSS源配置文件不存在")
        
        # 加载配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        with open(self.sources_path, 'r', encoding='utf-8') as f:
            self.sources = yaml.safe_load(f)
            
        # 验证关键配置
        self.assertIn('email', self.config, "缺少邮件配置")
        self.assertIn('dashscope', self.config, "缺少通义千问API配置")
        self.assertIn('sources', self.sources, "缺少RSS源配置")
        
    def test_process_daily_news(self):
        """测试每日新闻处理流程
        
        这个测试将：
        1. 初始化谛听实例
        2. 获取并处理RSS源内容
        3. 生成摘要
        4. 发送邮件
        5. 验证整个流程
        """
        try:
            # 初始化谛听实例
            diting = DiTing()
            
            # 执行每日新闻处理
            diting.process_daily_news()
            
            # 检查日志文件是否生成
            log_file = self.config['logging']['file']
            self.assertTrue(os.path.exists(log_file), "日志文件未生成")
            
            # 检查日志内容
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            # 验证关键流程是否执行
            self.assertIn("开始处理每日新闻", log_content, "未开始处理新闻")
            self.assertIn("每日报告发送成功", log_content, "邮件发送失败")
            
            # 检查是否生成了媒体文件
            media_dir = 'media/images'
            if os.path.exists(media_dir):
                images = [f for f in os.listdir(media_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                print(f"处理的图片数量: {len(images)}")
            
        except Exception as e:
            self.fail(f"端到端测试失败: {str(e)}")

    def tearDown(self):
        """测试后清理工作"""
        # 清理测试过程中生成的媒体文件
        media_dir = 'media/images'
        if os.path.exists(media_dir):
            for file in os.listdir(media_dir):
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        os.remove(os.path.join(media_dir, file))
                    except:
                        pass

if __name__ == '__main__':
    # 设置更详细的测试输出
    unittest.main(verbosity=2) 