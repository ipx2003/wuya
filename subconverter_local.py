#!/usr/bin/env python3
"""
基于 subconverter 理念的本地订阅转换器
集成了 sub-web-modify 的高级功能
"""

import requests
import base64
import yaml
import uuid
import re
from urllib.parse import urlparse, parse_qs

class AdvancedSubConverter:
    def __init__(self):
        self.nodes = []
        self.config_templates = {
            'clash': self.generate_clash_config,
            'mihomo': self.generate_mihomo_config,
            'surge': self.generate_surge_config
        }
    
    def load_remote_config(self, config_url):
        """加载远程配置（仿 sub-web-modify）"""
        try:
            response = requests.get(config_url, timeout=10)
            return response.text
        except:
            return None
    
    def parse_advanced_filters(self, filter_rules):
        """解析高级过滤规则"""
        # 支持：包含、排除、正则、排序等
        filters = []
        for rule in filter_rules.split(';'):
            if '=' in rule:
                key, value = rule.split('=', 1)
                filters.append({'type': key, 'value': value})
        return filters
    
    def apply_filters(self, nodes, filters):
        """应用高级过滤器"""
        filtered_nodes = nodes.copy()
        
        for filter_rule in filters:
            filter_type = filter_rule['type']
            filter_value = filter_rule['value']
            
            if filter_type == 'include':
                filtered_nodes = [n for n in filtered_nodes if filter_value in n['name']]
            elif filter_type == 'exclude':
                filtered_nodes = [n for n in filtered_nodes if filter_value not in n['name']]
            elif filter_type == 'regex':
                filtered_nodes = [n for n in filtered_nodes if re.search(filter_value, n['name'])]
        
        return filtered_nodes
    
    def sort_nodes(self, nodes, sort_by='name'):
        """节点排序"""
        if sort_by == 'name':
            return sorted(nodes, key=lambda x: x['name'])
        elif sort_by == 'delay':
            # 可以添加延迟测试功能
            return nodes
        return nodes
    
    def generate_clash_config(self, nodes):
        """生成Clash配置"""
        config = {
            'port': 7890,
            'socks-port': 7891,
            'mode': 'rule',
            'proxies': nodes,
            'proxy-groups': [
                {
                    'name': '🚀 自动选择',
                    'type': 'url-test',
                    'proxies': [n['name'] for n in nodes],
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                }
            ],
            'rules': [
                'GEOIP,CN,DIRECT',
                'MATCH,🚀 自动选择'
            ]
        }
        return yaml.dump(config, allow_unicode=True)
    
    def generate_mihomo_config(self, nodes):
        """生成Mihomo配置"""
        config = self.generate_clash_config(nodes)
        # Mihomo兼容Clash配置
        return config
    
    def generate_surge_config(self, nodes):
        """生成Surge配置"""
        surge_config = "[General]
loglevel = notify
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com

[Proxy]
"
        for node in nodes:
            if node['type'] == 'vmess':
                surge_config += f"{node['name']] = vmess, {node['server']}, {node['port']}, username={node['uuid']}
"
            elif node['type'] == 'vless':
                surge_config += f"{node['name']] = vless, {node['server']}, {node['port']}, encryption=none
"
        
        surge_config += "
[Proxy Group]
🚀 自动选择 = url-test, {{proxies}}, url=http://www.gstatic.com/generate_204, interval=300

[Rule]
GEOIP,CN,DIRECT
FINAL,🚀 自动选择"
        
        return surge_config
    
    def convert(self, sub_url, target='mihomo', config_url=None, filters=None):
        """高级转换方法"""
        
        # 获取订阅内容
        content = self.fetch_subscription(sub_url)
        if not content:
            return None
        
        # 处理订阅内容
        self.process_subscription(content)
        
        # 应用过滤器
        if filters:
            filter_rules = self.parse_advanced_filters(filters)
            self.nodes = self.apply_filters(self.nodes, filter_rules)
        
        # 节点排序
        self.nodes = self.sort_nodes(self.nodes)
        
        # 生成配置
        if target in self.config_templates:
            config = self.config_templates[target](self.nodes)
        else:
            config = self.config_templates['mihomo'](self.nodes)
        
        return config

# 使用示例
if __name__ == "__main__":
    converter = AdvancedSubConverter()
    
    # 高级转换选项
    config = converter.convert(
        sub_url="你的订阅链接",
        target="mihomo",
        filters="include=香港;exclude=过期"
    )
    
    if config:
        with open('config.yaml', 'w', encoding='utf-8') as f:
            f.write(config)
        print("✅ 高级配置生成完成")
    else:
        print("❌ 转换失败")