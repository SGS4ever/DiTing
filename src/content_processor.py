#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
from typing import Dict, List, Any
from PIL import Image
import requests
from io import BytesIO
import os
from bs4 import BeautifulSoup

class ContentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process(self, items: List[Dict[str, Any]], content_type: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理新闻内容
        
        Args:
            items: 新闻列表
            content_type: 内容类型 (text/image/video)
            rules: 处理规则
            
        Returns:
            处理后的新闻列表
        """
        processed_items = []
        
        for item in items:
            try:
                # 应用内容过滤规则
                if self._should_filter(item, rules['content_filters']):
                    continue
                    
                # 处理文本内容
                if 'content' in item:
                    item['content'] = self._process_text(
                        item['content'],
                        rules['content_extractors']
                    )
                    
                # 处理标题
                if 'title' in item:
                    item['title'] = self._process_text(
                        item['title'],
                        rules['content_extractors'],
                        is_title=True
                    )
                    
                # 处理媒体内容
                if content_type in ['image', 'video']:
                    item['media'] = self._process_media(
                        item['media'],
                        rules['image_processing']
                    )
                    
                processed_items.append(item)
                
            except Exception as e:
                self.logger.error(f"处理新闻内容时出错: {str(e)}")
                continue
                
        return processed_items
        
    def _should_filter(self, item: Dict[str, Any], filters: List[Dict[str, str]]) -> bool:
        """检查是否应该过滤掉该内容"""
        for filter_rule in filters:
            pattern = filter_rule['pattern']
            if (pattern in item.get('title', '') or
                pattern in item.get('content', '')):
                return True
        return False
        
    def _process_text(self, text: str, rules: Dict[str, Dict[str, int]], is_title: bool = False) -> str:
        """处理文本内容"""
        if not text:
            return text
            
        # 清理HTML标签
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 截断文本
        max_length = rules['title']['max_length'] if is_title else rules['summary']['max_length']
        if len(text) > max_length:
            text = text[:max_length] + '...'
            
        return text
        
    def _process_media(self, media: Dict[str, List[str]], rules: Dict[str, Any]) -> Dict[str, List[str]]:
        """处理媒体内容"""
        processed_media = {
            'images': [],
            'videos': media['videos']  # 视频暂时不做处理
        }
        
        # 处理图片
        for img_url in media['images']:
            try:
                # 下载图片
                response = requests.get(img_url, timeout=30)
                img = Image.open(BytesIO(response.content))
                
                # 调整大小
                if img.width > rules['max_width'] or img.height > rules['max_height']:
                    img.thumbnail((rules['max_width'], rules['max_height']))
                    
                # 转换格式
                if img.format != rules['format']:
                    img = img.convert('RGB')
                    
                # 保存处理后的图片
                output_dir = 'media/images'
                os.makedirs(output_dir, exist_ok=True)
                
                filename = f"{hash(img_url)}.{rules['format'].lower()}"
                output_path = os.path.join(output_dir, filename)
                
                img.save(output_path, rules['format'], quality=rules['quality'])
                processed_media['images'].append(output_path)
                
            except Exception as e:
                self.logger.error(f"处理图片时出错: {str(e)}")
                continue
                
        return processed_media 