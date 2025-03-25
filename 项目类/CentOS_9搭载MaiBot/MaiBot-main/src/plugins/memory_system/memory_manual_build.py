# -*- coding: utf-8 -*-
import datetime
import math
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from dotenv import load_dotenv
from src.common.logger import get_module_logger
import jieba

# from chat.config import global_config
# 添加项目根目录到 Python 路径
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(root_path)

from src.common.database import db  # noqa E402
from src.plugins.memory_system.offline_llm import LLMModel  # noqa E402

# 获取当前文件的目录
current_dir = Path(__file__).resolve().parent
# 获取项目根目录（上三层目录）
project_root = current_dir.parent.parent.parent
# env.dev文件路径
env_path = project_root / ".env.dev"

logger = get_module_logger("mem_manual_bd")

# 加载环境变量
if env_path.exists():
    logger.info(f"从 {env_path} 加载环境变量")
    load_dotenv(env_path)
else:
    logger.warning(f"未找到环境变量文件: {env_path}")
    logger.info("将使用默认配置")


def calculate_information_content(text):
    """计算文本的信息量（熵）"""
    char_count = Counter(text)
    total_chars = len(text)

    entropy = 0
    for count in char_count.values():
        probability = count / total_chars
        entropy -= probability * math.log2(probability)

    return entropy


def get_closest_chat_from_db(length: int, timestamp: str):
    """从数据库中获取最接近指定时间戳的聊天记录，并记录读取次数

    Returns:
        list: 消息记录字典列表，每个字典包含消息内容和时间信息
    """
    chat_records = []
    closest_record = db.messages.find_one({"time": {"$lte": timestamp}}, sort=[("time", -1)])

    if closest_record and closest_record.get("memorized", 0) < 4:
        closest_time = closest_record["time"]
        group_id = closest_record["group_id"]
        # 获取该时间戳之后的length条消息，且groupid相同
        records = list(
            db.messages.find({"time": {"$gt": closest_time}, "group_id": group_id}).sort("time", 1).limit(length)
        )

        # 更新每条消息的memorized属性
        for record in records:
            current_memorized = record.get("memorized", 0)
            if current_memorized > 3:
                print("消息已读取3次，跳过")
                return ""

            # 更新memorized值
            db.messages.update_one({"_id": record["_id"]}, {"$set": {"memorized": current_memorized + 1}})

            # 添加到记录列表中
            chat_records.append(
                {"text": record["detailed_plain_text"], "time": record["time"], "group_id": record["group_id"]}
            )

    return chat_records


class Memory_graph:
    def __init__(self):
        self.G = nx.Graph()  # 使用 networkx 的图结构

    def connect_dot(self, concept1, concept2):
        # 如果边已存在，增加 strength
        if self.G.has_edge(concept1, concept2):
            self.G[concept1][concept2]["strength"] = self.G[concept1][concept2].get("strength", 1) + 1
        else:
            # 如果是新边，初始化 strength 为 1
            self.G.add_edge(concept1, concept2, strength=1)

    def add_dot(self, concept, memory):
        if concept in self.G:
            # 如果节点已存在，将新记忆添加到现有列表中
            if "memory_items" in self.G.nodes[concept]:
                if not isinstance(self.G.nodes[concept]["memory_items"], list):
                    # 如果当前不是列表，将其转换为列表
                    self.G.nodes[concept]["memory_items"] = [self.G.nodes[concept]["memory_items"]]
                self.G.nodes[concept]["memory_items"].append(memory)
            else:
                self.G.nodes[concept]["memory_items"] = [memory]
        else:
            # 如果是新节点，创建新的记忆列表
            self.G.add_node(concept, memory_items=[memory])

    def get_dot(self, concept):
        # 检查节点是否存在于图中
        if concept in self.G:
            # 从图中获取节点数据
            node_data = self.G.nodes[concept]
            return concept, node_data
        return None

    def get_related_item(self, topic, depth=1):
        if topic not in self.G:
            return [], []

        first_layer_items = []
        second_layer_items = []

        # 获取相邻节点
        neighbors = list(self.G.neighbors(topic))

        # 获取当前节点的记忆项
        node_data = self.get_dot(topic)
        if node_data:
            concept, data = node_data
            if "memory_items" in data:
                memory_items = data["memory_items"]
                if isinstance(memory_items, list):
                    first_layer_items.extend(memory_items)
                else:
                    first_layer_items.append(memory_items)

        # 只在depth=2时获取第二层记忆
        if depth >= 2:
            # 获取相邻节点的记忆项
            for neighbor in neighbors:
                node_data = self.get_dot(neighbor)
                if node_data:
                    concept, data = node_data
                    if "memory_items" in data:
                        memory_items = data["memory_items"]
                        if isinstance(memory_items, list):
                            second_layer_items.extend(memory_items)
                        else:
                            second_layer_items.append(memory_items)

        return first_layer_items, second_layer_items

    @property
    def dots(self):
        # 返回所有节点对应的 Memory_dot 对象
        return [self.get_dot(node) for node in self.G.nodes()]


