from typing import List, Dict, Any
from agent.agent.agent import Agent
import datetime
import random
import traceback


class Actor:
    def __init__(self, name: str, bio: str, goal: str, model: str, memorySystem: str, planSystem: str,
                 buildings: List[str], cash: int, start_time: float) -> None:
        self.using = False
        self.agent = Agent(name, bio, goal, model, memorySystem, planSystem, buildings, cash, start_time)
        self.last_action_signature = ""
        self.fail_count = 0

    def from_json(self, obj: Dict[str, Any]):
        self.agent.from_json(obj)
        # --- V7关键：加载时清洗“当前正在进行”的状态，防止时钟锁死 ---
        self._clean_active_state()
        self._clean_history()
        self._clean_experiences()
        return self

    def to_json(self) -> Dict[str, Any]:
        return self.agent.to_json()

    # --- V7新增：清洗当前活跃状态 (Active State Sanitizer) ---
    def _clean_active_state(self):
        """
        检查 Agent 当前是否正处于一个时间异常的动作中。
        如果是，强制结束该动作，以便 Tick 系统能释放 Agent，再次调用 react。
        """
        if self.agent.state.use:
            raw_time = self.agent.state.use.get("continue_time", 0)
            try:
                c_time = float(raw_time)
            except:
                c_time = 0

            # 如果当前动作剩余时间超过 4 小时，强制归零或设为极短
            if c_time > 14400:
                print(f"Force unlocking agent {self.agent.name}: {c_time}s -> 1s")
                self.agent.state.use["continue_time"] = 1  # 设为1秒，让他立刻结束
                self.agent.state.use["result"] = str(self.agent.state.use.get("result", "")) + " (System Unlocked)"

    # --- 清洗长期经验记忆 ---
    def _clean_experiences(self):
        if not hasattr(self.agent.memory_data, 'experience'):
            return

        for exp_id, exp_data in self.agent.memory_data.experience.items():
            if "acts" in exp_data and isinstance(exp_data["acts"], list):
                cleaned_acts = []
                for act in exp_data["acts"]:
                    if not isinstance(act, dict): continue
                    raw_time = act.get("continue_time", 60)
                    try:
                        c_time = float(raw_time)
                    except:
                        c_time = 60

                    if c_time > 14400:
                        act["continue_time"] = 3600
                        if "result" in act:
                            act["result"] = str(act["result"]) + " (Exp Corrected)"
                    cleaned_acts.append(act)
                exp_data["acts"] = cleaned_acts

    # --- 强力历史清洗 ---
    def _clean_history(self):
        if not hasattr(self.agent.cache, 'act_cache') or not self.agent.cache.act_cache:
            return

        cleaned = []
        for act in self.agent.cache.act_cache:
            if not isinstance(act, dict): continue
            if "building" in act or "purpose" in act: continue

            raw_time = act.get("continue_time", 60)
            try:
                c_time = float(raw_time)
            except:
                c_time = 60

            if c_time > 14400:
                act["continue_time"] = 3600
                if "result" in act:
                    act["result"] = str(act["result"]) + " (System Corrected)"

            cleaned.append(act)
        self.agent.cache.act_cache = cleaned

    # --- 状态回写式清洗 ---
    def _sanitize_result(self, result_dict: Dict[str, Any]) -> Dict[str, Any]:
        if "chat" in result_dict:
            return result_dict

        if "use" not in result_dict:
            result_dict["use"] = {"continue_time": 60, "result": "Action verified."}

        raw_time = result_dict["use"].get("continue_time", 60)
        final_time = 60
        try:
            final_time = float(raw_time)
        except:
            final_time = 60

        if final_time > 14400:  # > 4 hours
            final_time = 3600
            result_dict["use"]["result"] = str(result_dict["use"].get("result", "")) + " (Time limited)"
        elif final_time < 1:
            final_time = 60

        result_dict["use"]["continue_time"] = final_time

        eq_val = ""
        if "equipment" in result_dict:
            eq = result_dict["equipment"]
            if isinstance(eq, list):
                eq_val = str(eq[0]) if len(eq) > 0 else ""
            elif eq is None:
                eq_val = ""
            else:
                eq_val = str(eq)
        result_dict["equipment"] = eq_val

        # 回写状态
        if self.agent.state.use is None:
            self.agent.state.use = {}
        self.agent.state.use["continue_time"] = final_time
        self.agent.state.use["result"] = result_dict["use"]["result"]
        if "bought_thing" not in self.agent.state.use:
            self.agent.state.use["bought_thing"] = ""
        if "amount" not in self.agent.state.use:
            self.agent.state.use["amount"] = 0

        if self.agent.state.act and isinstance(self.agent.state.act, dict):
            self.agent.state.act["continue_time"] = final_time

        return result_dict

    async def react(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        ret_dict = {"status": 500, "message": "", "data": dict()}
        if self.using:
            ret_dict["message"] = "still using"
            if observation['source'] != 'chatted':
                return ret_dict
        self.using = True

        try:
            data = observation.get("data", dict())
            self.agent.state.equipments = data.get("equipments", list())
            self.agent.state.people = data.get("people", list())
            self.agent.state.cash = data.get("cash", 0)
            self.agent.state.game_time = datetime.datetime.fromtimestamp(
                data.get("game_time", datetime.datetime.now().timestamp() * 1000) / 1000)

            # --- 执行清洗 ---
            self._clean_history()
            self._clean_experiences()
            self._clean_active_state()  # 运行时也检查一下
            # ------------------

            source = observation['source']
            if source == 'timetick-finishMoving':
                ret_dict["data"] = await self._act()
            elif source == 'timetick-finishUse':
                ret_dict["data"] = await self._critic()
            elif source == 'timetick-finishChatting':
                await self._store_memory()
                ret_dict["data"] = await self._plan()
            elif source == 'inited':
                ret_dict["data"] = await self._plan()
            elif source == 'chatted':
                person = data.get("person", "")
                topic = data.get("topic", "")
                self.agent.cache.chat_cache = data.get("chat_cache", list())
                ret_dict["data"] = await self._chat(person, topic)
            elif source == "addBuilding":
                self._addBuilding(observation['data']['building_name'])
            elif source == 'timetick-storeMemory':
                ret_dict["data"] = await self._store_memory()
            elif source == 'cover-prompt':
                self.agent.cover_prompt(data.get("prompt_type", ""), data.get("prompt_text", ""))

            ret_dict["prompts"] = self.agent.state.get_prompts()
            ret_dict["status"] = 200

        except Exception as e:
            print(f"CRITICAL ERROR in actor {self.agent.name}: {e}")
            traceback.print_exc()
            ret_dict["status"] = 500
            ret_dict["message"] = f"Internal Error: {str(e)}"
            ret_dict["data"] = {"use": {"continue_time": 60, "result": "System Error Recovered"}, "equipment": "",
                                "operation": "Wait"}

        finally:
            self.using = False

        return ret_dict

    async def _critic(self) -> Dict[str, Any]:
        if self.agent.cache.experience_cache:
            acts = self.agent.cache.experience_cache
            act = acts.pop(0) if acts else dict()
            self.agent.cache.experience_cache = acts

            if not act:
                return self._sanitize_result(await self._act())

            raw_result = {
                "use": {"continue_time": act.get("continue_time", 60), "result": act.get("result", "")},
                "equipment": act.get('equipment', ""),
                "operation": act.get('operation', "")
            }
            return self._sanitize_result(raw_result)

        if self.agent.state.execute_experience:
            self.agent.state.execute_experience = False
            return await self._plan()

        await self.agent.critic()
        if self.agent.state.critic:
            result = self.agent.state.critic.get("result", "fail")
            if result == "success" or result == "fail":
                await self._store_memory()
                if result == "success":
                    self.agent.experience()
                    self.agent.cache.plan_cache.append(self.agent.state.plan)
                else:
                    self.agent.cache.act_cache.clear()
                return await self._plan()
            else:
                return self._sanitize_result(await self._act())

    async def _plan(self) -> Dict[str, Any]:
        ret_dict = dict()
        await self.agent.plan()
        ret_dict["newPlan"] = self.agent.state.plan
        return ret_dict

    async def _act(self) -> Dict[str, Any]:
        await self.agent.act()
        if self.agent.state.act:
            if "building" in self.agent.state.act or "purpose" in self.agent.state.act:
                print(f"Warning: Agent {self.agent.name} hallucinated PLAN format in ACT phase. Forcing correction.")
                self.agent.state.act = {"action": "use", "equipment": "",
                                        "operation": "Think (Format Error Correction)"}

            action = self.agent.state.act.get("action", "")

            current_signature = f"{action}"
            current_target = ""
            if action == "use":
                current_target = self.agent.state.act.get('equipment', "")
            elif action == "chat":
                current_target = self.agent.state.act.get('person', "")

            current_signature = f"{action}:{current_target}"

            if current_signature == self.last_action_signature:
                self.fail_count += 1
            else:
                self.fail_count = 0
            self.last_action_signature = current_signature

            if self.fail_count >= 5:
                print(f"DEBUG: Breaking loop for {self.agent.name}")
                self.fail_count = 0
                return self._sanitize_result({
                    "use": {"continue_time": 60, "result": "I seem to be stuck. I will stop and rethink."},
                    "equipment": "",
                    "operation": "Wait"
                })

            if action == "use":
                equipment = self.agent.state.act.get("equipment", "")
                operation = self.agent.state.act.get("operation", "")

                if isinstance(equipment, list):
                    equipment = str(equipment[0]) if len(equipment) > 0 else ""
                elif equipment is None:
                    equipment = ""
                else:
                    equipment = str(equipment)

                target_equip_obj = None
                for e in self.agent.state.equipments:
                    if equipment == e["name"]:
                        target_equip_obj = e
                        break
                if not target_equip_obj:
                    for e in self.agent.state.equipments:
                        if equipment in e["name"]:
                            target_equip_obj = e
                            break

                description = ""
                menu = dict()
                if target_equip_obj:
                    description = target_equip_obj.get("description", "")
                    menu = target_equip_obj.get("menu", dict())
                else:
                    return self._sanitize_result({
                        "use": {"continue_time": 60, "result": f"Could not find equipment {equipment}."},
                        "equipment": equipment,
                        "operation": operation
                    })

                await self.agent.use(equipment, operation, description, menu)

                op_lower = operation.lower()
                eq_lower = equipment.lower()

                if "gate" in eq_lower and ("buy" in op_lower or "check" in op_lower or "open" in op_lower):
                    self.agent.state.use["result"] = "This is just a door. Enter inside."
                    self.agent.state.use["bought_thing"] = ""

                if ("worktop" in eq_lower or "table" in eq_lower) and (
                        "laptop" in op_lower or "work" in op_lower or "thesis" in op_lower):
                    self.agent.state.use["result"] = "You CANNOT use a laptop here. Find a Desk."
                    self.agent.state.use["continue_time"] = 60

                if self.agent.state.use.get("bought_thing") in menu and isinstance(self.agent.state.use.get("amount"),
                                                                                   (int, float)):
                    self.agent.state.use["cost"] = int(self.agent.state.use["amount"]) * menu[
                        self.agent.state.use["bought_thing"]]

                raw_ret = {"use": self.agent.state.use, "equipment": equipment, "operation": operation}
                return self._sanitize_result(raw_ret)

            elif action == "chat":
                person = self.agent.state.act.get("person", "")
                topic = self.agent.state.act.get("topic", "")

                if person not in self.agent.state.people:
                    return self._sanitize_result({
                        "use": {"continue_time": 60, "result": f"No one named {person} is here."},
                        "equipment": "",
                        "operation": "Wait"
                    })

                if person == self.agent.name:
                    return self._sanitize_result({
                        "use": {"continue_time": 60, "result": "I am talking to myself."},
                        "equipment": "",
                        "operation": "Think"
                    })

                await self.agent.chat(person, topic)

                if not self.agent.state.chat:
                    return self._sanitize_result({
                        "use": {"continue_time": 60, "result": "Mind blank. Stopped chatting."},
                        "equipment": "",
                        "operation": "Think"
                    })

                return {"chat": self.agent.state.chat, "person": person, "topic": topic}

            elif action == "experience":
                experienceID = self.agent.state.act.get("experienceID", "")
                experience = self.agent.memory_data.experience.get(experienceID, dict())
                if not experience:
                    return self._sanitize_result(
                        {"use": {"continue_time": 0, "result": "fail"}, "equipment": "", "operation": "nothing"})
                acts = experience.get("acts", list())
                act = acts.pop(0) if acts else dict()
                self.agent.cache.experience_cache = acts
                if not act:
                    return self._sanitize_result(
                        {"use": {"continue_time": 0, "result": "fail"}, "equipment": "", "operation": "nothing"})
                self.agent.state.execute_experience = True

                raw_ret = {
                    "use": {"continue_time": act.get("continue_time", 60), "result": act.get("result", "")},
                    "equipment": act.get('equipment'),
                    "operation": act.get('operation')
                }
                return self._sanitize_result(raw_ret)

            else:
                print(f"Unknown action: {action}. Forcing correction.")
                self.agent.state.act = {"action": "use", "equipment": "", "operation": "Wait (Unknown Action)"}
                return self._sanitize_result({
                    "use": {"continue_time": 60, "result": "Unknown action."},
                    "equipment": "",
                    "operation": "Wait"
                })

    async def _chat(self, person: str, topic: str) -> Dict[str, Any]:
        await self.agent.chat(person, topic)
        if not self.agent.state.chat:
            self.agent.state.chat = "..."
        return {"chat": self.agent.state.chat, "person": person, "topic": topic}

    def _addBuilding(self, building_name: str):
        self.agent.state.buildings.append(building_name)

    async def _store_memory(self):
        await self.agent.memory_store()
        if self.agent.state.memory:
            people = self.agent.state.memory.get("people", dict())
            for name, info in people.items():
                if name not in self.agent.memory_data.people:
                    self.agent.memory_data.people[name] = {"name": name, "relationShip": "", "episodicMemory": list()}
                self.agent.memory_data.people[name]["impression"] = info["impression"]
                self.agent.memory_data.people[name]["episodicMemory"].append(info["newEpisodicMemory"])
            building = self.agent.state.memory.get("building", dict())
            for name, info in building.items():
                if name not in self.agent.memory_data.building:
                    self.agent.memory_data.building[name] = {"name": name, "relationShip": "", "episodicMemory": list()}
                self.agent.memory_data.building[name]["impression"] = info["impression"]
                self.agent.memory_data.building[name]["episodicMemory"].append(info["newEpisodicMemory"])
        return {"stored": True}
        # self.agent.state.buildings.append(building_name)
# from typing import List, Dict, Any
# from agent.agent.agent import Agent
# import datetime
#
# class Actor:
#     """
#         agent:
#             init -> QA -> plan
#         plan -> building -> moving
#         moving -> act -> use / chat
#         use -> critic ? plan : act
#         chat -> set maxInteraction to 5 -> storeMemory -> plan
#         critic true -> pack act to experience
#         timetick -> storeMemory -> memory_store -> Memory
#     """
#     def __init__(self, name: str, bio: str, goal: str, model: str, memorySystem: str, planSystem: str, buildings: List[str], cash: int, start_time: float) -> None:
#         self.using = False
#         self.agent = Agent(name, bio, goal, model, memorySystem, planSystem, buildings, cash, start_time)
#
#     # def _init(self):
#     #     self.agent.plan()
#     def from_json(self, obj: Dict[str, Any]):
#         self.agent.from_json(obj)
#         return self
#
#     def to_json(self) -> Dict[str, Any]:
#         return self.agent.to_json()
#
#     async def react(self, observation: Dict[str, Any]) -> Dict[str, Any]:
#         """_summary_
#
#         Args:
#             observation (Dict[str, Any]):
#             supposed to contains fields like:
#                 : source : str : timetick-finishMoving / timetick-finishUse / chatted / addBuilding / timetick-storeMemory
#                 : data : dict :
#
#         Returns:
#             Dict[str, Any]: _description_
#         """
#         ret_dict = {"status": 500, "message": "", "data": dict()}
#         if self.using:
#             ret_dict["message"] = "still using" # to avoid message overwhelming
#             if observation['source'] != 'chatted':
#                 return ret_dict
#         self.using = True
#         self.agent.state.equipments = observation.get("data", dict()).get("equipments", list())
#         self.agent.state.people = observation.get("data", dict()).get("people", list())
#         self.agent.state.cash = observation.get("data", dict()).get("cash", list())
#         self.agent.state.game_time = datetime.datetime.fromtimestamp(observation.get("data", dict()).get("game_time", datetime.datetime.now().timestamp() * 1000) / 1000)
#         if observation['source'] == 'timetick-finishMoving':
#             ret_dict["data"] = await self._act()
#         elif observation['source'] == 'timetick-finishUse':
#             ret_dict["data"] = await self._critic()
#         elif observation['source'] == 'timetick-finishChatting':
#             await self._store_memory()
#             ret_dict["data"] = await self._plan()
#         elif observation['source'] == 'inited':
#             ret_dict["data"] = await self._plan()
#         elif observation['source'] == 'chatted':
#             person = observation.get("data", dict()).get("person", "")
#             topic = observation.get("data", dict()).get("topic", "")
#             self.agent.cache.chat_cache = observation.get("data", dict()).get("chat_cache", list())
#             ret_dict["data"] = await self._chat(person, topic)
#         elif observation['source'] == "addBuilding":
#             self._addBuilding(observation['data']['building_name'])
#         elif observation['source'] == 'timetick-storeMemory':
#             ret_dict["data"] = await self._store_memory()
#         elif observation['source'] == 'cover-prompt':
#             # ret_dict["data"] = self._cover_prompt()
#             prompt_type = observation.get("data", dict()).get("prompt_type", "")
#             prompt_text = observation.get("data", dict()).get("prompt_text", "")
#             self.agent.cover_prompt(prompt_type, prompt_text)
#         ret_dict["prompts"] = self.agent.state.get_prompts()
#         self.using = False
#         ret_dict["status"] = 200
#         return ret_dict
#
#     async def _critic(self) -> Dict[str, Any]:
#         # ret_dict = dict()
#         if self.agent.cache.experience_cache:
#             acts = self.agent.cache.experience_cache
#             act = dict()
#             if acts:
#                 act = acts.pop(0)
#             self.agent.cache.experience_cache = acts
#             if not act:
#                 return await self._act()
#             return {"use": {"continue_time": act["continue_time"], "result": act["result"]}, "equipment": act['equipment'], "operation": act['operation']}
#         if self.agent.state.execute_experience:
#             self.agent.state.execute_experience = False
#             return await self._plan()
#         await self.agent.critic()
#         if self.agent.state.critic:
#             result = self.agent.state.critic.get("result", "fail")
#             if result == "success" or result == "fail":
#                 await self._store_memory()
#                 if result == "success":
#                     self.agent.experience()
#                     self.agent.cache.plan_cache.append(self.agent.state.plan)
#                 else:
#                     self.agent.cache.act_cache.clear()
#                 return await self._plan()
#                 # ret_dict["newPlan": self.agent.state.plan]
#             else:
#                 return await self._act()
#
#     async def _plan(self) -> Dict[str, Any]:
#         ret_dict = dict()
#         await self.agent.plan()
#         # ret_dict = self._act()
#         ret_dict["newPlan"] = self.agent.state.plan
#         return ret_dict
#
#     async def _act(self) -> Dict[str, Any]:
#         await self.agent.act()
#         if self.agent.state.act:
#             action = self.agent.state.act.get("action", "")
#             # target = self.agent.state.act.get("target", "")
#             if action == "use":
#                 equipment = self.agent.state.act.get("equipment", "")
#                 operation = self.agent.state.act.get("operation", "")
#                 description = ""
#                 menu = dict()
#                 # TODO: find nearest
#                 for e in self.agent.state.equipments:
#                     if equipment in e["name"]:
#                         description = e["description"]
#                         menu = e["menu"]
#                         break
#                 await self.agent.use(equipment, operation, description, menu)
#                 if self.agent.state.use["bought_thing"] in menu and isinstance(self.agent.state.use["amount"], int):
#                     self.agent.state.use["cost"] = self.agent.state.use["amount"] * menu[self.agent.state.use["bought_thing"]]
#                 return {"use": self.agent.state.use, "equipment": equipment, "operation": operation}
#             elif action == "chat":
#                 person = self.agent.state.act.get("person", "")
#                 topic = self.agent.state.act.get("topic", "")
#                 await self.agent.chat(person, topic)
#                 return {"chat": self.agent.state.chat, "person": person, "topic": topic}
#             elif action == "experience":
#                 experienceID = self.agent.state.act.get("experienceID", "")
#                 print(experienceID)
#                 experience = self.agent.memory_data.experience.get(experienceID, dict())
#                 print(experience)
#                 if not experience:
#                     experience = dict()
#                 acts = experience.get("acts", list())
#                 act = dict()
#                 if acts:
#                     act = acts.pop(0)
#                 print(act)
#                 self.agent.cache.experience_cache = acts
#                 # if acts:
#                 if not act:
#                     return {"use": {"continue_time": 0, "result": "fail", "cost": 0, "earn": 0}, "equipment": "", "operation": "nothing to do"}
#                 self.agent.state.execute_experience = True
#                 print(act)
#                 return {"use": {"continue_time": act["continue_time"], "result": act["result"], "cost": act.get("cost", 0), "earn": act.get("earn", 0)}, "equipment": act['equipment'], "operation": act['operation']}
#
#     async def _chat(self, person: str, topic: str) -> Dict[str, Any]:
#         await self.agent.chat(person, topic)
#         return {"chat": self.agent.state.chat, "person": person, "topic": topic}
#
#     def _addBuilding(self, building_name: str):
#         self.agent.state.buildings.append(building_name)
#
#     async def _store_memory(self):
#         await self.agent.memory_store()
#         if self.agent.state.memory:
#             people = self.agent.state.memory.get("people", dict())
#             for name, info in people.items():
#                 if name not in self.agent.memory_data.people:
#                     self.agent.memory_data.people[name] = {
#                         "name": name,
#                         "relationShip": "",
#                         "episodicMemory": list(),
#                     }
#                 self.agent.memory_data.people[name]["impression"] = info["impression"]
#                 self.agent.memory_data.people[name]["episodicMemory"].append(info["newEpisodicMemory"])
#             building = self.agent.state.memory.get("building", dict())
#             for name, info in building.items():
#                 if name not in self.agent.memory_data.building:
#                     self.agent.memory_data.building[name] = {
#                         "name": name,
#                         "relationShip": "",
#                         "episodicMemory": list(),
#                     }
#                 self.agent.memory_data.building[name]["impression"] = info["impression"]
#                 self.agent.memory_data.building[name]["episodicMemory"].append(info["newEpisodicMemory"])
#         return {"stored": True}
#         # self.agent.state.buildings.append(building_name)
