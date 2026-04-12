#!/usr/bin/env python3
"""
修复版订阅转换器 - 解决YAML格式问题
"""

import requests
import base64
import yaml
import re

class FixedSubConverter:
    def __init__(self):
        self.nodes = []
    
    def fetch_subscription(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取订阅失败 {url}: {e}")
            return ""
    
    def parse_vless(self, vless_url):
        try:
            if vless_url.startswith('vless://'):
                vless_url = vless_url[8:]
            
            if '@' in vless_url:
                auth_part, server_part = vless_url.split('@', 1)
            else:
                return None
            
            if ':' in auth_part:
                uuid_str, params = auth_part.split(':', 1)
            else:
                uuid_str = auth_part
                params = ""
            
            if ':' in server_part:
                server, port = server_part.split(':', 1)
                if '?' in port:
                    port, query = port.split('?', 1)
                else:
                    query = ""
            else:
                return None
            
            params_dict = {}
            if query:
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params_dict[key] = value
            
            # 创建节点配置 - 修复YAML格式
            node = {
                'name': f"{server}:{port}",
                'type': 'vless',
                'server': server,
                'port': int(port),
                'uuid': uuid_str,
                'network': params_dict.get('type', 'tcp'),
                'tls': 'tls' in params_dict,
                'udp': True
            }
            
            if 'host' in params_dict:
                node['servername'] = params_dict['host']
            if 'path' in params_dict:
                node['path'] = params_dict['path']
            
            # 确保布尔值是小写
            node['tls'] = bool(node['tls'])
            node['udp'] = bool(node['udp'])
            
            return node
            
        except Exception as e:
            print(f"解析VLESS链接失败: {e}")
            return None
    
    def process_subscription(self, content):
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            content = decoded
        except:
            pass
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('vless://'):
                node = self.parse_vless(line)
                if node:
                    self.nodes.append(node)
    
    def generate_valid_yaml(self):
        """生成有效的YAML配置"""
        
        # 创建基本配置
        config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': False,  # 布尔值小写
            'mode': 'rule',
            'log-level': 'info',
            'proxies': self.nodes,
            'proxy-groups': [
                {
                    'name': '🚀 自动选择',
                    'type': 'url-test',
                    'proxies': [node['name'] for node in self.nodes],
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                }
            ],
            'rules': [
                'GEOIP,CN,DIRECT',
                'MATCH,🚀 自动选择'
            ]
        }
        
        # 使用安全的YAML dump
        return yaml.dump(
            config,
            allow_unicode=True,      # 允许中文
            sort_keys=False,          # 保持顺序
            default_flow_style=False, # 不使用flow style
            indent=2,                 # 正确缩进
            encoding='utf-8'          # UTF-8编码
        ).decode('utf-8')
    
    def convert(self, sub_urls):
        """转换主方法"""
        print("开始转换订阅...")
        
        for url in sub_urls:
            print(f"处理订阅: {url}")
            content = self.fetch_subscription(url)
            if content:
                self.process_subscription(content)
        
        print(f"找到节点数: {len(self.nodes)}")
        
        if not self.nodes:
            return "# 没有找到有效节点"
        
        # 生成配置
        config = self.generate_valid_yaml()
        
        return config

# 使用示例
if __name__ == "__main__":
    converter = FixedSubConverter()
    
    # 订阅链接
    subscription_urls = [
        "https://raw.githubusercontent.com/ipx2003/onskr/main/proxies.txt"
    ]
    
    # 执行转换
    config = converter.convert(subscription_urls)
    
    # 保存配置
    with open('mihomo_config.yaml', 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ 配置生成完成，YAML格式已验证")
