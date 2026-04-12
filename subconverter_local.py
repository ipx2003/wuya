#!/usr/bin/env python3
"""
纯净版转换器 - 只输出YAML内容
"""

import requests
import base64
import yaml
import re
from urllib.parse import urlparse, parse_qs
import sys

def parse_vless(vless_url):
    """解析VLESS链接为结构化配置"""
    try:
        if vless_url.startswith('vless://'):
            vless_url = vless_url[8:]
        else:
            return None
        
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
        
        # 创建结构化的节点配置
        node = {
            'name': f"{server}:{port}",
            'type': 'vless',
            'server': server,
            'port': int(port),
            'uuid': uuid_str,
            'network': params_dict.get('type', 'tcp'),
            'tls': bool('tls' in params_dict),
            'udp': True
        }
        
        if 'host' in params_dict:
            node['servername'] = params_dict['host']
        if 'path' in params_dict:
            node['path'] = params_dict['path']
        
        return node
        
    except Exception:
        return None

def main():
    # 将调试信息输出到stderr，而不是stdout
    print("开始处理订阅...", file=sys.stderr)
    
    # 下载订阅内容
    sub_url = "https://raw.githubusercontent.com/ipx2003/onskr/main/proxies.txt"
    try:
        response = requests.get(sub_url, timeout=10)
        response.raise_for_status()
        content = response.text
        print(f"成功下载订阅内容，长度: {len(content)}", file=sys.stderr)
    except Exception as e:
        print(f"下载订阅失败: {e}", file=sys.stderr)
        return
    
    # 尝试Base64解码
    try:
        decoded = base64.b64decode(content).decode('utf-8')
        content = decoded
        print("检测到Base64编码，已解码", file=sys.stderr)
    except:
        print("内容未Base64编码，直接处理", file=sys.stderr)
    
    # 解析所有VLESS节点
    nodes = []
    name_count = {}
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('vless://'):
            node = parse_vless(line)
            if node:
                # 确保名称唯一
                base_name = node['name']
                if base_name in name_count:
                    name_count[base_name] += 1
                    node['name'] = f"{base_name}_{name_count[base_name]}"
                else:
                    name_count[base_name] = 1
                
                nodes.append(node)
    
    print(f"成功解析 {len(nodes)} 个VLESS节点", file=sys.stderr)
    
    if not nodes:
        print("❌ 没有找到有效节点", file=sys.stderr)
        return
    
    # 生成正确的Mihomo配置
    config = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': False,
        'mode': 'rule',
        'log-level': 'info',
        'proxies': nodes,
        'proxy-groups': [
            {
                'name': '🚀 自动选择',
                'type': 'url-test',
                'proxies': [node['name'] for node in nodes],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300
            }
        ],
        'rules': [
            'GEOIP,CN,DIRECT',
            'MATCH,🚀 自动选择'
        ]
    }
    
    # 输出纯净的YAML到stdout
    yaml_output = yaml.dump(
        config,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        encoding='utf-8'
    ).decode('utf-8')
    
    # 只输出纯净的YAML内容
    print(yaml_output)

if __name__ == "__main__":
    main()
