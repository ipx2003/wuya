#!/usr/bin/env python3
"""
终极纯净版VLESS解析器 - 零调试输出
"""

import requests
import base64
import yaml
import re
from urllib.parse import urlparse, parse_qs
import sys

def parse_vless_advanced(vless_url):
    """高级VLESS链接解析"""
    try:
        if not vless_url.startswith('vless://'):
            return None
        
        vless_url = vless_url[8:]
        
        if '@' not in vless_url:
            return None
        
        auth_part, server_part = vless_url.split('@', 1)
        
        if ':' in auth_part:
            uuid_str, params = auth_part.split(':', 1)
        else:
            uuid_str = auth_part
            params = ""
        
        server_info = server_part.split('?')[0]
        if ':' in server_info:
            server, port = server_info.split(':', 1)
        else:
            return None
        
        query_params = {}
        if '?' in server_part:
            query_str = server_part.split('?', 1)[1]
            if '#' in query_str:
                query_str = query_str.split('#', 1)[0]
            
            for param in query_str.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        
        node = {
            'name': f"VLESS-{server}:{port}",
            'type': 'vless',
            'server': server,
            'port': int(port),
            'uuid': uuid_str,
            'cipher': 'auto',
            'udp': True,
            'skip-cert-verify': False
        }
        
        network_type = query_params.get('type', 'tcp')
        node['network'] = network_type
        
        security = query_params.get('security', '')
        if security == 'tls' or 'tls' in query_params:
            node['tls'] = True
            node['servername'] = query_params.get('sni') or query_params.get('host') or server
        else:
            node['tls'] = False
        
        if network_type == 'ws':
            node['ws-opts'] = {
                'path': query_params.get('path', '/')
            }
            if 'host' in query_params:
                node['ws-opts']['headers'] = {
                    'Host': query_params['host']
                }
        
        if network_type == 'grpc':
            node['grpc-opts'] = {
                'grpc-service-name': query_params.get('serviceName', '')
            }
        
        if network_type == 'h2':
            node['h2-opts'] = {
                'host': query_params.get('host', '').split(','),
                'path': query_params.get('path', '/')
            }
        
        return node
        
    except Exception:
        return None

def main():
    # 完全静默运行，零输出到stdout
    
    # 下载订阅内容
    sub_url = "https://raw.githubusercontent.com/ipx2003/onskr/main/proxies.txt"
    try:
        response = requests.get(sub_url, timeout=10)
        response.raise_for_status()
        content = response.text
    except Exception:
        # 完全静默失败
        return
    
    # 尝试Base64解码
    try:
        decoded = base64.b64decode(content).decode('utf-8')
        content = decoded
    except:
        pass
    
    # 解析VLESS节点
    nodes = []
    name_count = {}
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('vless://'):
            node = parse_vless_advanced(line)
            if node:
                base_name = node['name']
                if base_name in name_count:
                    name_count[base_name] += 1
                    node['name'] = f"{base_name}-{name_count[base_name]}"
                else:
                    name_count[base_name] = 1
                
                nodes.append(node)
    
    if not nodes:
        return
    
    # 生成Mihomo配置
    config = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': False,
        'mode': 'rule',
        'log-level': 'info',
        'proxies': nodes,
        'proxy-groups': [
            {
                'name': '🚀 VLESS节点',
                'type': 'url-test',
                'proxies': [node['name'] for node in nodes],
                '极速': 'http://www.gstatic.com/generate_204',
                'interval': 300
            }
        ],
        'rules': [
            'GEOIP,CN,DIRECT',
            'MATCH,🚀 VLESS节点'
        ]
    }
    
    # 输出纯净YAML
    yaml_output = yaml.dump(
        config,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        encoding='utf-8'
    ).decode('utf-8')
    
    # 这是唯一输出到stdout的内容
    print(yaml_output)

if __name__ == "__main__":
    main()