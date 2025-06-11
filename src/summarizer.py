#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import requests
import sys
from typing import Dict, List, Any
import markdown2  # 添加markdown转换库

# 检查Python版本
PY_VERSION = sys.version_info
USE_DASHSCOPE_SDK = PY_VERSION >= (3, 8)

# 初始化变量
DASHSCOPE_IMPORT_ERROR = None

# 根据Python版本导入dashscope
if USE_DASHSCOPE_SDK:
    try:
        from dashscope import Generation
    except ImportError as e:
        DASHSCOPE_IMPORT_ERROR = str(e)
        USE_DASHSCOPE_SDK = False
else:
    DASHSCOPE_IMPORT_ERROR = "Python版本不支持DashScope SDK"

class Summarizer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        # 记录使用的API方式
        if USE_DASHSCOPE_SDK:
            self.logger.info("使用DashScope SDK进行API调用")
        else:
            if DASHSCOPE_IMPORT_ERROR:
                self.logger.warning(f"DashScope SDK导入失败 ({DASHSCOPE_IMPORT_ERROR})，将使用HTTP API")
            else:
                self.logger.info(f"Python版本 {sys.version.split()[0]} 不支持DashScope SDK，将使用HTTP API")
        
    def generate_summary(self, news_items: List[Dict[str, Any]]) -> str:
        """生成新闻摘要"""
        try:
            if not news_items:
                self.logger.warning("没有需要处理的新闻")
                return "今日无新闻更新。"

            # 按分类组织新闻
            news_by_category = {}
            for item in news_items:
                if not item:  # 跳过空项
                    continue
                category = item.get('category', 'general')
                if category not in news_by_category:
                    news_by_category[category] = []
                news_by_category[category].append(item)
            
            self.logger.info(f"新闻分类统计: {', '.join([f'{k}({len(v)}条)' for k, v in news_by_category.items()])}")
            
            # 生成每个分类的摘要
            summaries = []
            for category, items in news_by_category.items():
                self.logger.info(f"开始生成 {category} 类新闻摘要，共 {len(items)} 条新闻")
                category_summary = self._generate_category_summary(category, items)
                if category_summary:  # 只添加非空摘要
                    summaries.append(category_summary)
                
            # 组合所有摘要
            if not summaries:
                return "无法生成摘要，请查看日志了解详细信息。"
            
            final_summary = "\n\n".join(summaries)
            
            # 将Markdown转换为HTML
            html_summary = self._convert_to_html(final_summary)
            self.logger.info(f"摘要生成完成并转换为HTML，总长度: {len(html_summary)} 字符")
            
            return html_summary
            
        except Exception as e:
            self.logger.error(f"生成摘要时发生错误: {str(e)}")
            return "摘要生成失败，请查看日志了解详细信息。"

    def _convert_to_html(self, markdown_text: str) -> str:
        """将Markdown文本转换为HTML"""
        try:
            # 使用markdown2转换，启用额外特性
            html = markdown2.markdown(markdown_text, extras=[
                "fenced-code-blocks",
                "tables",
                "break-on-newline"
            ])
            return html
        except Exception as e:
            self.logger.error(f"Markdown转HTML失败: {str(e)}")
            return markdown_text
            
    def _generate_category_summary(self, category: str, items: List[Dict[str, Any]]) -> str:
        """生成单个分类的新闻摘要"""
        try:
            # 准备提示词
            prompt = self._prepare_prompt(category, items)
            messages = [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ]
            
            self.logger.info(f"准备调用通义千问API生成 {category} 类摘要")
            self.logger.info(f"dump prompt {prompt}")

            if USE_DASHSCOPE_SDK:
                return self._generate_using_sdk(category, messages)
            else:
                return self._generate_using_http(category, messages)
                
        except Exception as e:
            self.logger.error(f"生成分类摘要时出错: {str(e)}")
            return f"## {category}\n\n摘要生成失败，请稍后重试。"
    
    def _generate_using_sdk(self, category: str, messages: List[Dict[str, str]]) -> str:
        """使用SDK生成摘要"""
        try:
            response = Generation.call(
                model='qwen-turbo-2025-04-28',
                messages=messages,
                api_key=self.api_key,
                result_format='message',
                max_tokens=3000,
                temperature=0.7,
                top_p=0.8,
            )
            
            if response.status_code == 200:
                summary = response.output.choices[0].message.content
                self.logger.info(f"{category} 类摘要生成成功，响应内容: {summary}")
                return summary
            else:
                self.logger.error(f"API调用失败: {response.code} - {response.message}")
                return f"## {category}\n\n摘要生成失败，请稍后重试。"
        except Exception as e:
            self.logger.error(f"SDK调用出错: {str(e)}")
            return f"## {category}\n\n摘要生成失败，SDK调用异常。"
    
    def _generate_using_http(self, category: str, messages: List[Dict[str, str]]) -> str:
        """使用HTTP API生成摘要"""
        try:
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Algorithm": "qwen-turbo"
            }
            
            # 准备请求体
            data = {
                "model": "qwen-turbo",
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "result_format": "message"
                }
            }
            
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=90
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if "output" in result and "choices" in result["output"]:
                    summary = result["output"]["choices"][0]["message"]["content"]
                    self.logger.info(f"{category} 类摘要生成成功，长度: {len(summary)} 字符")
                    return summary
                else:
                    self.logger.error(f"API响应格式异常: {result}")
                    return f"## {category}\n\n摘要生成失败，API响应格式异常。"
            else:
                self.logger.error(f"API调用失败: {response.status_code} - {response.text}")
                return f"## {category}\n\n摘要生成失败，请稍后重试。"
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP请求异常: {str(e)}")
            return f"## {category}\n\n摘要生成失败，HTTP请求异常。"
            
    def _prepare_prompt(self, category: str, items: List[Dict[str, Any]]) -> str:
        """准备提示词"""
        news_texts = []
        for item in items:
            if not item:  # 跳过空项
                continue
            text = f"标题：{item.get('title', '无标题')}\n"
            text += f"来源：{item.get('source_name', '未知来源')}\n"
            text += f"内容：{item.get('content', '无内容')}\n"
            text += f"链接：{item.get('link', '无链接')}\n"
            if item.get('media', {}).get('images'):
                text += f"包含 {len(item['media']['images'])} 张图片\n"
            if item.get('media', {}).get('videos'):
                text += f"包含 {len(item['media']['videos'])} 个视频\n"
            news_texts.append(text)
            
        separator = "="*50
        prompt = f"""请你作为一个专业的新闻编辑，帮我总结以下{category}类新闻的要点。

要求：
1. 用简洁的语言概括新闻的主要内容
2. 突出重要信息和关键数据
3. 保持客观中立的态度
4. 按重要性排序
5. 使用规范的Markdown格式
6. 遵循以下格式规范：
   - 使用二级标题(##)标记分类名
   - 重要新闻使用无序列表(-)
   - 关键数据或重要引用使用粗体(**)标记
   - 每条新闻之间使用空行分隔
   - 需要用[链接]给出新闻的原始链接，如果无链接，则指出"原始链接缺失"
7. 在完成摘要后，你应自己再检查一下摘要的内容是否完整，链接是否有误等

以下是需要总结的新闻：

{separator}
{chr(10).join(news_texts)}
{separator}

请生成一个格式规范的摘要，示例格式如下：
## {category}

- 第一条重要新闻概述，**关键数据**，核心信息，原始链接

- 第二条新闻概述，包含**重要引用**或数据，原始链接

[其他新闻概述...]"""
        
        self.logger.debug(f"生成的提示词长度: {len(prompt)} 字符")
        return prompt 