# 海马体
class Hippocampus:
    def __init__(self, memory_graph: Memory_graph):
        self.memory_graph = memory_graph
        self.llm_model = LLMModel()
        self.llm_model_small = LLMModel(model_name="deepseek-ai/DeepSeek-V2.5")
        self.llm_model_get_topic = LLMModel(model_name="Pro/Qwen/Qwen2.5-7B-Instruct")
        self.llm_model_summary = LLMModel(model_name="Qwen/Qwen2.5-32B-Instruct")

    def get_memory_sample(self, chat_size=20, time_frequency=None):
        """获取记忆样本

        Returns:
            list: 消息记录列表，每个元素是一个消息记录字典列表
        """
        if time_frequency is None:
            time_frequency = {"near": 2, "mid": 4, "far": 3}
        current_timestamp = datetime.datetime.now().timestamp()
        chat_samples = []

        # 短期：1h   中期：4h   长期：24h
        for _ in range(time_frequency.get("near")):
            random_time = current_timestamp - random.randint(1, 3600 * 4)
            messages = get_closest_chat_from_db(length=chat_size, timestamp=random_time)
            if messages:
                chat_samples.append(messages)

        for _ in range(time_frequency.get("mid")):
            random_time = current_timestamp - random.randint(3600 * 4, 3600 * 24)
            messages = get_closest_chat_from_db(length=chat_size, timestamp=random_time)
            if messages:
                chat_samples.append(messages)

        for _ in range(time_frequency.get("far")):
            random_time = current_timestamp - random.randint(3600 * 24, 3600 * 24 * 7)
            messages = get_closest_chat_from_db(length=chat_size, timestamp=random_time)
            if messages:
                chat_samples.append(messages)

        return chat_samples

    def calculate_topic_num(self, text, compress_rate):
        """计算文本的话题数量"""
        information_content = calculate_information_content(text)
        topic_by_length = text.count("\n") * compress_rate
        topic_by_information_content = max(1, min(5, int((information_content - 3) * 2)))
        topic_num = int((topic_by_length + topic_by_information_content) / 2)
        print(
            f"topic_by_length: {topic_by_length}, topic_by_information_content: {topic_by_information_content}, "
            f"topic_num: {topic_num}"
        )
        return topic_num

    async def memory_compress(self, messages: list, compress_rate=0.1):
        """压缩消息记录为记忆

        Args:
            messages: 消息记录字典列表，每个字典包含text和time字段
            compress_rate: 压缩率

        Returns:
            set: (话题, 记忆) 元组集合
        """
        if not messages:
            return set()

        # 合并消息文本，同时保留时间信息
        input_text = ""
        time_info = ""
        # 计算最早和最晚时间
        earliest_time = min(msg["time"] for msg in messages)
        latest_time = max(msg["time"] for msg in messages)

        earliest_dt = datetime.datetime.fromtimestamp(earliest_time)
        latest_dt = datetime.datetime.fromtimestamp(latest_time)

        # 如果是同一年
        if earliest_dt.year == latest_dt.year:
            earliest_str = earliest_dt.strftime("%m-%d %H:%M:%S")
            latest_str = latest_dt.strftime("%m-%d %H:%M:%S")
            time_info += f"是在{earliest_dt.year}年，{earliest_str} 到 {latest_str} 的对话:\n"
        else:
            earliest_str = earliest_dt.strftime("%Y-%m-%d %H:%M:%S")
            latest_str = latest_dt.strftime("%Y-%m-%d %H:%M:%S")
            time_info += f"是从 {earliest_str} 到 {latest_str} 的对话:\n"

        for msg in messages:
            input_text += f"{msg['text']}\n"

        print(input_text)

        topic_num = self.calculate_topic_num(input_text, compress_rate)
        topics_response = self.llm_model_get_topic.generate_response(self.find_topic_llm(input_text, topic_num))

        # 过滤topics
        filter_keywords = ["表情包", "图片", "回复", "聊天记录"]
        topics = [
            topic.strip()
            for topic in topics_response[0].replace("，", ",").replace("、", ",").replace(" ", ",").split(",")
            if topic.strip()
        ]
        filtered_topics = [topic for topic in topics if not any(keyword in topic for keyword in filter_keywords)]

        # print(f"原始话题: {topics}")
        print(f"过滤后话题: {filtered_topics}")

        # 创建所有话题的请求任务
        tasks = []
        for topic in filtered_topics:
            topic_what_prompt = self.topic_what(input_text, topic, time_info)
            # 创建异步任务
            task = self.llm_model_small.generate_response_async(topic_what_prompt)
            tasks.append((topic.strip(), task))

        # 等待所有任务完成
        compressed_memory = set()
        for topic, task in tasks:
            response = await task
            if response:
                compressed_memory.add((topic, response[0]))

        return compressed_memory

    async def operation_build_memory(self, chat_size=12):
        # 最近消息获取频率
        time_frequency = {"near": 3, "mid": 8, "far": 5}
        memory_samples = self.get_memory_sample(chat_size, time_frequency)

        all_topics = []  # 用于存储所有话题

        for i, messages in enumerate(memory_samples, 1):
            # 加载进度可视化
            all_topics = []
            progress = (i / len(memory_samples)) * 100
            bar_length = 30
            filled_length = int(bar_length * i // len(memory_samples))
            bar = "█" * filled_length + "-" * (bar_length - filled_length)
            print(f"\n进度: [{bar}] {progress:.1f}% ({i}/{len(memory_samples)})")

            # 生成压缩后记忆
            compress_rate = 0.1
            compressed_memory = await self.memory_compress(messages, compress_rate)
            print(f"\033[1;33m压缩后记忆数量\033[0m: {len(compressed_memory)}")

            # 将记忆加入到图谱中
            for topic, memory in compressed_memory:
                print(f"\033[1;32m添加节点\033[0m: {topic}")
                self.memory_graph.add_dot(topic, memory)
                all_topics.append(topic)

            # 连接相关话题
            for i in range(len(all_topics)):
                for j in range(i + 1, len(all_topics)):
                    print(f"\033[1;32m连接节点\033[0m: {all_topics[i]} 和 {all_topics[j]}")
                    self.memory_graph.connect_dot(all_topics[i], all_topics[j])

        self.sync_memory_to_db()

    def sync_memory_from_db(self):
        """
        从数据库同步数据到内存中的图结构
        将清空当前内存中的图，并从数据库重新加载所有节点和边
        """
        # 清空当前图
        self.memory_graph.G.clear()

        # 从数据库加载所有节点
        nodes = db.graph_data.nodes.find()
        for node in nodes:
            concept = node["concept"]
            memory_items = node.get("memory_items", [])
            # 确保memory_items是列表
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []
            # 添加节点到图中
            self.memory_graph.G.add_node(concept, memory_items=memory_items)

        # 从数据库加载所有边
        edges = db.graph_data.edges.find()
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            strength = edge.get("strength", 1)  # 获取 strength，默认为 1
            # 只有当源节点和目标节点都存在时才添加边
            if source in self.memory_graph.G and target in self.memory_graph.G:
                self.memory_graph.G.add_edge(source, target, strength=strength)

        logger.success("从数据库同步记忆图谱完成")

    def calculate_node_hash(self, concept, memory_items):
        """
        计算节点的特征值
        """
        if not isinstance(memory_items, list):
            memory_items = [memory_items] if memory_items else []
        # 将记忆项排序以确保相同内容生成相同的哈希值
        sorted_items = sorted(memory_items)
        # 组合概念和记忆项生成特征值
        content = f"{concept}:{'|'.join(sorted_items)}"
        return hash(content)

    def calculate_edge_hash(self, source, target):
        """
        计算边的特征值
        """
        # 对源节点和目标节点排序以确保相同的边生成相同的哈希值
        nodes = sorted([source, target])
        return hash(f"{nodes[0]}:{nodes[1]}")

    def sync_memory_to_db(self):
        """
        检查并同步内存中的图结构与数据库
        使用特征值(哈希值)快速判断是否需要更新
        """
        # 获取数据库中所有节点和内存中所有节点
        db_nodes = list(db.graph_data.nodes.find())
        memory_nodes = list(self.memory_graph.G.nodes(data=True))

        # 转换数据库节点为字典格式，方便查找
        db_nodes_dict = {node["concept"]: node for node in db_nodes}

        # 检查并更新节点
        for concept, data in memory_nodes:
            memory_items = data.get("memory_items", [])
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []

            # 计算内存中节点的特征值
            memory_hash = self.calculate_node_hash(concept, memory_items)

            if concept not in db_nodes_dict:
                # 数据库中缺少的节点，添加
                # logger.info(f"添加新节点: {concept}")
                node_data = {"concept": concept, "memory_items": memory_items, "hash": memory_hash}
                db.graph_data.nodes.insert_one(node_data)
            else:
                # 获取数据库中节点的特征值
                db_node = db_nodes_dict[concept]
                db_hash = db_node.get("hash", None)

                # 如果特征值不同，则更新节点
                if db_hash != memory_hash:
                    # logger.info(f"更新节点内容: {concept}")
                    db.graph_data.nodes.update_one(
                        {"concept": concept}, {"$set": {"memory_items": memory_items, "hash": memory_hash}}
                    )

        # 检查并删除数据库中多余的节点
        memory_concepts = set(node[0] for node in memory_nodes)
        for db_node in db_nodes:
            if db_node["concept"] not in memory_concepts:
                # logger.info(f"删除多余节点: {db_node['concept']}")
                db.graph_data.nodes.delete_one({"concept": db_node["concept"]})

        # 处理边的信息
        db_edges = list(db.graph_data.edges.find())
        memory_edges = list(self.memory_graph.G.edges())

        # 创建边的哈希值字典
        db_edge_dict = {}
        for edge in db_edges:
            edge_hash = self.calculate_edge_hash(edge["source"], edge["target"])
            db_edge_dict[(edge["source"], edge["target"])] = {"hash": edge_hash, "num": edge.get("num", 1)}

        # 检查并更新边
        for source, target in memory_edges:
            edge_hash = self.calculate_edge_hash(source, target)
            edge_key = (source, target)

            if edge_key not in db_edge_dict:
                # 添加新边
                logger.info(f"添加新边: {source} - {target}")
                edge_data = {"source": source, "target": target, "num": 1, "hash": edge_hash}
                db.graph_data.edges.insert_one(edge_data)
            else:
                # 检查边的特征值是否变化
                if db_edge_dict[edge_key]["hash"] != edge_hash:
                    logger.info(f"更新边: {source} - {target}")
                    db.graph_data.edges.update_one({"source": source, "target": target}, {"$set": {"hash": edge_hash}})

        # 删除多余的边
        memory_edge_set = set(memory_edges)
        for edge_key in db_edge_dict:
            if edge_key not in memory_edge_set:
                source, target = edge_key
                logger.info(f"删除多余边: {source} - {target}")
                db.graph_data.edges.delete_one({"source": source, "target": target})

        logger.success("完成记忆图谱与数据库的差异同步")

    def find_topic_llm(self, text, topic_num):
        prompt = (
            f"这是一段文字：{text}。请你从这段话中总结出{topic_num}个关键的概念，可以是名词，动词，或者特定人物，帮我列出来，"
            f"用逗号,隔开，尽可能精简。只需要列举{topic_num}个话题就好，不要有序号，不要告诉我其他内容。"
        )
        return prompt

    def topic_what(self, text, topic, time_info):
        # 获取当前时间
        prompt = (
            f'这是一段文字，{time_info}：{text}。我想让你基于这段文字来概括"{topic}"这个概念，帮我总结成一句自然的话，'
            f"可以包含时间和人物，以及具体的观点。只输出这句话就好"
        )
        return prompt

    def remove_node_from_db(self, topic):
        """
        从数据库中删除指定节点及其相关的边

        Args:
            topic: 要删除的节点概念
        """
        # 删除节点
        db.graph_data.nodes.delete_one({"concept": topic})
        # 删除所有涉及该节点的边
        db.graph_data.edges.delete_many({"$or": [{"source": topic}, {"target": topic}]})

    def forget_topic(self, topic):
        """
        随机删除指定话题中的一条记忆，如果话题没有记忆则移除该话题节点
        只在内存中的图上操作，不直接与数据库交互

        Args:
            topic: 要删除记忆的话题

        Returns:
            removed_item: 被删除的记忆项，如果没有删除任何记忆则返回 None
        """
        if topic not in self.memory_graph.G:
            return None

        # 获取话题节点数据
        node_data = self.memory_graph.G.nodes[topic]

        # 如果节点存在memory_items
        if "memory_items" in node_data:
            memory_items = node_data["memory_items"]

            # 确保memory_items是列表
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []

            # 如果有记忆项可以删除
            if memory_items:
                # 随机选择一个记忆项删除
                removed_item = random.choice(memory_items)
                memory_items.remove(removed_item)

                # 更新节点的记忆项
                if memory_items:
                    self.memory_graph.G.nodes[topic]["memory_items"] = memory_items
                else:
                    # 如果没有记忆项了，删除整个节点
                    self.memory_graph.G.remove_node(topic)

                return removed_item

        return None

    async def operation_forget_topic(self, percentage=0.1):
        """
        随机选择图中一定比例的节点进行检查，根据条件决定是否遗忘

        Args:
            percentage: 要检查的节点比例，默认为0.1（10%）
        """
        # 获取所有节点
        all_nodes = list(self.memory_graph.G.nodes())
        # 计算要检查的节点数量
        check_count = max(1, int(len(all_nodes) * percentage))
        # 随机选择节点
        nodes_to_check = random.sample(all_nodes, check_count)

        forgotten_nodes = []
        for node in nodes_to_check:
            # 获取节点的连接数
            connections = self.memory_graph.G.degree(node)

            # 获取节点的内容条数
            memory_items = self.memory_graph.G.nodes[node].get("memory_items", [])
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []
            content_count = len(memory_items)

            # 检查连接强度
            weak_connections = True
            if connections > 1:  # 只有当连接数大于1时才检查强度
                for neighbor in self.memory_graph.G.neighbors(node):
                    strength = self.memory_graph.G[node][neighbor].get("strength", 1)
                    if strength > 2:
                        weak_connections = False
                        break

            # 如果满足遗忘条件
            if (connections <= 1 and weak_connections) or content_count <= 2:
                removed_item = self.forget_topic(node)
                if removed_item:
                    forgotten_nodes.append((node, removed_item))
                    logger.info(f"遗忘节点 {node} 的记忆: {removed_item}")

        # 同步到数据库
        if forgotten_nodes:
            self.sync_memory_to_db()
            logger.info(f"完成遗忘操作，共遗忘 {len(forgotten_nodes)} 个节点的记忆")
        else:
            logger.info("本次检查没有节点满足遗忘条件")

    async def merge_memory(self, topic):
        """
        对指定话题的记忆进行合并压缩

        Args:
            topic: 要合并的话题节点
        """
        # 获取节点的记忆项
        memory_items = self.memory_graph.G.nodes[topic].get("memory_items", [])
        if not isinstance(memory_items, list):
            memory_items = [memory_items] if memory_items else []

        # 如果记忆项不足，直接返回
        if len(memory_items) < 10:
            return

        # 随机选择10条记忆
        selected_memories = random.sample(memory_items, 10)

        # 拼接成文本
        merged_text = "\n".join(selected_memories)
        print(f"\n[合并记忆] 话题: {topic}")
        print(f"选择的记忆:\n{merged_text}")

        # 使用memory_compress生成新的压缩记忆
        compressed_memories = await self.memory_compress(selected_memories, 0.1)

        # 从原记忆列表中移除被选中的记忆
        for memory in selected_memories:
            memory_items.remove(memory)

        # 添加新的压缩记忆
        for _, compressed_memory in compressed_memories:
            memory_items.append(compressed_memory)
            print(f"添加压缩记忆: {compressed_memory}")

        # 更新节点的记忆项
        self.memory_graph.G.nodes[topic]["memory_items"] = memory_items
        print(f"完成记忆合并，当前记忆数量: {len(memory_items)}")

    async def operation_merge_memory(self, percentage=0.1):
        """
        随机检查一定比例的节点，对内容数量超过100的节点进行记忆合并

        Args:
            percentage: 要检查的节点比例，默认为0.1（10%）
        """
        # 获取所有节点
        all_nodes = list(self.memory_graph.G.nodes())
        # 计算要检查的节点数量
        check_count = max(1, int(len(all_nodes) * percentage))
        # 随机选择节点
        nodes_to_check = random.sample(all_nodes, check_count)

        merged_nodes = []
        for node in nodes_to_check:
            # 获取节点的内容条数
            memory_items = self.memory_graph.G.nodes[node].get("memory_items", [])
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []
            content_count = len(memory_items)

            # 如果内容数量超过100，进行合并
            if content_count > 100:
                print(f"\n检查节点: {node}, 当前记忆数量: {content_count}")
                await self.merge_memory(node)
                merged_nodes.append(node)

        # 同步到数据库
        if merged_nodes:
            self.sync_memory_to_db()
            print(f"\n完成记忆合并操作，共处理 {len(merged_nodes)} 个节点")
        else:
            print("\n本次检查没有需要合并的节点")

    async def _identify_topics(self, text: str) -> list:
        """从文本中识别可能的主题"""
        topics_response = self.llm_model_get_topic.generate_response(self.find_topic_llm(text, 5))
        topics = [
            topic.strip()
            for topic in topics_response[0].replace("，", ",").replace("、", ",").replace(" ", ",").split(",")
            if topic.strip()
        ]
        return topics

    def _find_similar_topics(self, topics: list, similarity_threshold: float = 0.4, debug_info: str = "") -> list:
        """查找与给定主题相似的记忆主题"""
        all_memory_topics = list(self.memory_graph.G.nodes())
        all_similar_topics = []

        for topic in topics:
            if debug_info:
                pass

            topic_vector = text_to_vector(topic)

            for memory_topic in all_memory_topics:
                memory_vector = text_to_vector(memory_topic)
                all_words = set(topic_vector.keys()) | set(memory_vector.keys())
                v1 = [topic_vector.get(word, 0) for word in all_words]
                v2 = [memory_vector.get(word, 0) for word in all_words]
                similarity = cosine_similarity(v1, v2)

                if similarity >= similarity_threshold:
                    all_similar_topics.append((memory_topic, similarity))

        return all_similar_topics

    def _get_top_topics(self, similar_topics: list, max_topics: int = 5) -> list:
        """获取相似度最高的主题"""
        seen_topics = set()
        top_topics = []

        for topic, score in sorted(similar_topics, key=lambda x: x[1], reverse=True):
            if topic not in seen_topics and len(top_topics) < max_topics:
                seen_topics.add(topic)
                top_topics.append((topic, score))

        return top_topics

    async def memory_activate_value(self, text: str, max_topics: int = 5, similarity_threshold: float = 0.3) -> int:
        """计算输入文本对记忆的激活程度"""
        logger.info(f"[记忆激活]识别主题: {await self._identify_topics(text)}")

        identified_topics = await self._identify_topics(text)
        if not identified_topics:
            return 0

        all_similar_topics = self._find_similar_topics(
            identified_topics, similarity_threshold=similarity_threshold, debug_info="记忆激活"
        )

        if not all_similar_topics:
            return 0

        top_topics = self._get_top_topics(all_similar_topics, max_topics)

        if len(top_topics) == 1:
            topic, score = top_topics[0]
            memory_items = self.memory_graph.G.nodes[topic].get("memory_items", [])
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []
            content_count = len(memory_items)
            penalty = 1.0 / (1 + math.log(content_count + 1))

            activation = int(score * 50 * penalty)
            print(
                f"\033[1;32m[记忆激活]\033[0m 单主题「{topic}」- 相似度: {score:.3f}, 内容数: {content_count}, "
                f"激活值: {activation}"
            )
            return activation

        matched_topics = set()
        topic_similarities = {}

        for memory_topic, _similarity in top_topics:
            memory_items = self.memory_graph.G.nodes[memory_topic].get("memory_items", [])
            if not isinstance(memory_items, list):
                memory_items = [memory_items] if memory_items else []
            content_count = len(memory_items)
            penalty = 1.0 / (1 + math.log(content_count + 1))

            for input_topic in identified_topics:
                topic_vector = text_to_vector(input_topic)
                memory_vector = text_to_vector(memory_topic)
                all_words = set(topic_vector.keys()) | set(memory_vector.keys())
                v1 = [topic_vector.get(word, 0) for word in all_words]
                v2 = [memory_vector.get(word, 0) for word in all_words]
                sim = cosine_similarity(v1, v2)
                if sim >= similarity_threshold:
                    matched_topics.add(input_topic)
                    adjusted_sim = sim * penalty
                    topic_similarities[input_topic] = max(topic_similarities.get(input_topic, 0), adjusted_sim)
                    print(
                        f"\033[1;32m[记忆激活]\033[0m 主题「{input_topic}」-> "
                        f"「{memory_topic}」(内容数: {content_count}, "
                        f"相似度: {adjusted_sim:.3f})"
                    )

        topic_match = len(matched_topics) / len(identified_topics)
        average_similarities = sum(topic_similarities.values()) / len(topic_similarities) if topic_similarities else 0

        activation = int((topic_match + average_similarities) / 2 * 100)
        print(
            f"\033[1;32m[记忆激活]\033[0m 匹配率: {topic_match:.3f}, 平均相似度: {average_similarities:.3f}, "
            f"激活值: {activation}"
        )

        return activation

    async def get_relevant_memories(
        self, text: str, max_topics: int = 5, similarity_threshold: float = 0.4, max_memory_num: int = 5
    ) -> list:
        """根据输入文本获取相关的记忆内容"""
        identified_topics = await self._identify_topics(text)

        all_similar_topics = self._find_similar_topics(
            identified_topics, similarity_threshold=similarity_threshold, debug_info="记忆检索"
        )

        relevant_topics = self._get_top_topics(all_similar_topics, max_topics)

        relevant_memories = []
        for topic, score in relevant_topics:
            first_layer, _ = self.memory_graph.get_related_item(topic, depth=1)
            if first_layer:
                if len(first_layer) > max_memory_num / 2:
                    first_layer = random.sample(first_layer, max_memory_num // 2)
                for memory in first_layer:
                    relevant_memories.append({"topic": topic, "similarity": score, "content": memory})

        relevant_memories.sort(key=lambda x: x["similarity"], reverse=True)

        if len(relevant_memories) > max_memory_num:
            relevant_memories = random.sample(relevant_memories, max_memory_num)

        return relevant_memories


def segment_text(text):
    """使用jieba进行文本分词"""
    seg_text = list(jieba.cut(text))
    return seg_text


def text_to_vector(text):
    """将文本转换为词频向量"""
    words = segment_text(text)
    vector = {}
    for word in words:
        vector[word] = vector.get(word, 0) + 1
    return vector


def cosine_similarity(v1, v2):
    """计算两个向量的余弦相似度"""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)


def visualize_graph_lite(memory_graph: Memory_graph, color_by_memory: bool = False):
    # 设置中文字体
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 用来正常显示中文标签
    plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号

    G = memory_graph.G

    # 创建一个新图用于可视化
    H = G.copy()

    # 过滤掉内容数量小于2的节点
    nodes_to_remove = []
    for node in H.nodes():
        memory_items = H.nodes[node].get("memory_items", [])
        memory_count = len(memory_items) if isinstance(memory_items, list) else (1 if memory_items else 0)
        if memory_count < 2:
            nodes_to_remove.append(node)

    H.remove_nodes_from(nodes_to_remove)

    # 如果没有符合条件的节点，直接返回
    if len(H.nodes()) == 0:
        print("没有找到内容数量大于等于2的节点")
        return

    # 计算节点大小和颜色
    node_colors = []
    node_sizes = []
    nodes = list(H.nodes())

    # 获取最大记忆数用于归一化节点大小
    max_memories = 1
    for node in nodes:
        memory_items = H.nodes[node].get("memory_items", [])
        memory_count = len(memory_items) if isinstance(memory_items, list) else (1 if memory_items else 0)
        max_memories = max(max_memories, memory_count)

    # 计算每个节点的大小和颜色
    for node in nodes:
        # 计算节点大小（基于记忆数量）
        memory_items = H.nodes[node].get("memory_items", [])
        memory_count = len(memory_items) if isinstance(memory_items, list) else (1 if memory_items else 0)
        # 使用指数函数使变化更明显
        ratio = memory_count / max_memories
        size = 400 + 2000 * (ratio**2)  # 增大节点大小
        node_sizes.append(size)

        # 计算节点颜色（基于连接数）
        degree = H.degree(node)
        if degree >= 30:
            node_colors.append((1.0, 0, 0))  # 亮红色 (#FF0000)
        else:
            # 将1-10映射到0-1的范围
            color_ratio = (degree - 1) / 29.0 if degree > 1 else 0
            # 使用蓝到红的渐变
            red = min(0.9, color_ratio)
            blue = max(0.0, 1.0 - color_ratio)
            node_colors.append((red, 0, blue))

    # 绘制图形
    plt.figure(figsize=(16, 12))  # 减小图形尺寸
    pos = nx.spring_layout(
        H,
        k=1,  # 调整节点间斥力
        iterations=100,  # 增加迭代次数
        scale=1.5,  # 减小布局尺寸
        weight="strength",
    )  # 使用边的strength属性作为权重

    nx.draw(
        H,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=node_sizes,
        font_size=12,  # 保持增大的字体大小
        font_family="SimHei",
        font_weight="bold",
        edge_color="gray",
        width=1.5,
    )  # 统一的边宽度

    title = """记忆图谱可视化（仅显示内容≥2的节点）
节点大小表示记忆数量
节点颜色：蓝(弱连接)到红(强连接)渐变，边的透明度表示连接强度
连接强度越大的节点距离越近"""
    plt.title(title, fontsize=16, fontfamily="SimHei")
    plt.show()


async def main():
    start_time = time.time()

    test_pare = {
        "do_build_memory": False,
        "do_forget_topic": False,
        "do_visualize_graph": True,
        "do_query": False,
        "do_merge_memory": False,
    }

    # 创建记忆图
    memory_graph = Memory_graph()

    # 创建海马体
    hippocampus = Hippocampus(memory_graph)

    # 从数据库同步数据
    hippocampus.sync_memory_from_db()

    end_time = time.time()
    logger.info(f"\033[32m[加载海马体耗时: {end_time - start_time:.2f} 秒]\033[0m")

    # 构建记忆
    if test_pare["do_build_memory"]:
        logger.info("开始构建记忆...")
        chat_size = 20
        await hippocampus.operation_build_memory(chat_size=chat_size)

        end_time = time.time()
        logger.info(
            f"\033[32m[构建记忆耗时: {end_time - start_time:.2f} 秒,chat_size={chat_size},chat_count = 16]\033[0m"
        )

    if test_pare["do_forget_topic"]:
        logger.info("开始遗忘记忆...")
        await hippocampus.operation_forget_topic(percentage=0.1)

        end_time = time.time()
        logger.info(f"\033[32m[遗忘记忆耗时: {end_time - start_time:.2f} 秒]\033[0m")

    if test_pare["do_merge_memory"]:
        logger.info("开始合并记忆...")
        await hippocampus.operation_merge_memory(percentage=0.1)

        end_time = time.time()
        logger.info(f"\033[32m[合并记忆耗时: {end_time - start_time:.2f} 秒]\033[0m")

    if test_pare["do_visualize_graph"]:
        # 展示优化后的图形
        logger.info("生成记忆图谱可视化...")
        print("\n生成优化后的记忆图谱：")
        visualize_graph_lite(memory_graph)

    if test_pare["do_query"]:
        # 交互式查询
        while True:
            query = input("\n请输入新的查询概念（输入'退出'以结束）：")
            if query.lower() == "退出":
                break

            items_list = memory_graph.get_related_item(query)
            if items_list:
                first_layer, second_layer = items_list
                if first_layer:
                    print("\n直接相关的记忆：")
                    for item in first_layer:
                        print(f"- {item}")
                if second_layer:
                    print("\n间接相关的记忆：")
                    for item in second_layer:
                        print(f"- {item}")
            else:
                print("未找到相关记忆。")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
