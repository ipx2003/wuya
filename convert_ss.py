import requests
import yaml
import base64
from urllib.parse import unquote

def parse_ss_url(ss_url):
    try:
        if not ss_url.startswith('ss://'):
            return None
        
        ss_url = ss_url[5:]
        remark = "SS_Node"
        
        if '#' in ss_url:
            url_part, remark = ss_url.split('#', 1)
        else:
            url_part = ss_url
        
        if '@' in url_part:
            auth_part, server_part = url_part.split('@', 1)
            
            if ':' in server_part:
                host, port_str = server_part.split(':', 1)
                port = int(port_str)
            else:
                host, port = server_part, 8388
            
            if ':' in auth_part:
                cipher, password = auth_part.split(':', 1)
            else:
                decoded = base64.urlsafe_b64decode(auth_part + '===').decode('utf-8')
                if ':' in decoded:
                    cipher, password = decoded.split(':', 1)
                else:
                    cipher, password = 'aes-256-gcm', decoded
        else:
            host, port = "", 8388
            decoded = base64.urlsafe_b64decode(url_part + '===').decode('utf-8')
            if '@' in decoded:
                auth_part, server_part = decoded.split('@', 1)
                if ':' in server_part:
                    host, port_str = server_part.split(':', 1)
                    port = int(port_str)
                if ':' in auth_part:
                    cipher, password = auth_part.split(':', 1)
                else:
                    cipher, password = 'aes-256-gcm', auth_part
            elif ':' in decoded:
                cipher, password = decoded.split(':', 1)
            else:
                cipher, password = 'aes-256-gcm', decoded
        
        decoded_remark = unquote(remark)
        
        return {
            'name': decoded_remark.strip(),
            'type': 'ss',
            'server': host or '127.0.0.1',
            'port': port,
            'cipher': cipher.lower(),
            'password': password,
            'udp': True
        }
        
    except Exception as e:
        print(f"SS解析失败: {e}")
        return None

# 获取订阅
url = "https://raw.githubusercontent.com/ipx2003/onskr/main/proxies.txt"
response = requests.get(url, timeout=30)
all_lines = [line.strip() for line in response.text.split('\n') if line.strip()]

ss_proxies = []
for line in all_lines:
    if line.startswith('ss://'):
        config = parse_ss_url(line)
        if config:
            ss_proxies.append(config)
            print(f"SS节点: {config['name']}")

print(f"成功解析 {len(ss_proxies)} 个SS节点")

if ss_proxies:
    config = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': True,
        'mode': 'Rule',
        'log-level': 'info',
        'external-controller': ':9090',
        'dns': {
            'enable': True,
            'nameserver': ['119.29.29.29', '223.5.5.5'],
            'fallback': ['8.8.8.8', '8.8.4.4', '1.1.1.1', 'tls://1.0.0.1:853', 'tls://dns.google:853']
        },
        'proxies': ss_proxies,
        'proxy-groups': [{
            'name': '🚀 SS节点选择',
            'type': 'select',
            'proxies': [p['name'] for p in ss_proxies] + ['DIRECT']
        }],
        'rules': ['GEO极速,CN,DIRECT', 'MATCH,🚀 SS节点选择']
    }
    
    with open('mihomo_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    print("✅ SS节点转换完成")
else:
    print("❌ 没有SS节点")
