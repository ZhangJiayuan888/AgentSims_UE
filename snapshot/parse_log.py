import json

with open('app.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

actors = data.get("actors", {})

with open("full_log.txt", "w", encoding="utf-8") as out:
    for uid, agent in actors.items():
        name = agent.get("name", uid)
        out.write(f"\n🧠 智能体：{name} ({uid})\n")
        out.write("-" * 60 + "\n")

        # 基本信息
        out.write(f"📄 简介: {agent.get('bio', '')}\n")
        out.write(f"🎯 目标: {agent.get('goal', '')}\n")
        state = agent.get("state", {})

        # 当前计划
        plan = state.get("plan")
        out.write("\n📋 当前计划：\n")
        if plan:
            for k, v in plan.items():
                out.write(f"  {k}: {v}\n")
        else:
            out.write("  无\n")

        # 当前行为
        act = state.get("act")
        out.write("\n🛠️ 当前行为：\n")
        if act:
            for k, v in act.items():
                out.write(f"  {k}: {v}\n")
        else:
            out.write("  无\n")

        # 使用反馈
        use = agent.get("use")
        out.write("\n⚙️ 使用反馈:\n")
        if use:
            out.write(json.dumps(use, ensure_ascii=False, indent=2) + "\n")
        else:
            out.write("无\n")

        # 当前对话
        out.write("\n💬 当前对话:\n")
        chat = agent.get("chat", {}).get("content")
        if chat:
            out.write(chat.strip() + "\n")
        else:
            out.write("无\n")

        # 历史对话
        out.write("\n📚 历史对话记录:\n")
        chat_log = agent.get("cache", {}).get("chat_cache", [])
        if chat_log:
            for entry in chat_log:
                speaker = entry.get("speaker", "")
                content = entry.get("content", "")
                out.write(f"  {speaker} said: {content.strip()}\n")
        else:
            out.write("无\n")

        # 行为经验记录
        out.write("\n🧾 行为经历:\n")
        experience = agent.get("experience", [])
        if experience:
            for exp in experience:
                out.write("- " + json.dumps(exp, ensure_ascii=False) + "\n")
        else:
            out.write("无\n")

        # 记忆系统数据
        out.write("\n🧠 记忆数据:\n")
        memory_data = agent.get("memory_data", [])
        if memory_data:
            for mem in memory_data:
                out.write("- " + json.dumps(mem, ensure_ascii=False) + "\n")
        else:
            out.write("无\n")

        out.write("\n\n")
