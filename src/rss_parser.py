#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import logging
from datetime import datetime
import requests
from typing import Dict, List, Any

class RSSParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析RSS源
        
        Args:
            source: RSS源配置信息
            
        Returns:
            解析后的新闻列表
        """
        try:
            self.logger.info(f"开始解析RSS源: {source['name']}")
            
            # 获取RSS内容
            response = requests.get(source['url'], timeout=30)
            feed = feedparser.parse(response.content)
            
            # 处理每个条目
            news_items = []
            for entry in feed.entries:
                try:
                    item = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'description': entry.get('description', ''),
                        'content': entry.get('content', [{}])[0].get('value', entry.get('description', '')),
                        'published': self._parse_date(entry.get('published', '')),
                        'source_name': source['name'],
                        'source_type': source['type'],
                        'category': source.get('category', 'general'),
                        'media': self._extract_media(entry)
                    }
                    news_items.append(item)
                except Exception as e:
                    self.logger.error(f"处理RSS条目时出错: {str(e)}")
                    continue
            
            self.logger.info(f"RSS源 {source['name']} 解析完成，共获取 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            self.logger.error(f"解析RSS源 {source['name']} 时发生错误: {str(e)}")
            return []
            
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            return datetime(*feedparser._parse_date(date_str)[:6])
        except:
            return datetime.now()
            
    def _extract_media(self, entry: Dict[str, Any]) -> Dict[str, List[str]]:
        """提取媒体内容"""
        media = {
            'images': [],
            'videos': []
        }
        
        # 提取封面图片
        if hasattr(entry, 'media_content'):
            for content in entry.media_content:
                if content.get('type', '').startswith('image/'):
                    media['images'].append(content['url'])
                elif content.get('type', '').startswith('video/'):
                    media['videos'].append(content['url'])
                    
        # 提取文章中的图片
        if hasattr(entry, 'media_thumbnail'):
            for thumbnail in entry.media_thumbnail:
                if 'url' in thumbnail:
                    media['images'].append(thumbnail['url'])
                    
        # 从内容中提取图片URL
        if 'content' in entry and entry.content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(entry.content[0].value, 'html.parser')
            for img in soup.find_all('img'):
                if img.get('src'):
                    media['images'].append(img['src'])
                    
        return media 