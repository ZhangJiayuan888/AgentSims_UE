import json
from datetime import datetime


def process_agent_data(agent_data):
    """处理单个智能体的数据"""
    result = []

    # 基本信息
    result.append(f"Name: {agent_data.get('name', 'Unknown')}")
    result.append(f"Bio: {agent_data.get('bio', 'No bio available')}")
    result.append(f"Goal: {agent_data.get('goal', 'No goal specified')}")
    result.append("")

    # 状态信息
    state = agent_data.get('state', {})
    if state:
        result.append("Current State:")
        result.append(f"- Buildings available: {', '.join(state.get('buildings', []))}")
        result.append(f"- People nearby: {', '.join(state.get('people', []))}")
        result.append(f"- Cash: {state.get('cash', 0)}")
        result.append(f"- Game Time: {state.get('game_time', 0)}")
        result.append("")

    # 提取完整的历史行为记录
    cache = agent_data.get('cache', {})

    # 历史行为记录 (act_cache)
    if 'act_cache' in cache and cache['act_cache']:
        result.append("Historical Actions (act_cache):")
        for i, action in enumerate(cache['act_cache'], 1):
            result.append(f"  Action #{i}:")
            result.append(f"    Equipment: {action.get('equipment', 'N/A')}")
            result.append(f"    Operation: {action.get('operation', 'N/A')}")
            result.append(f"    Continue Time: {action.get('continue_time', 'N/A')} seconds")
            result.append(f"    Result: {action.get('result', 'N/A')}")
        result.append("")

    # 历史对话记录 (chat_cache)
    if 'chat_cache' in cache and cache['chat_cache']:
        result.append("Historical Conversations (chat_cache):")
        for i, chat in enumerate(cache['chat_cache'], 1):
            result.append(f"  Conversation #{i}:")
            result.append(f"    Speaker: {chat.get('speaker', 'Unknown')}")
            result.append(f"    Content: {chat.get('content', 'No content')}")
        result.append("")

    # 历史计划记录 (plan_cache)
    if 'plan_cache' in cache and cache['plan_cache']:
        result.append("Historical Plans (plan_cache):")
        for i, plan in enumerate(cache['plan_cache'], 1):
            result.append(f"  Plan #{i}:")
            result.append(f"    Building: {plan.get('building', 'N/A')}")
            result.append(f"    Purpose: {plan.get('purpose', 'N/A')}")
        result.append("")

    # 历史记忆记录 (memory_cache)
    if 'memory_cache' in cache and cache['memory_cache']:
        result.append("Historical Memories (memory_cache):")
        for i, memory in enumerate(cache['memory_cache'], 1):
            result.append(f"  Memory #{i}:")
            if 'people' in memory:
                for person, data in memory['people'].items():
                    result.append(f"    Person: {person}")
                    result.append(f"      Impression: {data.get('impression', 'N/A')}")
                    result.append(f"      New Memory: {data.get('newEpisodicMemory', 'N/A')}")
            if 'buildings' in memory:
                for building, data in memory['buildings'].items():
                    result.append(f"    Building: {building}")
                    result.append(f"      Impression: {data.get('impression', 'N/A')}")
                    result.append(f"      New Memory: {data.get('newEpisodicMemory', 'N/A')}")
        result.append("")

    # 当前问题和答案
    if 'question' in agent_data and 'response' in agent_data['question']:
        result.append("Current Questions:")
        for line in agent_data['question']['response'].strip().split('\n'):
            if line.strip():
                result.append(f"- {line.strip()}")
        result.append("")

    if 'answer' in agent_data and 'response' in agent_data['answer']:
        result.append("Current Answers:")
        for line in agent_data['answer']['response'].strip().split('\n'):
            if line.strip():
                result.append(f"- {line.strip()}")
        result.append("")

    # 当前计划和行动
    if 'plan' in agent_data:
        result.append("Current Plan:")
        result.append(f"- Building: {agent_data['plan'].get('building', 'None')}")
        result.append(f"- Purpose: {agent_data['plan'].get('purpose', 'None')}")
        result.append("")

    if 'act' in agent_data and agent_data['act']:
        result.append("Recent Action:")
        if 'action' in agent_data['act']:
            result.append(f"- Action type: {agent_data['act']['action']}")
        if 'equipment' in agent_data['act']:
            result.append(f"- Equipment used: {agent_data['act']['equipment']}")
        if 'operation' in agent_data['act']:
            result.append(f"- Operation: {agent_data['act']['operation']}")
        result.append("")

    # 当前对话
    if 'chat' in agent_data and 'content' in agent_data['chat']:
        result.append("Recent Conversation:")
        result.append(f"- {agent_data['chat']['content']}")
        result.append("")

    return '\n'.join(result)


def process_json_to_txt(input_file, output_file):
    """处理JSON文件并输出为TXT"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return

    # 获取所有智能体
    actors = data.get('actors', {})

    # 准备输出内容
    output_content = []
    output_content.append(f"Simulation Log Summary - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_content.append(f"Last Real Time: {data.get('last_real_time', 'N/A')}")
    output_content.append(f"Last Game Time: {data.get('last_game_time', 'N/A')}")
    output_content.append(f"Tick Count: {data.get('tick_state', {}).get('tick_count', 0)}")
    output_content.append("=" * 100)
    output_content.append("")

    # 处理每个智能体
    for npc_id, agent_data in actors.items():
        output_content.append(f"Agent ID: {npc_id}")
        output_content.append("-" * 100)
        output_content.append(process_agent_data(agent_data))
        output_content.append("=" * 100)
        output_content.append("")

    # 写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_content))
        print(f"Successfully processed data and saved to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")


if __name__ == "__main__":
    input_json = "app.json"  # 替换为你的输入文件路径
    output_txt = "simulation_summary.txt"  # 输出文件路径

    process_json_to_txt(input_json, output_txt)