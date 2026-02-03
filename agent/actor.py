from typing import List, Dict, Any
from agent.agent.agent import Agent
import datetime
import random
import traceback  # 用于打印报错堆栈


class Actor:
    def __init__(self, name: str, bio: str, goal: str, model: str, memorySystem: str, planSystem: str,
                 buildings: List[str], cash: int, start_time: float) -> None:
        self.using = False
        self.agent = Agent(name, bio, goal, model, memorySystem, planSystem, buildings, cash, start_time)
        self.last_action_signature = ""
        self.fail_count = 0

    def from_json(self, obj: Dict[str, Any]):
        self.agent.from_json(obj)
        return self

    def to_json(self) -> Dict[str, Any]:
        return self.agent.to_json()

    # --- 修复：更智能的数据清洗函数 ---
    def _sanitize_result(self, result_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        强制清洗返回结果，防止数值溢出和格式错误
        """
        # 如果是聊天动作，直接返回，不要强行添加 use，否则会导致系统混淆
        if "chat" in result_dict:
            return result_dict

        # 1. 确保 use 字典存在
        if "use" not in result_dict:
            result_dict["use"] = {"continue_time": 60, "result": "Action verified by system."}

        # 2. 强制钳位时间 (Clamping)
        raw_time = result_dict["use"].get("continue_time", 60)
        final_time = 60
        try:
            final_time = float(raw_time)
        except:
            final_time = 60

        # 核心修复：防止天文数字
        if final_time > 14400:  # 超过 4 小时
            final_time = 3600  # 强制设为 1 小时
            result_dict["use"]["result"] = str(result_dict["use"].get("result", "")) + " (System: Duration shortened)"
        elif final_time < 1:
            final_time = 60

        result_dict["use"]["continue_time"] = final_time

        # 3. 确保 equipment 是字符串
        if "equipment" in result_dict:
            eq = result_dict["equipment"]
            if isinstance(eq, list):
                result_dict["equipment"] = str(eq[0]) if len(eq) > 0 else ""
            elif eq is None:
                result_dict["equipment"] = ""
            elif not isinstance(eq, str):
                result_dict["equipment"] = str(eq)

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

            # 分发逻辑
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
            # 捕获所有异常，防止 self.using 锁死
            print(f"CRITICAL ERROR in actor {self.agent.name}: {e}")
            traceback.print_exc()
            ret_dict["status"] = 500
            ret_dict["message"] = f"Internal Error: {str(e)}"
            # 尝试返回一个兜底的空动作，防止前端崩溃
            ret_dict["data"] = {"use": {"continue_time": 60, "result": "System Error Recovered"}, "equipment": "",
                                "operation": "Wait"}

        finally:
            # --- 关键修复：无论发生什么，必须释放锁 ---
            self.using = False

        return ret_dict

    async def _critic(self) -> Dict[str, Any]:
        if self.agent.cache.experience_cache:
            acts = self.agent.cache.experience_cache
            act = acts.pop(0) if acts else dict()
            self.agent.cache.experience_cache = acts

            if not act:
                # 递归调用 _act，结果也需要清洗
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
            action = self.agent.state.act.get("action", "")

            # 死循环检测
            current_signature = f"{action}"
            if action == "use":
                current_signature += f":{self.agent.state.act.get('equipment')}:{self.agent.state.act.get('operation')}"

            if current_signature == self.last_action_signature:
                self.fail_count += 1
            else:
                self.fail_count = 0
            self.last_action_signature = current_signature

            if self.fail_count >= 3:
                print(f"DEBUG: Breaking loop for {self.agent.name}")
                self.fail_count = 0
                return self._sanitize_result({
                    "use": {"continue_time": 60, "result": "Confusion cleared. Stopping to rethink."},
                    "equipment": "",
                    "operation": "Wait"
                })

            if action == "use":
                equipment = self.agent.state.act.get("equipment", "")
                operation = self.agent.state.act.get("operation", "")

                # 类型清洗
                if isinstance(equipment, list):
                    equipment = str(equipment[0]) if len(equipment) > 0 else ""
                elif equipment is None:
                    equipment = ""
                else:
                    equipment = str(equipment)

                # 模糊查找
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

                if target_equip_obj:
                    description = target_equip_obj.get("description", "")
                    menu = target_equip_obj.get("menu", dict())
                else:
                    return self._sanitize_result({
                        "use": {"continue_time": 60, "result": f"Could not find {equipment}."},
                        "equipment": equipment,
                        "operation": operation
                    })

                await self.agent.use(equipment, operation, description, menu)

                # 逻辑拦截 (Gate/Worktop)
                op_lower = operation.lower()
                eq_lower = equipment.lower()

                if "gate" in eq_lower and ("buy" in op_lower or "check" in op_lower):
                    self.agent.state.use["result"] = "This is a door. Please enter inside."
                    self.agent.state.use["bought_thing"] = ""

                if ("worktop" in eq_lower or "table" in eq_lower) and ("laptop" in op_lower or "path" in op_lower):
                    self.agent.state.use["result"] = "Cannot work here. Find a Desk."

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
                        "use": {"continue_time": 60, "result": f"{person} is not here."},
                        "equipment": "",
                        "operation": "Wait"
                    })

                await self.agent.chat(person, topic)
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
                # 兜底未知动作
                return self._sanitize_result({
                    "use": {"continue_time": 60, "result": "Unknown action, waiting."},
                    "equipment": "",
                    "operation": "Wait"
                })

    async def _chat(self, person: str, topic: str) -> Dict[str, Any]:
        await self.agent.chat(person, topic)
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
