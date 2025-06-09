#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Dict, List
import os
import re
from datetime import datetime

class Mailer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def send_daily_report(self, content: str, date: str) -> bool:
        """发送每日报告"""
        try:
            self.logger.info("开始准备发送每日报告")
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.config['subject_template'].format(date=date)
            msg['From'] = self.config['username']
            msg['To'] = ', '.join(self.config['recipients'])
            
            # 添加HTML内容
            html_content = self._format_html_content(content)
            msg.attach(MIMEText(html_content, 'html'))
            
            # 添加图片附件
            self._attach_images(msg)
            
            # 连接SMTP服务器并发送
            smtp_server = self.config['smtp_server']
            smtp_port = self.config['smtp_port']
            username = self.config['username']
            password = self.config['password']
            
            self.logger.info(f"正在连接SMTP服务器: {smtp_server}:{smtp_port}")
            
            try:
                # 使用SSL连接
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                    self.logger.debug("SMTP SSL连接已建立")
                    
                    # 尝试登录
                    self.logger.debug(f"正在尝试登录，用户名: {username}")
                    server.login(username, password)
                    self.logger.debug("SMTP登录成功")
                    
                    # 发送邮件
                    self.logger.debug(f"正在发送邮件到: {msg['To']}")
                    server.send_message(msg)
                    self.logger.info(f"邮件发送成功，收件人: {msg['To']}")
                    return True
                
            except smtplib.SMTPConnectError as e:
                self.logger.error(f"SMTP连接错误: {str(e)}")
                return False
            except smtplib.SMTPAuthenticationError as e:
                self.logger.error(f"SMTP认证错误: {str(e)}")
                return False
            except smtplib.SMTPException as e:
                self.logger.error(f"SMTP错误: {str(e)}")
                return False
            except TimeoutError:
                self.logger.error(f"连接超时: 无法在30秒内连接到SMTP服务器")
                return False
            except Exception as e:
                self.logger.error(f"发送邮件时发生未知错误: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"准备邮件时发生错误: {str(e)}")
            return False
            
    def _format_html_content(self, content: str) -> str:
        """格式化HTML内容"""
        try:
            self.logger.info("开始格式化邮件HTML内容")
            
            # 准备替换内容
            date = datetime.now().strftime('%Y-%m-%d')
            footer_text = "本邮件由谛听自动生成发送。如需退订，请回复\"退订\"。"
            
            # 读取模板文件
            template_path = 'config/templates/email.html'
            
            if not os.path.exists(template_path):
                self.logger.warning(f"模板文件 {template_path} 不存在，使用默认模板")
                template = self._get_default_template()
            else:
                # 读取模板
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                    self.logger.debug(f"成功读取模板文件，长度: {len(template)} 字符")
            
            # 使用字符串替换而不是格式化
            formatted_content = (
                template
                .replace('{date}', date)
                .replace('{content}', content)
                .replace('{footer_text}', footer_text)
            )
            
            self.logger.info(f"HTML内容格式化完成，长度: {len(formatted_content)} 字符")
            return formatted_content
            
        except Exception as e:
            self.logger.error(f"格式化HTML内容时出错: {str(e)}")
            # 使用极简模板作为后备
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
    </style>
</head>
<body>
    <h1>谛听日报 - {date}</h1>
    <div>{content}</div>
    <footer><p>{footer_text}</p></footer>
</body>
</html>"""
            
    def _get_default_template(self) -> str:
        """获取默认模板"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            text-align: center;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 30px;
        }}
        .content {{
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
            text-align: center;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            h1 {{
                font-size: 24px;
            }}
            h2 {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <h1>谛听日报 - {date}</h1>
    <div class="content">
        {content}
    </div>
    <footer>
        <p>{footer_text}</p>
    </footer>
</body>
</html>"""
            
    def _attach_images(self, msg: MIMEMultipart) -> None:
        """添加图片附件"""
        image_dir = 'media/images'
        if not os.path.exists(image_dir):
            return
            
        images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if images:
            self.logger.info(f"开始添加图片附件，共 {len(images)} 张")
            
        for filename in images:
            try:
                file_path = os.path.join(image_dir, filename)
                with open(file_path, 'rb') as f:
                    img_data = f.read()
                    
                # 根据文件扩展名确定MIME类型
                ext = os.path.splitext(filename)[1].lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif'
                }.get(ext, 'application/octet-stream')
                
                img = MIMEImage(img_data, _subtype=mime_type.split('/')[-1])
                img.add_header('Content-ID', f'<{filename}>')
                img.add_header('Content-Disposition', 'inline', filename=filename)
                msg.attach(img)
                self.logger.debug(f"成功添加图片附件: {filename} ({mime_type})")
                
            except Exception as e:
                self.logger.error(f"添加图片附件时出错: {str(e)}")
                continue 