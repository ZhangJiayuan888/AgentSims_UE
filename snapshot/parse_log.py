import json
import os
import time


def analyze_app_json():
    file_path = 'app.json'
    output_file = 'Agent_Status_Report.md'

    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return

    try:
        print(f"正在读取 {file_path} ...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        report = []
        report.append(f"# AgentSims 智能体状态全量分析报告")
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # --- 1. 全局状态分析 ---
        movings = set(data.get('movings', []))
        using = set(data.get('using', []))
        chatted = set(data.get('chatted', []))

        report.append("## 1. 全局状态概览")
        report.append(f"- **总智能体数**: {len(data.get('actors', {}))}")
        report.append(f"- **正在移动 (Moving)**: {len(movings)} 人")
        report.append(f"- **正在交互 (Using)**: {len(using)} 人")
        report.append(f"- **正在聊天 (Chatting)**: {len(chatted)} 人")
        report.append(f"- **游戏内时间 (Game Time)**: {data.get('last_game_time', 'Unknown')}")
        report.append(f"- **现实时间 (Real Time)**: {data.get('last_real_time', 'Unknown')}\n")

        # --- 2. 智能体详细分析 ---
        report.append("## 2. 智能体详细状态\n")

        actors = data.get('actors', {})
        for uid, actor_data in actors.items():
            name = actor_data.get('name', 'Unknown')
            bio = actor_data.get('bio', 'N/A')
            goal = actor_data.get('goal', 'N/A')
            caller = actor_data.get('caller', 'Default')

            # 判定当前状态标签
            status_tags = []
            if uid in movings: status_tags.append("🏃 移动中")
            if uid in using: status_tags.append("🔧 使用设施中")
            if uid in chatted: status_tags.append("💬 聊天中")
            if not status_tags: status_tags.append("💤 空闲/思考中")

            report.append(f"### 🏁 {uid} - {name}")
            report.append(f"- **状态**: {' '.join(status_tags)}")
            report.append(f"- **职业/人设**: {bio}")
            report.append(f"- **当前目标**: {goal}")
            report.append(f"- **LLM模型**: `{caller}`")

            # 提取思维/计划 (State)
            state = actor_data.get('state', {})
            plan = state.get('plan', None)

            # 尝试提取 DeepSeek 的 QAFramework 状态
            qa_framework = state.get('question', {})
            if qa_framework:
                report.append(f"- **🧠 思考框架 (QA Framework)**:")
                questions = qa_framework.get('questions', [])
                if questions:
                    report.append(f"  - *当前问题*: {questions}")

            if plan:
                report.append(f"- **📅 当前计划**: {plan}")

            # 提取 Prompt 信息 (通常包含当前的思维链上下文)
            # 注意：Prompt 可能很长，只提取关键部分
            prompts = actor_data.get('prompts', {}).get('prompts', {})
            if prompts:
                # 检查有没有正在进行的 act/plan prompt
                pass

            # 提取对话缓存 (Chat Cache)
            # 在 AgentSims 中，近期对话通常保存在 cache -> chat_cache 或者 state -> chat 中
            cache = actor_data.get('cache', {})
            chat_cache = cache.get('chat_cache', [])

            # 有时对话也直接存储在 state['chat'] 字符串中
            state_chat = state.get('chat', None)

            if chat_cache or (state_chat and isinstance(state_chat, str) and len(state_chat) > 5):
                report.append(f"- **💬 近期对话记录**:")
                if chat_cache:
                    for chat in chat_cache:
                        speaker = chat.get('speaker', 'Unknown')
                        content = chat.get('content', '')
                        report.append(f"  - **{speaker}**: {content}")
                if state_chat and isinstance(state_chat, str):
                    report.append(f"  - *State Buffer*: {state_chat[:200]}..." if len(
                        state_chat) > 200 else f"  - *State Buffer*: {state_chat}")
            else:
                report.append(f"- **💬 近期对话记录**: 无")

            report.append("---\n")

        # --- 3. 保存文件 ---
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"✅ 分析完成！报告已保存至: {output_file}")
        print("请在右侧编辑器中打开该文件查看详情。")

    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_app_json()