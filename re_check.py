import os
import requests
from urllib.parse import urljoin
import re
import sys
import json


def recheck_arranged_channels(input_file="channels_arrange.json", output_file="channels_final.json", timeout=10):
    """
    重新检测channels_arrange.json中的播放地址，删除不可用的项
    如果主项不可用，则从childlist中选择第一个可用的作为主项
    如果主项和childlist都不可用，则删除整个频道组
    
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
        
        print(f"开始重新检测 {len(channels)} 个频道组...")
        
        final_channels = {}
        checked_groups = 0
        
        # 逐个检测频道组
        for channel_name, channel_group in channels.items():
            # 检测主项
            main_stream_url = channel_group.get('stream_url')
            main_playable = False
            
            if main_stream_url:
                try:
                    # 发送HEAD请求检查URL是否可访问
                    response = requests.head(main_stream_url, timeout=timeout, allow_redirects=True)
                    main_playable = response.status_code == 200
                    if main_playable:
                        print(f"✓ {channel_name} - 主项可播放")
                    else:
                        print(f"✗ {channel_name} - 主项不可播放 (HTTP {response.status_code})")
                except requests.exceptions.Timeout:
                    print(f"✗ {channel_name} - 主项请求超时")
                except requests.exceptions.RequestException as e:
                    print(f"✗ {channel_name} - 主项网络错误: {str(e)}")
                except Exception as e:
                    print(f"⚠ {channel_name} - 主项检测错误: {str(e)}")
            
            # 检测childlist中的项
            playable_childlist = []
            childlist = channel_group.get('childlist', [])
            
            for i, child_entry in enumerate(childlist):
                child_stream_url = child_entry.get('stream_url')
                if not child_stream_url:
                    continue
                
                try:
                    # 发送HEAD请求检查URL是否可访问
                    response = requests.head(child_stream_url, timeout=timeout, allow_redirects=True)
                    if response.status_code == 200:
                        # 检测通过，保存到可播放列表
                        playable_childlist.append(child_entry)
                        print(f"✓ {channel_name} - 子项{i+1}可播放")
                    else:
                        print(f"✗ {channel_name} - 子项{i+1}不可播放 (HTTP {response.status_code})")
                except requests.exceptions.Timeout:
                    print(f"✗ {channel_name} - 子项{i+1}请求超时")
                except requests.exceptions.RequestException as e:
                    print(f"✗ {channel_name} - 子项{i+1}网络错误: {str(e)}")
                except Exception as e:
                    print(f"⚠ {channel_name} - 子项{i+1}检测错误: {str(e)}")
            
            # 根据检测结果决定如何处理这个频道组
            if main_playable:
                # 主项可用，保留主项和所有可用的子项
                final_channels[channel_name] = {
                    "source_url": channel_group.get('source_url'),
                    "channel_name": channel_group.get('channel_name'),
                    "stream_url": main_stream_url,
                    "attributes": channel_group.get('attributes', {}),
                    "childlist": playable_childlist
                }
            elif playable_childlist:
                # 主项不可用但有可用的子项，将第一个可用子项提升为主项
                first_playable = playable_childlist[0]
                final_channels[channel_name] = {
                    "source_url": first_playable.get('source_url'),
                    "channel_name": channel_group.get('channel_name'),
                    "stream_url": first_playable.get('stream_url'),
                    "attributes": first_playable.get('attributes', {}),
                    "childlist": playable_childlist[1:]  # 剩余的子项
                }
                print(f"↑ {channel_name} - 主项已替换为第一个可用子项")
            else:
                # 主项和所有子项都不可用，跳过这个频道组
                print(f"⊘ {channel_name} - 所有项都不可播放，已删除")
                continue
            
            checked_groups += 1
            
            # 每检测10个频道组就保存一次
            if checked_groups % 10 == 0 or checked_groups == len(channels):
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(final_channels, f, ensure_ascii=False, indent=2)
                print(f"进度: {checked_groups}/{len(channels)}, 有效频道组: {len(final_channels)}")
        
        print(f"重新检测完成！共 {len(final_channels)} 个有效频道组，已保存到 {output_file}")
        return {
            "success": True,
            "total_groups": len(channels),
            "final_groups": len(final_channels),
            "output_file": output_file
        }
        
    except FileNotFoundError:
        return {"error": f"文件未找到: {input_file}"}
    except json.JSONDecodeError:
        return {"error": f"JSON文件格式错误: {input_file}"}
    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}"}

def main():
    print("开始重新检测整理后的频道数据...")
    if os.path.exists("channels_final.json"):
        os.remove("channels_final.json")
    result = recheck_arranged_channels()
    if result.get("success"):
        print("✓ 频道数据重新检测完成！")
        print(f"• 原始频道组数: {result['total_groups']}")
        print(f"• 有效频道组数: {result['final_groups']}")
        print(f"• 输出文件: {result['output_file']}")
    else:
        print(f"✗ 重新检测失败: {result.get('error')}")

if __name__ == "__main__":
    main()
