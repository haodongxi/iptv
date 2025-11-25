import os
import requests
from urllib.parse import urljoin
import re
import sys
import json

def parse_m3u_to_json(m3u_url, output_file="channels.json"):
    """
    从M3U URL解析所有播放地址到JSON文件
    
    Args:
        m3u_url (str): M3U文件的URL地址
        output_file (str): 输出JSON文件路径
    
    Returns:
        dict: 包含处理结果的字典
    """
    
    try:
        # 下载M3U文件
        print(f"正在下载M3U文件: {m3u_url}")
        response = requests.get(m3u_url, timeout=30)
        response.raise_for_status()
        
        content = response.text
        lines = content.split('\n')
        
        # 检查文件格式
        if not lines or not lines[0].strip().startswith('#EXTM3U'):
            return {"error": "无效的M3U文件格式"}
        
        channels = {}
        current_channel_info = None
        channel_index = 0
        
        # 解析M3U文件
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#EXTINF'):
                # 解析频道信息
                channel_name = extract_channel_name(line)
                attributes = extract_attributes(line)
                current_channel_info = {
                    'name': channel_name,
                    'attributes': attributes
                }
            elif line.startswith('http'):
                if current_channel_info:
                    channel_key = f"{m3u_url}_{channel_index}"
                    channels[channel_key] = {
                        'source_url': m3u_url,
                        'channel_name': current_channel_info['name'],
                        'stream_url': line,
                        'attributes': current_channel_info['attributes']
                    }
                    channel_index += 1
                    # 重置当前频道信息
                    current_channel_info = None
        
        # 保存到JSON文件（追加模式）
        try:
            # 尝试读取现有文件
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_channels = json.load(f)
                # 合并现有数据和新数据
                existing_channels.update(channels)
                final_channels = existing_channels
            else:
                final_channels = channels
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件不存在或格式错误，则使用新数据
            final_channels = channels
        
        # 写入合并后的数据
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_channels, f, ensure_ascii=False, indent=2)
        
        print(f"解析完成，共找到 {len(channels)} 个播放地址，已保存到 {output_file}")
        return {
            "success": True,
            "total_channels": len(channels),
            "output_file": output_file
        }
        
    except requests.RequestException as e:
        return {"error": f"下载文件失败: {str(e)}"}
    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}"}

def extract_channel_name(extinf_line):
    """从EXTINF行中提取频道名称[1](@ref)"""
    # 格式: #EXTINF:-1 tvg-id="..." tvg-name="...",频道名称
    match = re.search(r',([^,]+)$', extinf_line)
    if match:
        return match.group(1).strip()
    return "未知频道"

def extract_attributes(extinf_line):
    """提取EXTINF行中的属性[2](@ref)"""
    attributes = {}
    # 提取tvg-id, tvg-name, tvg-logo, group-title等属性
    patterns = {
        'tvg-id': r'tvg-id="([^"]*)"',
        'tvg-name': r'tvg-name="([^"]*)"', 
        'tvg-logo': r'tvg-logo="([^"]*)"',
        'group-title': r'group-title="([^"]*)"'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, extinf_line)
        if match:
            attributes[key] = match.group(1)
    
    return attributes

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

def main():
    if os.path.exists('channels.json'):
        os.remove('channels.json')
    channels = json.load(open('channels_url.json'))
    if channels is not None:
        for key, url in channels.items():
            print(f"正在解析 {key}: {url}")
            parse_m3u_to_json(url)

if __name__ == "__main__":
    # 默认使用您提供的URL
    main()
