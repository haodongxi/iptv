import json
import os

def arrange_channels(input_file="playable_channels.json", output_file="channels_arrange.json"):
    """
    整理channels.json的内容，将channel_name相同的合并到一起
    
    Args:
        input_file (str): 输入的JSON文件路径
        output_file (str): 输出的JSON文件路径
    
    Returns:
        dict: 包含处理结果的字典
    """
    try:
        # 读取输入JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            channels = json.load(f)
        
        print(f"开始整理 {len(channels)} 个频道...")
        
        # 按channel_name分组
        grouped_channels = {}
        
        for key, channel_info in channels.items():
            channel_name = channel_info.get('channel_name', 'Unknown')
            
            if channel_name not in grouped_channels:
                # 第一次遇到这个频道名称，创建新的条目
                grouped_channels[channel_name] = {
                    "source_url": channel_info.get('source_url'),
                    "channel_name": channel_name,
                    "stream_url": channel_info.get('stream_url'),
                    "attributes": channel_info.get('attributes', {}),
                    "childlist": []
                }
            else:
                # 已经存在这个频道名称，将当前条目添加到childlist中
                grouped_channels[channel_name]["childlist"].append({
                    "source_url": channel_info.get('source_url'),
                    "stream_url": channel_info.get('stream_url'),
                    "attributes": channel_info.get('attributes', {})
                })
        
        # 后处理：重新排序每个频道组，按照优先级选择最佳母项
        # 优先级：HTTPS的IPv4 > HTTP的IPv4 > HTTPS的IPv6 > HTTP的IPv6
        for channel_name, channel_group in grouped_channels.items():
            # 获取所有条目（主条目+childlist中的条目）
            all_entries = [channel_group] + channel_group["childlist"]
            
            # 按优先级排序条目
            best_entry = None
            
            # 优先级1: HTTPS的IPv4地址
            if not best_entry:
                for entry in all_entries:
                    stream_url = entry.get("stream_url", "")
                    if stream_url.startswith("https://") and "[" not in stream_url:
                        best_entry = entry
                        break
            
            # 优先级2: HTTP的IPv4地址
            if not best_entry:
                for entry in all_entries:
                    stream_url = entry.get("stream_url", "")
                    if stream_url.startswith("http://") and "[" not in stream_url:
                        best_entry = entry
                        break
            
            # 优先级3: HTTPS的IPv6地址
            if not best_entry:
                for entry in all_entries:
                    stream_url = entry.get("stream_url", "")
                    if stream_url.startswith("https://") and "[" in stream_url:
                        best_entry = entry
                        break
            
            # 优先级4: HTTP的IPv6地址
            if not best_entry:
                for entry in all_entries:
                    stream_url = entry.get("stream_url", "")
                    if stream_url.startswith("http://") and "[" in stream_url:
                        best_entry = entry
                        break
            
            # 如果找到了更好的条目且不是当前主条目，则进行交换
            if best_entry and best_entry != channel_group:
                # 将当前主条目添加到childlist中
                channel_group["childlist"].append({
                    "source_url": channel_group["source_url"],
                    "stream_url": channel_group["stream_url"],
                    "attributes": channel_group["attributes"]
                })
                
                # 将找到的最佳条目设为新的主条目
                channel_group["source_url"] = best_entry["source_url"]
                channel_group["stream_url"] = best_entry["stream_url"]
                channel_group["attributes"] = best_entry["attributes"]
                
                # 从childlist中移除已提升为母项的条目
                channel_group["childlist"] = [entry for entry in channel_group["childlist"] 
                                              if entry.get("stream_url") != best_entry["stream_url"]]
        
        # 保存到JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(grouped_channels, f, ensure_ascii=False, indent=2)
        
        print(f"整理完成，共合并为 {len(grouped_channels)} 个频道组，已保存到 {output_file}")
        return {
            "success": True,
            "total_channels": len(channels),
            "grouped_channels": len(grouped_channels),
            "output_file": output_file
        }
        
    except FileNotFoundError:
        return {"error": f"文件未找到: {input_file}"}
    except json.JSONDecodeError:
        return {"error": f"JSON文件格式错误: {input_file}"}
    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}"}

def main():
    print("开始整理频道数据...")
    if os.path.exists('channels_arrange.json'):
        os.remove('channels_arrange.json')
    result = arrange_channels()
    if result.get("success"):
        print("✓ 频道数据整理完成！")
        print(f"• 原始频道数: {result['total_channels']}")
        print(f"• 合并后频道组数: {result['grouped_channels']}")
        print(f"• 输出文件: {result['output_file']}")
        
        # 清空channels_final.json并复制channels_arrange.json的内容
        try:
            # 如果channels_final.json存在，先清空它
            if os.path.exists('channels_final.json'):
                with open('channels_final.json', 'w', encoding='utf-8') as f:
                    f.write('{}')  # 写入空的JSON对象
            
            # 读取channels_arrange.json的内容
            with open('channels_arrange.json', 'r', encoding='utf-8') as source_file:
                content = json.load(source_file)
            
            # 将内容写入channels_final.json
            with open('channels_final.json', 'w', encoding='utf-8') as target_file:
                json.dump(content, target_file, ensure_ascii=False, indent=2)
            
            print("✓ channels_final.json已更新")
        except Exception as e:
            print(f"⚠ 复制到channels_final.json时出错: {str(e)}")
    else:
        print(f"✗ 整理失败: {result.get('error')}")

if __name__ == "__main__":
    main()