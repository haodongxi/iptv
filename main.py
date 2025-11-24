import os
import requests
from urllib.parse import urljoin
import re
import sys
import json

def split_m3u_by_channel(m3u_url, output_dir="channel_files"):
    """
    下载M3U文件并按频道拆分成多个独立的M3U文件
    
    Args:
        m3u_url (str): M3U文件的URL地址
        output_dir (str): 输出目录，默认为"channel_files"
    
    Returns:
        dict: 包含处理结果的字典
    """
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
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
        
        channels = []
        current_channel = {}
        
        # 解析M3U文件[1,2](@ref)
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#EXTINF'):
                # 解析频道信息[2](@ref)
                current_channel = {
                    'extinf': line,
                    'name': extract_channel_name(line),
                    'attributes': extract_attributes(line),
                    'urls': []
                }
            elif line.startswith('http'):
                if current_channel:
                    current_channel['urls'].append(line)
                    # 完成一个频道的解析
                    channels.append(current_channel.copy())
                    current_channel = {}
        
        print(f"找到 {len(channels)} 个频道")
        
        # 为每个频道创建独立的M3U文件[1](@ref)
        created_files = []
        for i, channel in enumerate(channels):
            if channel['urls']:
                filename = sanitize_filename(f"{i+1:03d}_{channel['name']}.m3u")
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('#EXTM3U\n')
                    for url in channel['urls']:
                        f.write(f"{channel['extinf']}\n")
                        f.write(f"{url}\n")
                
                created_files.append({
                    'filename': filename,
                    'channel_name': channel['name'],
                    'stream_count': len(channel['urls'])
                })
        
        # 生成汇总报告
        summary_file = os.path.join(output_dir, "拆分报告.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("M3U文件拆分报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"源文件: {m3u_url}\n")
            f.write(f"总频道数: {len(channels)}\n")
            f.write(f"生成文件: {len(created_files)}\n\n")
            
            for file_info in created_files:
                f.write(f"{file_info['filename']} - {file_info['channel_name']} "
                       f"({file_info['stream_count']}个源)\n")
        
        return {
            "success": True,
            "total_channels": len(channels),
            "created_files": len(created_files),
            "output_dir": os.path.abspath(output_dir),
            "summary_file": summary_file
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
        
        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        
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

def check_m3u_playability(m3u_file_path, timeout=10):
    """
    检测单个m3u文件中的流媒体是否可以播放
    
    Args:
        m3u_file_path (str): m3u文件路径
        timeout (int): 请求超时时间（秒）
    
    Returns:
        dict: 包含检测结果的字典
    """
    try:
        with open(m3u_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找流媒体URL
        urls = []
        for line in lines:
            line = line.strip()
            if line.startswith('http'):
                urls.append(line)
        
        if not urls:
            return {
                "file": os.path.basename(m3u_file_path),
                "status": "error",
                "message": "未找到流媒体URL"
            }
        
        # 测试第一个URL
        stream_url = urls[0]
        try:
            # 发送HEAD请求检查URL是否可访问
            response = requests.head(stream_url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return {
                    "file": os.path.basename(m3u_file_path),
                    "status": "playable",
                    "message": "流媒体可播放",
                    "url": stream_url,
                    "status_code": response.status_code
                }
            else:
                return {
                    "file": os.path.basename(m3u_file_path),
                    "status": "not_playable",
                    "message": f"HTTP状态码: {response.status_code}",
                    "url": stream_url,
                    "status_code": response.status_code
                }
        except requests.exceptions.Timeout:
            return {
                "file": os.path.basename(m3u_file_path),
                "status": "not_playable",
                "message": f"请求超时 ({timeout}秒)",
                "url": stream_url
            }
        except requests.exceptions.RequestException as e:
            return {
                "file": os.path.basename(m3u_file_path),
                "status": "not_playable",
                "message": f"网络错误: {str(e)}",
                "url": stream_url
            }
    
    except Exception as e:
        return {
            "file": os.path.basename(m3u_file_path),
            "status": "error",
            "message": f"文件读取错误: {str(e)}"
        }

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

def check_all_channels_playability(directory="channel_files", timeout=10):
    """
    检测目录下所有m3u文件的可播放性
    
    Args:
        directory (str): 包含m3u文件的目录路径
        timeout (int): 请求超时时间（秒）
    
    Returns:
        dict: 包含所有检测结果的字典
    """
    if not os.path.exists(directory):
        return {"error": f"目录不存在: {directory}"}
    
    # 获取所有m3u文件
    m3u_files = [f for f in os.listdir(directory) if f.endswith('.m3u') and f != "拆分报告.txt"]
    
    if not m3u_files:
        return {"error": f"目录中没有找到m3u文件: {directory}"}
    
    results = []
    playable_count = 0
    not_playable_count = 0
    error_count = 0
    
    print(f"开始检测 {len(m3u_files)} 个频道文件...")
    
    for i, filename in enumerate(m3u_files):
        file_path = os.path.join(directory, filename)
        result = check_m3u_playability(file_path, timeout)
        results.append(result)
        
        if result["status"] == "playable":
            playable_count += 1
        elif result["status"] == "not_playable":
            not_playable_count += 1
        else:  # error
            error_count += 1
        
        # 显示进度
        if (i + 1) % 10 == 0 or (i + 1) == len(m3u_files):
            print(f"进度: {i+1}/{len(m3u_files)} - 可播放: {playable_count}, 不可播放: {not_playable_count}, 错误: {error_count}")
    
    # 生成统计报告
    report = {
        "total": len(m3u_files),
        "playable": playable_count,
        "not_playable": not_playable_count,
        "errors": error_count,
        "results": results
    }
    
    # 保存详细报告
    report_file = os.path.join(directory, "播放性检测报告.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("M3U文件播放性检测报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"总文件数: {report['total']}\n")
        f.write(f"可播放: {report['playable']}\n")
        f.write(f"不可播放: {report['not_playable']}\n")
        f.write(f"错误: {report['errors']}\n\n")
        
        # 分类列出结果
        f.write("可播放的频道:\n")
        for result in results:
            if result["status"] == "playable":
                f.write(f"  ✓ {result['file']}: {result['message']}\n")
                if 'url' in result:
                    f.write(f"    URL: {result['url']}\n")
        
        f.write("\n不可播放的频道:\n")
        for result in results:
            if result["status"] == "not_playable":
                f.write(f"  ✗ {result['file']}: {result['message']}\n")
        
        f.write("\n处理错误的频道:\n")
        for result in results:
            if result["status"] == "error":
                f.write(f"  ⚠ {result['file']}: {result['message']}\n")
    
    print(f"\n检测完成！报告已保存到: {report_file}")
    return report

# 使用示例
if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            # 执行播放性检测
            print("开始检测所有频道文件的可播放性...")
            report = check_all_channels_playability()
            
            if "error" in report:
                print(f"✗ 检测失败: {report['error']}")
            else:
                print("\n检测结果摘要:")
                print(f"• 总文件数: {report['total']}")
                print(f"• 可播放: {report['playable']}")
                print(f"• 不可播放: {report['not_playable']}")
                print(f"• 错误: {report['errors']}")
                print(f"• 详细报告: channel_files/播放性检测报告.txt")
        elif sys.argv[1] == "parse":
            # 解析M3U文件到JSON
            m3u_url = sys.argv[2] if len(sys.argv) > 2 else "https://iptv-org.github.io/iptv/languages/zho.m3u"
            print(f"开始解析M3U文件: {m3u_url}")
            result = parse_m3u_to_json(m3u_url)
            
            if result.get("success"):
                print("✓ M3U文件解析完成！")
                print(f"• 总频道数: {result['total_channels']}")
                print(f"• 输出文件: {result['output_file']}")
            else:
                print(f"✗ 解析失败: {result.get('error')}")
        elif sys.argv[1] == "validate":
            # 验证JSON中的播放地址
            input_file = sys.argv[2] if len(sys.argv) > 2 else "channels.json"
            output_file = sys.argv[3] if len(sys.argv) > 3 else "playable_channels.json"
            print(f"开始验证播放地址: {input_file}")
            result = check_playable_channels_from_json(input_file, output_file)
            
            if result.get("success"):
                print("✓ 播放地址验证完成！")
                print(f"• 总频道数: {result['total_channels']}")
                print(f"• 可播放: {result['playable_channels']}")
                print(f"• 输出文件: {result['output_file']}")
            else:
                print(f"✗ 验证失败: {result.get('error')}")
        else:
            print("用法:")
            print("  python main.py check     - 检测所有频道文件的可播放性")
            print("  python main.py parse [url] - 解析M3U文件到JSON (默认URL: https://iptv-org.github.io/iptv/languages/zho.m3u)")
            print("  python main.py validate [input.json] [output.json] - 验证JSON中的播放地址")
    else:
        # 默认行为：拆分M3U文件
        m3u_url = "https://iptv-org.github.io/iptv/languages/zho.m3u"
        
        result = split_m3u_by_channel(m3u_url)
        
        if result.get("success"):
            print("✓ M3U文件拆分完成！")
            print(f"• 总频道数: {result['total_channels']}")
            print(f"• 输出目录: {result['output_dir']}")
            print(f"• 查看详情: {result['summary_file']}")
        else:
            print(f"✗ 处理失败: {result.get('error')}")
        
        # 提示用户如何进行播放性检测
        print("\n提示：运行 'python main.py check' 来检测所有频道的可播放性")
        print("提示：运行 'python main.py parse' 来解析M3U文件到JSON")
        print("提示：运行 'python main.py validate' 来验证JSON中的播放地址")