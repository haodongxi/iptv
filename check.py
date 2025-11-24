import os
import requests
from urllib.parse import urljoin
import re
import sys
import json


def check_playable_channels_from_json(input_file="channels.json", output_file="playable_channels.json", timeout=10):
    """
    从JSON文件中读取播放地址，检测可用性并生成新的JSON文件
    边解析边检测边存储
    
    Args:
        input_file (str): 输入的JSON文件路径
        output_file (str): 输出的JSON文件路径
        timeout (int): 请求超时时间（秒）
    
    Returns:
        dict: 包含处理结果的字典
    """
    try:
        # 读取输入JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            channels = json.load(f)
        
        print(f"开始检测 {len(channels)} 个播放地址...")
        
        playable_channels = {}
        checked_count = 0
        
        # 逐个检测播放地址
        for key, channel_info in channels.items():
            stream_url = channel_info.get('stream_url')
            if not stream_url:
                continue
            
            try:
                # 发送HEAD请求检查URL是否可访问
                response = requests.head(stream_url, timeout=timeout, allow_redirects=True)
                if response.status_code == 200:
                    # 检测通过，保存到可播放频道字典
                    playable_channels[key] = channel_info
                    print(f"✓ {channel_info.get('channel_name', 'Unknown')} - 可播放")
                else:
                    print(f"✗ {channel_info.get('channel_name', 'Unknown')} - HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"✗ {channel_info.get('channel_name', 'Unknown')} - 请求超时")
            except requests.exceptions.RequestException as e:
                print(f"✗ {channel_info.get('channel_name', 'Unknown')} - 网络错误: {str(e)}")
            except Exception as e:
                print(f"⚠ {channel_info.get('channel_name', 'Unknown')} - 检测错误: {str(e)}")
            
            checked_count += 1
            
            # 每检测10个地址就保存一次，实现边检测边存储
            if checked_count % 10 == 0 or checked_count == len(channels):
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(playable_channels, f, ensure_ascii=False, indent=2)
                print(f"进度: {checked_count}/{len(channels)}, 可播放: {len(playable_channels)}")
        
        print(f"检测完成！共 {len(playable_channels)} 个可播放地址，已保存到 {output_file}")
        return {
            "success": True,
            "total_channels": len(channels),
            "playable_channels": len(playable_channels),
            "output_file": output_file
        }
        
    except FileNotFoundError:
        return {"error": f"文件未找到: {input_file}"}
    except json.JSONDecodeError:
        return {"error": f"JSON文件格式错误: {input_file}"}
    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}"}

if __name__ == "__main__":
    result = check_playable_channels_from_json()
    print(result)
