import requests
import yaml
from urllib.parse import unquote

def parse_vless_url(vless_url):
    try:
        if not vless_url.startswith('vless://'):
            return None
        
        vless_url = vless_url[8:]
        remark = "VLESS_Node"
        
        if '#' in vless_url:
            url_part, remark = vless_url.split('#', 1)
        else:
            url_part = vless_url
        
        if '@' in url_part:
            uuid_part, server_part = url_part.split('@', 1)
            
            if '?' in server_part:
                server_part, query_part = server_part.split('?', 1)
            else:
                query_part = ''
            
            if ':' in server_part:
                host, port_str = server_part.split(':', 1)
                port = int(port_str)
            else:
                host, port = server_part, 443
            
            query_params = {}
            if query_part:
                for param in query_part.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            decoded_remark = unquote(remark)
            
            vless_config = {
                'name': decoded_remark.strip(),
                'type': 'vless',
                'server': host,
                'port': port,
                'uuid': uuid_part,
                'network': query_params.get('type', 'tcp'),
                'tls': query_params.get('security') == 'tls',
                'skip-cert-verify': False,
                'udp': True,
                'tfo': False,
                'servername': host
            }
            
            return vless_config
            
    except Exception as e:
        print(f"VLESS解析失败: {e}")
        return None

# 获取订阅
url = "https://raw.githubusercontent.com/ipx2003/onskr/main/proxies.txt"
response = requests.get(url, timeout=30)
all_lines = [line.strip() for line in response.text.split('\n') if line.strip()]

vless_proxies = []
for line in all_lines:
    if line.startswith('vless://'):
        config = parse_vless_url(line)
        if config:
            vless_proxies.append(config)
            print(f"VLESS节点: {config['name']}")
            print(f"  UUID: {config['uuid']}")

print(f"成功解析 {len(vless_proxies)} 个VLESS节点")

# 检查UUID重复
uuid_counts = {}
for proxy in vless_proxies:
    uuid = proxy['uuid']
    uuid_counts[uuid] = uuid_counts.get(uuid, 0) + 1

for uuid, count in uuid_counts.items():
    if count > 1:
        print(f"⚠️ UUID重复: {uuid} 使用了 {count} 次")

if vless_proxies:
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
        'proxies': vless_proxies,
        'proxy-groups': [{
            'name': '🚀 VLESS节点选择',
            'type': 'select',
            'proxies': [p['name'] for p in vless_proxies] + ['DIRECT']
        }],
        'rules': ['GEOIP,CN,DIRECT', 'MATCH,🚀 VLESS节点选择']
    }
    
    with open('mihomo_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    print("✅ VLESS节点转换完成")
else:
    print("❌ 没有VLESS节点")
