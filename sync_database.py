import os
from supabase import create_client, Client
from typing import List, Dict, Optional
import json


class ChannelDB:
    def __init__(self):
        """
        初始化Supabase客户端
        需要设置环境变量：
        SUPABASE_URL=your_supabase_url
        SUPABASE_KEY=your_supabase_key
        """
        try:
            self.url: str =  "https://eeuwpcynygzohstndlxf.supabase.co"
            self.key: str = "sb_secret_C-HpaYbH0gGYtivfb6j_1A_hkdWVKVy"
            if not self.url or not self.key:
                raise ValueError("请设置SUPABASE_URL和SUPABASE_KEY环境变量")
            
            self.supabase: Client = create_client(self.url, self.key)
        except Exception as e:
            print(f"初始化Supabase客户端失败: {e}")
            raise

    def insert_channel(self, channel_data: Dict) -> Optional[Dict]:
        """
        插入主频道记录
        
        Args:
            channel_data (dict): 频道数据
                {
                    "channel_key": "频道键名",
                    "source_url": "源URL",
                    "channel_name": "频道名称",
                    "stream_url": "流URL",
                    "tvg_name": "tvg名称",
                    "tvg_id": "tvg ID",
                    "tvg_logo": "台标",
                    "group_title": "分组标题"
                }
        
        Returns:
            dict: 插入的记录或None
        """
        try:
            # 准备插入数据
            data = {
                "channel_key": channel_data.get("channel_key"),
                "source_url": channel_data.get("source_url"),
                "channel_name": channel_data.get("channel_name"),
                "stream_url": channel_data.get("stream_url"),
                "tvg_name": channel_data.get("tvg_name"),
                "tvg_id": channel_data.get("tvg_id"),
                "tvg_logo": channel_data.get("tvg_logo"),
                "group_title": channel_data.get("group_title")
            }
            
            # 插入数据
            result = self.supabase.table("channels").insert(data).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"插入频道数据失败: {e}")
            return None

    def insert_channel_source(self, source_data: Dict) -> Optional[Dict]:
        """
        插入频道源记录
        
        Args:
            source_data (dict): 频道源数据
                {
                    "parent_channel_id": 1,  # 父频道ID
                    "source_url": "源URL",
                    "stream_url": "流URL",
                    "tvg_name": "tvg名称",
                    "tvg_id": "tvg ID",
                    "tvg_logo": "台标",
                    "group_title": "分组标题"
                }
        
        Returns:
            dict: 插入的记录或None
        """
        try:
            # 准备插入数据
            data = {
                "parent_channel_id": source_data.get("parent_channel_id"),
                "source_url": source_data.get("source_url"),
                "stream_url": source_data.get("stream_url"),
                "tvg_name": source_data.get("tvg_name"),
                "tvg_id": source_data.get("tvg_id"),
                "tvg_logo": source_data.get("tvg_logo"),
                "group_title": source_data.get("group_title")
            }
            
            # 插入数据
            result = self.supabase.table("channel_sources").insert(data).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"插入频道源数据失败: {e}")
            return None

    def get_channel_by_key(self, channel_key: str) -> Optional[Dict]:
        """
        根据频道键获取频道信息
        
        Args:
            channel_key (str): 频道键名
            
        Returns:
            dict: 频道信息或None
        """
        try:
            result = self.supabase.table("channels").select("*").eq("channel_key", channel_key).execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"查询频道失败: {e}")
            return None

    def get_channel_with_sources(self, channel_key: str) -> Optional[Dict]:
        """
        获取频道及其所有源信息
        
        Args:
            channel_key (str): 频道键名
            
        Returns:
            dict: 频道信息及源列表或None
        """
        try:
            # 先获取频道信息
            channel = self.get_channel_by_key(channel_key)
            if not channel:
                return None
            
            # 获取该频道的所有源
            sources_result = self.supabase.table("channel_sources").select("*").eq("parent_channel_id", channel["id"]).execute()
            channel["sources"] = sources_result.data if sources_result.data else []
            
            return channel
        except Exception as e:
            print(f"查询频道及源信息失败: {e}")
            return None

    def get_all_channels(self) -> List[Dict]:
        """
        获取所有频道
        
        Returns:
            list: 频道列表
        """
        try:
            result = self.supabase.table("channels").select("*").execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查询所有频道失败: {e}")
            return []

    def update_channel(self, channel_id: int, channel_data: Dict) -> bool:
        """
        更新频道信息
        
        Args:
            channel_id (int): 频道ID
            channel_data (dict): 要更新的数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 移除不需要的字段
            update_data = {k: v for k, v in channel_data.items() 
                          if k in ["source_url", "channel_name", "stream_url", 
                                  "tvg_name", "tvg_id", "tvg_logo", "group_title"]}
            
            result = self.supabase.table("channels").update(update_data).eq("id", channel_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"更新频道失败: {e}")
            return False

    def delete_channel(self, channel_id: int) -> bool:
        """
        删除频道（会级联删除相关源）
        
        Args:
            channel_id (int): 频道ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.supabase.table("channels").delete().eq("id", channel_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"删除频道失败: {e}")
            return False

    def delete_channel_source(self, source_id: int) -> bool:
        """
        删除频道源
        
        Args:
            source_id (int): 源ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.supabase.table("channel_sources").delete().eq("id", source_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"删除频道源失败: {e}")
            return False

    def batch_insert_channels_from_json(self, json_file_path: str) -> Dict:
        """
        从JSON文件批量插入频道数据
        
        Args:
            json_file_path (str): JSON文件路径
            
        Returns:
            dict: 处理结果统计
        """
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                channels_data = json.load(f)
            
            success_count = 0
            error_count = 0
            errors = []
            
            # 遍历所有频道
            for channel_key, channel_info in channels_data.items():
                try:
                    # 插入主频道
                    channel_data = {
                        "channel_key": channel_key,
                        "source_url": channel_info.get("source_url"),
                        "channel_name": channel_info.get("channel_name"),
                        "stream_url": channel_info.get("stream_url"),
                        "tvg_name": channel_info.get("attributes", {}).get("tvg-name"),
                        "tvg_id": channel_info.get("attributes", {}).get("tvg-id"),
                        "tvg_logo": channel_info.get("attributes", {}).get("tvg-logo"),
                        "group_title": channel_info.get("attributes", {}).get("group-title")
                    }
                    
                    channel_result = self.insert_channel(channel_data)
                    if channel_result:
                        success_count += 1
                        channel_id = channel_result["id"]
                        
                        # 插入子源
                        childlist = channel_info.get("childlist", [])
                        for child_source in childlist:
                            source_data = {
                                "parent_channel_id": channel_id,
                                "source_url": child_source.get("source_url"),
                                "stream_url": child_source.get("stream_url"),
                                "tvg_name": child_source.get("attributes", {}).get("tvg-name"),
                                "tvg_id": child_source.get("attributes", {}).get("tvg-id"),
                                "tvg_logo": child_source.get("attributes", {}).get("tvg-logo"),
                                "group_title": child_source.get("attributes", {}).get("group-title")
                            }
                            self.insert_channel_source(source_data)
                    else:
                        error_count += 1
                        errors.append(f"插入频道失败: {channel_key}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"处理频道 {channel_key} 时出错: {str(e)}")
            
            return {
                "success": True,
                "total_processed": success_count + error_count,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理JSON文件时出错: {str(e)}"
            }


def main():
    """
    主函数：同步channels_final.json到数据库
    """
    try:
        # 检查环境变量
        supabase_url = "https://eeuwpcynygzohstndlxf.supabase.co"
        supabase_key = "sb_secret_C-HpaYbH0gGYtivfb6j_1A_hkdWVKVy"
        
        if not supabase_url or not supabase_key:
            print("错误: 请设置SUPABASE_URL和SUPABASE_KEY环境变量")
            return
        
        # 初始化数据库连接
        db = ChannelDB()
        print("✓ 数据库连接初始化成功")
        print("开始同步频道数据到数据库...")
        
        # 从channels_final.json导入数据
        result = db.batch_insert_channels_from_json("channels_final.json")
        
        if result["success"]:
            print("✓ 数据同步完成！")
            print(f"• 处理总数: {result['total_processed']}")
            print(f"• 成功: {result['success_count']}")
            print(f"• 失败: {result['error_count']}")
            
            if result['errors']:
                print("详细错误信息:")
                for error in result['errors'][:5]:  # 只显示前5个错误
                    print(f"  - {error}")
                if len(result['errors']) > 5:
                    print(f"  ... 还有 {len(result['errors']) - 5} 个错误")
        else:
            print(f"✗ 数据同步失败: {result['error']}")
            
    except Exception as e:
        print(f"✗ 同步过程中出错: {e}")


if __name__ == "__main__":
    main()