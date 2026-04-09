#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SS订阅转换为Mihomo（Clash Meta）配置格式
输入: https://raw.githubusercontent.com/ipx2003/onskr/refs/heads/main/proxies.txt
输出: mihomo_config.yaml
"""

import requests
import yaml
import re
from urllib.parse import urlparse, parse_qs

def parse_ss_url(ss_url):
    """解析SS链接，返回配置字典"""
    try:
        # 移除 ss:// 前缀
        if ss_url.startswith('ss://'):
            ss_url = ss_url[5:]
        
        # 分割备注部分
        if '#' in ss_url:
            url_part, remark_part = ss_url.split('#', 1)
            remark = remark_part.strip()
        else:
            url_part = ss_url
            remark = "SS Node"
        
        # 解析base64部分
        if '@' in url_part:
            # 格式: method:password@host:port
            auth_part, server_part = url_part.split('@', 1)
            if ':' in auth_part:
                method, password = auth_part.split(':', 1)
            else:
                # 可能是base64编码的method:password
                import base64
                decoded = base64.b64decode(auth_part + '==').decode('utf-8')
                method, password = decoded.split(':', 1)
        
        # 解析服务器部分
        if ':' in server_part:
            host, port = server_part.split(':', 1)
            port = int(port)
        else:
            host = server_part
            port = 8388  # 默认端口
        
        return {
            'name': remark,
            'type': 'ss',
            'server': host,
            'port': port,
            'cipher': method,
            'password': password,
            'udp': True
        }
        
    except Exception as e:
        print(f"解析失败 {ss_url}: {e}")
        return None

def fetch_and_convert():
    """获取并转换订阅"""
    # 获取原始订阅
    url = "https://raw.githubusercontent.com/ipx2003/onskr/refs/heads/main/proxies.txt"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.text.strip()
        
        # 分割每行
        ss_urls = [line.strip() for line in content.split('\n') if line.strip()]
        
        print(f"获取到 {len(ss_urls)} 个SS节点")
        
        # 转换为Mihomo配置
        proxies = []
        for ss_url in ss_urls:
            config = parse_ss_url(ss_url)
            if config:
                proxies.append(config)
        
        print(f"成功转换 {len(proxies)} 个节点")
        
        # 创建Mihomo配置
        mihomo_config = {
            'proxies': proxies,
            'proxy-groups': [
                {
                    'name': '🚀 Auto Select',
                    'type': 'url-test',
                    'proxies': [p['name'] for p in proxies],
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                },
                {
                    'name': '🔁 Fallback',
                    'type': 'fallback',
                    'proxies': [p['name'] for p in proxies],
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                },
                {
                    'name': 'Ⓜ️ Manual',
                    'type': 'select',
                    'proxies': [p['name'] for p in proxies]
                }
            ],
            'rules': [
                'DOMAIN-SUFFIX,google.com,🚀 Auto Select',
                'DOMAIN-SUFFIX,youtube.com,🚀 Auto Select',
                'DOMAIN-SUFFIX,gstatic.com,🚀 Auto Select',
                'GEOIP,CN,DIRECT',
                'MATCH,Ⓜ️ Manual'
            ]
        }
        
        # 写入YAML文件
        with open('mihomo_config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(mihomo_config, f, allow_unicode=True, sort_keys=False)
        
        print("✅ 转换完成！文件已保存为 mihomo_config.yaml")
        print("\n使用方法:")
        print("1. 将 mihomo_config.yaml 导入Mihomo/Clash Meta")
        print("2. 选择 '🚀 Auto Select' 或 'Ⓜ️ Manual' 代理组")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    fetch_and_convert()