from command.command_base import CommandBase
from agent.actor import Actor


class LoginBase(CommandBase):

    def reg_npc(self, uid, nickname, x, y, asset, bio, goal):
        account_model = self.get_model('NPCRegister')
        # print(f'!!! when register npc uid: {uid}-{nickname}')
        # print(f'!!! when register database: {account_model.get_db()}')
        id = account_model.find_id(f'{uid}-{nickname}')
        if id <= 0:
            id = account_model.reg_npc(f'{uid}-{nickname}')
            if id <= 0:
                return self.error('register npc failed')
        npc_uid = self.gen_token("NPC", id)
        npc_model = self.get_single_model("NPC", id=id, create=True)
        npc_model.name = nickname
        npc_model.map = self.id
        # TODO: If agent use websocket connect with server
        # Then don't set server and use this field to search npcs not linked
        npc_model.server = npc_uid
        npc_model.cash = 10000
        npc_model.x = x
        npc_model.y = y
        npc_model.rotation = 0
        npc_model.asset = asset
        npc_model.save()

        # buildings_model = self.get_single_model("Buildings", create=False)
        buildings = ["dessert shop", "office", "houseZ", "park"]
        # 改成自定义
        model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        memorySystem = "LongShortTermMemories"
        planSystem = "QAFramework"
        npc_model.model = model
        npc_model.memorySystem = memorySystem
        npc_model.planSystem = planSystem
        npc_model.bio = bio
        npc_model.goal = goal
        npc_model.home_building = 3
        npc_model.work_building = 0
        # if buildings_model:
        #     buildings = buildings_model.get_names()
        self.app.actors[npc_uid] = Actor(nickname, bio, goal, model, memorySystem, planSystem, buildings, 10000,
                                         self.app.last_game_time)
        self.app.inited.add(npc_uid)
        return id, npc_model

    def reg_eval(self, uid):
        for eval_des, eval_cfg in self.app.eval_configs.items():
            eval_model = self.get_single_model('Eval', id=uid, create=True, eval_cfg=eval_cfg)
            self.app.evals[eval_des] = eval_model
        return eval_model

    # Common login logic.
    def handle_login(self, nickname, uid):
        buildings_info = []
        npcs_info = []
        player_model = self.get_single_model('Player', create=False)
        npc_configs = self.app.get_npc_config()
        # First time login, create all data to avoid creating them in scene server.
        # Otherwise, to update login time.
        if player_model is None:
            print(uid, "first login")
            # alan, alan_model = self.reg_npc(uid, "ProfChenWeiya", 0, 12, "premade_01",
            #                                 "ChenWeiya is a structural engineering professor who enjoys sparking conversations in the atrium.",
            #                                 "Wander the atrium after class to meet colleagues and discuss research.")
            # fei, fei_model = self.reg_npc(uid, "pH", 5, 13, "premade_02",
            #                               "Tom is an introverted professor who prefers to avoid crowds.",
            #                               "Head straight to his office to grade papers, minimizing social interactions.")
            # wangzining, wangzining_model = self.reg_npc(uid, "wangzining", 55, 80, "premade_03",
            #                                             "Ada is an outgoing student who loves chatting with anyone she meets.",
            #                                             "Study all the time as he can, unless he is tired.")

            chen, chen_model = self.reg_npc(uid, "ProfChenWeiya", 5, 10, "premade_01",
                                            "Chen Weiya is a structural engineering professor who enjoys sparking conversations in the rest area.",
                                            "Wander the rest area after class to meet colleagues or students and discuss research.")

            zhou, zhou_model = self.reg_npc(uid, "ProfZhouCheng", 4, 8, "premade_02",
                                            "Zhou Cheng is a civil engineering professor known for his engaging office hours.",
                                            "Hold impromptu Q&A sessions in the lounge to help students with their projects.")

            luo, luo_model = self.reg_npc(uid, "ProfLuohanbin", 20, 10, "premade_03",
                                          "Luo Hanbin is an introverted professor who prefers small-group discussions.",
                                          "Seek out one or two colleagues for deep technical talks in quiet corners.")

            # Students
            zhang, zhang_model = self.reg_npc(uid, "ZhangJiayuan", 20, 16, "premade_04",
                                              "Zhang Jiayuan is an outgoing student who loves exploring public spaces.",
                                              "Roam the rest area to find classmates for group study sessions.")

            wang, wang_model = self.reg_npc(uid, "WangZining", 77, 52, "premade_05",
                                            "Wang Zining is a serious student who keeps to herself.",
                                            "Head straight to the office and avoid idle chit-chat.")

            ma, ma_model = self.reg_npc(uid, "MaJiangping", 51, 63, "premade_06",
                                        "Ma Jiangping is a curious student who enjoys spontaneous meetups.",
                                        "Wander through the corridor looking for chance encounters with peers.")

            # Staff
            cai, cai_model = self.reg_npc(uid, "CaiJianhua", 59, 59, "premade_07",
                                          "Cai Jianhua is a friendly administrator who chats while on duty.",
                                          "Deliver mail across offices and greet colleagues in the hallway.")

            li, li_model = self.reg_npc(uid, "LiWenpeng", 77, 77, "premade_08",
                                        "Li Wenpeng is a no-nonsense staff member focused on efficiency.",
                                        "Move directly between offices to complete tasks with minimal stops.")
            song, song_model = self.reg_npc(uid, "SongJunbo", 26, 44, "premade_09",
                                        "SongJunbo is a task-oriented scholar limiting social engagement to essentials, pursuing maximally efficient routes.",
                                        "Take shortest path from study room to advisor's office for thesis consultation while declining all non-essential interactions during transit.")

            models = [
                'Player',
                'Map',
                'Town',
                'Buildings',
                'Equipments',
                'NPCs',
            ]
            for model_name in models:
                model = self.get_single_model(model_name)
                # if model_name == "NPCs":
                # last_npcs = model.npcs
                # for nid in last_npcs:
                #     nuid = self.gen_token("NPC", nid)
                #     if nuid in self.app.movings:
                #         self.app.movings.remove(nuid)
                #     if nuid in self.app.chatted:
                #         self.app.chatted.remove(nuid)
                #     if nuid in self.app.using:
                #         self.app.using.remove(nuid)
                #     if nuid in self.app.inited:
                #         self.app.inited.remove(nuid)
                #     self.app.cache = [c for c in self.app.cache if c["uid"] != nuid]
                #     if nuid in self.app.actors:
                #         del self.app.actors[nuid]
                model.init()
                if model_name == "Player":
                    model.name = nickname
                    model.x = 71
                    model.y = 41
                if model_name == "Map":
                    model.init_map()
                    model.add_uid(71, 41, uid, nickname)
                    # model.add_uid(50, 71, f"NPC-{alan}", "Alan")
                    # model.add_uid(52, 73, f"NPC-{fei}", "Fei")
                    # model.add_uid(55, 80, f"NPC-{wangzining}", "wangzining")
                    model.add_uid(5, 10, f"NPC-{chen}", "ProfChenWeiya")
                    model.add_uid(4, 8, f"NPC-{zhou}", "ProfZhouCheng")
                    model.add_uid(20, 10, f"NPC-{luo}", "ProfLuohanbin")
                    # Place Students
                    model.add_uid(20, 16, f"NPC-{zhang}", "ZhangJiayuan")
                    model.add_uid(77, 52, f"NPC-{wang}", "WangZining")
                    model.add_uid(51, 63, f"NPC-{ma}", "MaJiangping")
                    # Place Staff
                    model.add_uid(59, 59, f"NPC-{cai}", "CaiJianhua")
                    model.add_uid(77, 77, f"NPC-{li}", "LiWenpeng")
                    model.add_uid(26, 44, f"NPC-{song}", "SongJunbo")
                if model_name == "Buildings":
                    model.init_buildings()
                    for building in model.buildings:
                        if building["lC"] > 0:
                            # model.add_tenent(building["id"], alan)
                            # model.add_tenent(building["id"], fei)
                            # model.add_tenent(building["id"], wangzining)
                            model.add_tenent(building["id"], chen)
                            model.add_tenent(building["id"], zhou)
                            model.add_tenent(building["id"], luo)
                            model.add_tenent(building["id"], zhang)
                            model.add_tenent(building["id"], wang)
                            model.add_tenent(building["id"], ma)
                            model.add_tenent(building["id"], cai)
                            model.add_tenent(building["id"], li)
                            model.add_tenent(building["id"], song)
                        buildings_info.append(
                            {"building_id": building["id"], "building_type": building["t"], "name": building["n"],
                             "x": building["x"], "y": building["y"]})
                if model_name == "Equipments":
                    model.init_equipments()
                if model_name == "NPCs":
                    # model.npcs = [{"id": alan, "name": "Alan"}, {"id": fei, "name": "Fei"},
                    #               {"id": wangzining, "name": "wangzining"}]
                    model.npcs = [
                        {"id": chen, "name": "ProfChenWeiya"},
                        {"id": zhou, "name": "ProfZhouCheng"},
                        {"id": luo, "name": "ProfLuohanbin"},
                        {"id": zhang, "name": "ZhangJiayuan"},
                        {"id": wang, "name": "WangZining"},
                        {"id": ma, "name": "MaJiangping"},
                        {"id": cai, "name": "CaiJianhua"},
                        {"id": li, "name": "LiWenpeng"},
                        {"id": song, "name": "SongJunbo"}
                    ]
                    # for npc in model.npcs:
                    #     npc_model = self.get_single_model("NPC", npc["id"], create=False)
                    #     if not npc_model:
                    #         continue
                    #     home_building = self.get_single_model("Buildings", create=True).get_building(npc_model.home_building)
                    #     if not home_building:
                    #         continue

                    # npcs_info.append({"uid": f"NPC-{alan}", "homeBuilding": alan_model.home_building,
                    #                   'asset': npc_configs.assets.index(alan_model.asset),
                    #                   "assetName": alan_model.asset, 'model': alan_model.model,
                    #                   'memorySystem': alan_model.memorySystem, 'planSystem': alan_model.planSystem,
                    #                   'workBuilding': alan_model.work_building, 'nickname': alan_model.name,
                    #                   'bio': alan_model.bio, 'goal': alan_model.goal, 'cash': alan_model.cash,
                    #                   "x": alan_model.x, "y": alan_model.y})
                    # npcs_info.append({"uid": f"NPC-{fei}", "homeBuilding": fei_model.home_building,
                    #                   'asset': npc_configs.assets.index(fei_model.asset), "assetName": fei_model.asset,
                    #                   'model': fei_model.model, 'memorySystem': fei_model.memorySystem,
                    #                   'planSystem': fei_model.planSystem, 'workBuilding': fei_model.work_building,
                    #                   'nickname': fei_model.name, 'bio': fei_model.bio, 'goal': fei_model.goal,
                    #                   'cash': fei_model.cash, "x": fei_model.x, "y": fei_model.y})
                    # npcs_info.append({"uid": f"NPC-{wangzining}", "homeBuilding": wangzining_model.home_building,
                    #                   'asset': npc_configs.assets.index(wangzining_model.asset),
                    #                   "assetName": wangzining_model.asset,
                    #                   'model': wangzining_model.model, 'memorySystem': wangzining_model.memorySystem,
                    #                   'planSystem': wangzining_model.planSystem,
                    #                   'workBuilding': wangzining_model.work_building,
                    #                   'nickname': wangzining_model.name, 'bio': wangzining_model.bio,
                    #                   'goal': wangzining_model.goal,
                    #                   'cash': wangzining_model.cash, "x": wangzining_model.x, "y": wangzining_model.y})
                npcs_info.append({
                    "uid": f"NPC-{chen}",
                    "homeBuilding": chen_model.home_building,
                    "asset": npc_configs.assets.index(chen_model.asset),
                    "assetName": chen_model.asset,
                    "model": chen_model.model,
                    "memorySystem": chen_model.memorySystem,
                    "planSystem": chen_model.planSystem,
                    "workBuilding": chen_model.work_building,
                    "nickname": chen_model.name,
                    "bio": chen_model.bio,
                    "goal": chen_model.goal,
                    "cash": chen_model.cash,
                    "x": chen_model.x,
                    "y": chen_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{zhou}",
                    "homeBuilding": zhou_model.home_building,
                    "asset": npc_configs.assets.index(zhou_model.asset),
                    "assetName": zhou_model.asset,
                    "model": zhou_model.model,
                    "memorySystem": zhou_model.memorySystem,
                    "planSystem": zhou_model.planSystem,
                    "workBuilding": zhou_model.work_building,
                    "nickname": zhou_model.name,
                    "bio": zhou_model.bio,
                    "goal": zhou_model.goal,
                    "cash": zhou_model.cash,
                    "x": zhou_model.x,
                    "y": zhou_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{luo}",
                    "homeBuilding": luo_model.home_building,
                    "asset": npc_configs.assets.index(luo_model.asset),
                    "assetName": luo_model.asset,
                    "model": luo_model.model,
                    "memorySystem": luo_model.memorySystem,
                    "planSystem": luo_model.planSystem,
                    "workBuilding": luo_model.work_building,
                    "nickname": luo_model.name,
                    "bio": luo_model.bio,
                    "goal": luo_model.goal,
                    "cash": luo_model.cash,
                    "x": luo_model.x,
                    "y": luo_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{zhang}",
                    "homeBuilding": zhang_model.home_building,
                    "asset": npc_configs.assets.index(zhang_model.asset),
                    "assetName": zhang_model.asset,
                    "model": zhang_model.model,
                    "memorySystem": zhang_model.memorySystem,
                    "planSystem": zhang_model.planSystem,
                    "workBuilding": zhang_model.work_building,
                    "nickname": zhang_model.name,
                    "bio": zhang_model.bio,
                    "goal": zhang_model.goal,
                    "cash": zhang_model.cash,
                    "x": zhang_model.x,
                    "y": zhang_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{wang}",
                    "homeBuilding": wang_model.home_building,
                    "asset": npc_configs.assets.index(wang_model.asset),
                    "assetName": wang_model.asset,
                    "model": wang_model.model,
                    "memorySystem": wang_model.memorySystem,
                    "planSystem": wang_model.planSystem,
                    "workBuilding": wang_model.work_building,
                    "nickname": wang_model.name,
                    "bio": wang_model.bio,
                    "goal": wang_model.goal,
                    "cash": wang_model.cash,
                    "x": wang_model.x,
                    "y": wang_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{ma}",
                    "homeBuilding": ma_model.home_building,
                    "asset": npc_configs.assets.index(ma_model.asset),
                    "assetName": ma_model.asset,
                    "model": ma_model.model,
                    "memorySystem": ma_model.memorySystem,
                    "planSystem": ma_model.planSystem,
                    "workBuilding": ma_model.work_building,
                    "nickname": ma_model.name,
                    "bio": ma_model.bio,
                    "goal": ma_model.goal,
                    "cash": ma_model.cash,
                    "x": ma_model.x,
                    "y": ma_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{cai}",
                    "homeBuilding": cai_model.home_building,
                    "asset": npc_configs.assets.index(cai_model.asset),
                    "assetName": cai_model.asset,
                    "model": cai_model.model,
                    "memorySystem": cai_model.memorySystem,
                    "planSystem": cai_model.planSystem,
                    "workBuilding": cai_model.work_building,
                    "nickname": cai_model.name,
                    "bio": cai_model.bio,
                    "goal": cai_model.goal,
                    "cash": cai_model.cash,
                    "x": cai_model.x,
                    "y": cai_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{li}",
                    "homeBuilding": li_model.home_building,
                    "asset": npc_configs.assets.index(li_model.asset),
                    "assetName": li_model.asset,
                    "model": li_model.model,
                    "memorySystem": li_model.memorySystem,
                    "planSystem": li_model.planSystem,
                    "workBuilding": li_model.work_building,
                    "nickname": li_model.name,
                    "bio": li_model.bio,
                    "goal": li_model.goal,
                    "cash": li_model.cash,
                    "x": li_model.x,
                    "y": li_model.y
                })
                npcs_info.append({
                    "uid": f"NPC-{song}",
                    "homeBuilding": song_model.home_building,
                    "asset": npc_configs.assets.index(song_model.asset),
                    "assetName": song_model.asset,
                    "model": song_model.model,
                    "memorySystem": song_model.memorySystem,
                    "planSystem": song_model.planSystem,
                    "workBuilding": song_model.work_building,
                    "nickname": song_model.name,
                    "bio": song_model.bio,
                    "goal": song_model.goal,
                    "cash": song_model.cash,
                    "x": song_model.x,
                    "y": song_model.y
                })

                model.save()
        else:
            print(uid, "login")
            player_model.login_time = self.get_nowtime()
            player_model.save()

            buildings_model = self.get_single_model("Buildings", create=False)
            if buildings_model:
                for building in buildings_model.buildings:
                    buildings_info.append(
                        {"building_id": building["id"], "building_type": building["t"], "name": building["n"],
                         "x": building["x"], "y": building["y"]})

            npcs_model = self.get_single_model("NPCs", create=False)
            if npcs_model:
                for npc in npcs_model.npcs:
                    npc_model = self.get_single_model("NPC", npc["id"], create=False)
                    if not npc_model:
                        continue
                    npcs_info.append({"uid": f'NPC-{npc["id"]}', "homeBuilding": npc_model.home_building,
                                      'asset': npc_configs.assets.index(npc_model.asset), "assetName": npc_model.asset,
                                      'model': npc_model.model, 'memorySystem': npc_model.memorySystem,
                                      'planSystem': npc_model.planSystem, 'workBuilding': npc_model.work_building,
                                      'nickname': npc_model.name, 'bio': npc_model.bio, 'goal': npc_model.goal,
                                      'cash': npc_model.cash, "x": npc_model.x, "y": npc_model.y})

        self.reg_eval(uid)
        return buildings_info, npcs_info

    def is_check_token(self):
        return False

# from command.command_base import CommandBase
# from agent.actor import Actor
#
#
# class LoginBase(CommandBase):
#
#     # # Batch NPC definitions: (name, x, y, asset, bio, goal)
#     # NPC_DEFS = [
#     #     # Teachers
#     #     {"nickname": "Dr. Lily Zhao", "x": 50, "y": 70, "asset": "premade_01",
#     #      "bio": "Dr. Lily Zhao is a highly sociable architecture professor who organizes group discussions frequently.",
#     #      "goal": "Go to the seminar room for a team meeting, then head to the lounge to chat."},
#     #     {"nickname": "Dr. Jun Wei", "x": 52, "y": 72, "asset": "premade_02",
#     #      "bio": "Dr. Jun Wei enjoys spontaneous hallway conversations and exploring new spaces.",
#     #      "goal": "Wander through common areas looking for colleagues to converse with."},
#     #     # ... (add remaining 22 definitions here) ...
#     # ]
#
#     def reg_npc(self, uid, nickname, x, y, asset, bio, goal):
#         account_model = self.get_model('NPCRegister')
#         # print(f'!!! when register npc uid: {uid}-{nickname}')
#         # print(f'!!! when register database: {account_model.get_db()}')
#         id = account_model.find_id(f'{uid}-{nickname}')
#         if id <= 0:
#             id = account_model.reg_npc(f'{uid}-{nickname}')
#             if id <= 0:
#                 return self.error('register npc failed')
#         npc_uid = self.gen_token("NPC", id)
#         npc_model = self.get_single_model("NPC", id=id, create=True)
#         npc_model.name = nickname
#         npc_model.map = self.id
#         # TODO: If agent use websocket connect with server
#         # Then don't set server and use this field to search npcs not linked
#         npc_model.server = npc_uid
#         npc_model.cash = 10000
#         npc_model.x = x
#         npc_model.y = y
#         npc_model.rotation = 0
#         npc_model.asset = asset
#         npc_model.save()
#
#         # buildings_model = self.get_single_model("Buildings", create=False)
#         buildings = ["dessert shop", "office", "houseZ", "park"]
#         # 改成自定义
#         model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
#         memorySystem = "LongShortTermMemories"
#         planSystem = "QAFramework"
#         npc_model.model = model
#         npc_model.memorySystem = memorySystem
#         npc_model.planSystem = planSystem
#         npc_model.bio = bio
#         npc_model.goal = goal
#         npc_model.home_building = 3
#         npc_model.work_building = 0
#         # if buildings_model:
#         #     buildings = buildings_model.get_names()
#         self.app.actors[npc_uid] = Actor(nickname, bio, goal, model, memorySystem, planSystem, buildings, 10000, self.app.last_game_time)
#         self.app.inited.add(npc_uid)
#         return id, npc_model
#
#     def reg_eval(self, uid):
#         for eval_des, eval_cfg in self.app.eval_configs.items():
#             eval_model = self.get_single_model('Eval', id=uid, create=True, eval_cfg=eval_cfg)
#             self.app.evals[eval_des] = eval_model
#         return eval_model
#
#
#     # Common login logic.
#     def handle_login(self, nickname, uid):
#         buildings_info = []
#         npcs_info = []
#         player_model = self.get_single_model('Player', create=False)
#         npc_configs = self.app.get_npc_config()
#
#         if player_model is None:
#             print(uid, "first login")
#
#             # 定义 24 个 NPC
#             # 在 handle_login 的首次登录分支前，插入：
#             # NPC_DEFS = [
#             #     # —— Teachers （6 个） ——
#             #     {
#             #         "name": "ProfLuoHanbin", "x": 50, "y": 70, "asset": "premade_01",
#             #         "bio": "LuoHanbin is an enthusiastic structural engineering professor. He enjoys spontaneous chats in atriums and often initiates conversations with colleagues.",
#             #         "goal": "Wander around the building after class, hoping to meet colleagues and exchange ideas."
#             #     },
#             #     {
#             #         "name": "ProfChenWeiya", "x": 51, "y": 71, "asset": "premade_02",
#             #         "bio": "ChenWeiya teaches environmental design and values planned meetings over informal talks.",
#             #         "goal": "Go to Offices to attend a faculty meeting, then head to the lounge for a short break."
#             #     },
#             #     {
#             #         "name": "DrGuoZhiyuan", "x": 51, "y": 72, "asset": "premade_03",
#             #         "bio": "GuoZhiyuan prefers a quiet office environment and avoids social interaction unless necessary.",
#             #         "goal": "Head straight to his office to prepare lecture slides for tomorrow’s class."
#             #     },
#             #     {
#             #         "name": "ProfZhouCheng", "x": 3, "y": 1, "asset": "premade_04",
#             #         "bio": "Prof. ZhouCheng balances teaching and socializing, but only in structured settings.",
#             #         "goal": "Submit documents at the department office, then take a brief coffee break."
#             #     },
#             #     {
#             #         "name": "DrZhangzhuohao", "x": 2, "y": 3, "asset": "premade_05",
#             #         "bio": "Dr. Zhangzhuohao engages in informal talks occasionally and likes to roam the atrium.",
#             #         "goal": "Explore student activity areas to observe and engage."
#             #     },
#             #     {
#             #         "name": "ProfDinglieyun", "x": 3, "y": 2, "asset": "premade_06",
#             #         "bio": "Prof. Dinglieyun is introverted and prefers avoiding crowds.",
#             #         "goal": "Go to his office to grade papers, avoiding unnecessary interactions."
#             #     },
#             #
#             #     # —— Students （6 个） ——
#             #     {
#             #         "name": "ZhangJiayuan", "x": 4, "y": 4, "asset": "premade_07",
#             #         "bio": "ZhangJiayuan is a lively graduate student who enjoys exploring the campus and chatting in communal areas.",
#             #         "goal": "Visit various common areas looking for classmates to study with."
#             #     },
#             #     {
#             #         "name": "WangZining", "x": 1, "y": 1, "asset": "premade_08",
#             #         "bio": "WangZining is focused on his research but often takes breaks in the atrium to decompress.",
#             #         "goal": "Head to the Offices first, then relax in the atrium before class."
#             #     },
#             #     {
#             #         "name": "LiWenpeng", "x": 0, "y": 2, "asset": "premade_09",
#             #         "bio": "LiWenpeng is a reserved undergraduate student who prefers solitude but occasionally walks through busy areas.",
#             #         "goal": "Take a walk around the building to find a quiet place to read."
#             #     },
#             #     {
#             #         "name": "MaJiangping", "x": 0, "y": 3, "asset": "premade_10",
#             #         "bio": "MaJiangping is an extroverted student active in clubs and group chats.",
#             #         "goal": "Head to the lounge to meet classmates before attending group study."
#             #     },
#             #     {
#             #         "name": "CaiJianhua", "x": 0, "y": 4, "asset": "premade_11",
#             #         "bio": "CaiJianhua loves to roam and strike up conversations with anyone she meets.",
#             #         "goal": "Walk around looking for classmates to hang out with."
#             #     },
#             #     {
#             #         "name": "SongJunbo", "x": 1, "y": 4, "asset": "premade_12",
#             #         "bio": "SongJunbo is a quiet student serious about his academics, avoids small talk.",
#             #         "goal": "Go directly to the classroom, avoiding lingering in public areas."
#             #     },
#             #
#             #     # —— Staff （6 个） ——
#             #     {
#             #         "name": "ZhangYizhe", "x": 1, "y": 0, "asset": "premade_13",
#             #         "bio": "ZhangYizhe is a friendly administrative officer who often chats while delivering documents.",
#             #         "goal": "Deliver files to Room 203 and chat briefly with familiar staff in the corridor."
#             #     },
#             #     {
#             #         "name": "WangXiaoyang", "x": 1, "y": 3, "asset": "premade_14",
#             #         "bio": "WangXiaoyang enjoys casually greeting coworkers during breaks and occasionally changes her walking route.",
#             #         "goal": "Take an informal walk during lunch break and greet colleagues."
#             #     },
#             #     {
#             #         "name": "KongYue", "x": 1, "y": 2, "asset": "premade_15",
#             #         "bio": "KongYue keeps a balance between work tasks and small social interactions.",
#             #         "goal": "Head to the copy room, may stop for brief corridor conversations."
#             #     },
#             #     {
#             #         "name": "RenZhuo", "x": 2, "y": 1, "asset": "premade_16",
#             #         "bio": "RenZhuo occasionally takes informal walks to refresh her mind.",
#             #         "goal": "Walk freely around common areas to relax."
#             #     },
#             #     {
#             #         "name": "WangZhonghao", "x": 2, "y": 2, "asset": "premade_17",
#             #         "bio": "WangZhonghao is focused and avoids chit-chat.",
#             #         "goal": "Go to the supply room and return without delay."
#             #     },
#             #     {
#             #         "name": "LiLinfan", "x": 2, "y": 0, "asset": "premade_18",
#             #         "bio": "LiLinfan observes people quietly and rarely interacts.",
#             #         "goal": "Meander through corridors, keeping a low profile."
#             #     },
#             #
#             #     # —— Visitors （6 个） ——
#             #     {
#             #         "name": "MeiZhang", "x": 4, "y": 0, "asset": "premade_19",
#             #         "bio": "Mrs. Mei Zhang is a curious visitor attending an open day. She loves asking questions and meeting new people.",
#             #         "goal": "Explore the lobby and lounges, hoping to interact with students or staff."
#             #     },
#             #     {
#             #         "name": "TomLiu", "x": 4, "y": 3, "asset": "premade_20",
#             #         "bio": "Mr. Tom Liu is here for a scheduled meeting and is open to chatting if approached.",
#             #         "goal": "Locate Room 108 for a meeting, then briefly check out the atrium."
#             #     },
#             #     {
#             #         "name": "FionaYang", "x": 4, "y": 2, "asset": "premade_21",
#             #         "bio": "Miss Fiona Yang is a prospective graduate student visiting quietly, observing without much interaction.",
#             #         "goal": "Walk around the building, silently observing student life and space usage."
#             #     },
#             #     {
#             #         "name": "StevenXie", "x": 3, "y": 2, "asset": "premade_22",
#             #         "bio": "Mr. Steven Xie is an outgoing prospective collaborator who loves networking.",
#             #         "goal": "Visit lab office, talk to people in the hallway."
#             #     },
#             #     {
#             #         "name": "EmilyGao", "x": 3, "y": 0, "asset": "premade_23",
#             #         "bio": "Ms. Emily Gao is a friendly guest curious about building culture.",
#             #         "goal": "Tour the atrium and chat with students."
#             #     },
#             #     {
#             #         "name": "MarkNie", "x": 3, "y":4 , "asset": "premade_24",
#             #         "bio": "Mr. Mark Nie is on a brief visit and prefers to keep to himself.",
#             #         "goal": "Head to the front desk, then exit immediately."
#             #     },
#             # ]
#             NPC_DEFS = [
#                 # 1. DrAlanChen (教师+高社交+任务导向)
#                 {
#                     "name": "DrGuoZhiyuan", "x": 0, "y": 0, "asset": "premade_01",
#                     "bio": "Dr. GuoZhiyuan is an enthusiastic structural engineering professor. He enjoys spontaneous chats in atriums and often initiates conversations with colleagues.",
#                     "goal": "Wander around the building after class, hoping to meet colleagues and exchange ideas."
#                 },
#                 # 2. ProfTomQian (教师+低社交+探索型)
#                 {
#                     "name": "ProfChenWeiya", "x": 0, "y": 0, "asset": "premade_02",
#                     "bio": "Prof. ProfChenWeiya is introverted and prefers avoiding crowds.",
#                     "goal": "Go to his office to grade papers, avoiding unnecessary interactions."
#                 },
#                 # 3. AdaChen (学生+高社交+探索型)
#                 {
#                     "name": "ZhangJiaYuan", "x": 0, "y": 3, "asset": "premade_03",
#                     "bio": "ZhangJiaYuan loves to roam and strike up conversations with anyone she meets.",
#                     "goal": "Walk around looking for classmates to hang out with."
#                 },
#                 # 4. NickLin (学生+低社交+任务导向)
#                 {
#                     "name": "WangZining", "x": 0, "y": 3, "asset": "premade_04",
#                     "bio": "WangZining is a quiet student serious about his academics, avoids small talk.",
#                     "goal": "Go directly to the classroom, avoiding lingering in public areas."
#                 },
#                 # 5. DavidLin (职员+高社交+任务导向)
#                 {
#                     "name": "MaJiangping", "x": 3, "y": 0, "asset": "premade_05",
#                     "bio": "Mr. MaJiangping is a friendly administrative officer who often chats while delivering documents.",
#                     "goal": "Deliver files to Room 203 and chat briefly with familiar staff in the corridor."
#                 },
#                 # 6. SophieCheng (职员+低社交+探索型)
#                 {
#                     "name": "CaiJianhua", "x": 3, "y": 0, "asset": "premade_06",
#                     "bio": "Ms. CaiJianhua observes people quietly and rarely interacts.",
#                     "goal": "Meander through corridors, keeping a low profile."
#                 },
#                 # 7. TomLiu (访客+中社交+任务导向)
#                 {
#                     "name": "LiWenpeng", "x": 3, "y": 3, "asset": "premade_07",
#                     "bio": "Mr. LiWenpeng is here for a scheduled meeting and is open to chatting if approached.",
#                     "goal": "Locate Room 108 for a meeting, then briefly check out the atrium."
#                 },
#                 # 8. EmilyGao (访客+高社交+探索型)
#                 {
#                     "name": "SongJunbo", "x": 3, "y": 3, "asset": "premade_08",
#                     "bio": "Ms. SongJunbo is a friendly guest curious about building culture.",
#                     "goal": "Tour the atrium and chat with students."
#                 },
#             ]
#
#             # 然后接着 for defn in NPC_DEFS: 调用 self.reg_npc(...)
#
#             # 注册所有 NPC
#             npc_ids = []
#             npc_models = []
#             for defn in NPC_DEFS:
#                 npc_id, npc_model = self.reg_npc(uid, defn["name"], defn["x"], defn["y"], defn["asset"], defn["bio"], defn["goal"])
#                 npc_ids.append(npc_id)
#                 npc_models.append(npc_model)
#
#             models = ['Player', 'Map', 'Town', 'Buildings', 'Equipments', 'NPCs']
#             for model_name in models:
#                 model = self.get_single_model(model_name)
#                 model.init()
#
#                 if model_name == "Player":
#                     model.name = nickname
#                     model.x = 71
#                     model.y = 41
#
#                 if model_name == "Map":
#                     model.init_map()
#                     model.add_uid(71, 41, uid, nickname)
#
#                     # 这里替换成动态遍历 NPC_DEFS
#                     for idx, npc_id in enumerate(npc_ids):
#                         defn = NPC_DEFS[idx]
#                         model.add_uid(
#                             defn["x"], defn["y"],
#                             f"NPC-{npc_id}", defn["name"]
#                         )
#
#                 # if model_name == "Map":
#                 #     model.init_map()
#                 #     model.add_uid(71, 41, uid, nickname)
#                 #     for npc_id, npc_name in npc_ids:
#                 #         model.add_uid(50, 70, f"NPC-{npc_id}", npc_name)
#                 # if model_name == "Buildings":
#                 #     model.init_buildings()
#                 #     for building in model.buildings:
#                 #         if building["lC"] > 0:
#                 #             for npc_id, _ in npc_ids:
#                 #                 model.add_tenent(building["id"], npc_id)
#                 #         buildings_info.append({
#                 #             "building_id": building["id"], "building_type": building["t"],
#                 #             "name": building["n"], "x": building["x"], "y": building["y"]
#                 #         })
#                 if model_name == "Buildings":
#                     model.init_buildings()
#                     for building in model.buildings:
#                         if building["lC"] > 0:
#                             for npc_id in npc_ids:
#                                 model.add_tenent(building["id"], npc_id)
#                         buildings_info.append({
#                             "building_id": building["id"],
#                             "building_type": building["t"],
#                             "name": building["n"],
#                             "x": building["x"],
#                             "y": building["y"]
#                         })
#
#                 if model_name == "Equipments":
#                     model.init_equipments()
#
#                 if model_name == "NPCs":
#                     model.npcs = [{"id": npc_ids[i][0], "name": npc_ids[i][1]} for i in range(len(npc_ids))]
#                     for i, npc_model in enumerate(npc_models):
#                         defn = NPC_DEFS[i]
#                         npcs_info.append({
#                             "uid": f"NPC-{npc_ids[i]}",
#                             "homeBuilding": npc_model.home_building,
#                             "asset": npc_configs.assets.index(npc_model.asset),
#                             "assetName": npc_model.asset,
#                             "model": npc_model.model,
#                             "memorySystem": npc_model.memorySystem,
#                             "planSystem": npc_model.planSystem,
#                             "workBuilding": npc_model.work_building,
#                             "nickname": defn["name"],
#                             "bio": defn["bio"],
#                             "goal": defn["goal"],
#                             "cash": npc_model.cash,
#                             "x": defn["x"],
#                             "y": defn["y"]
#                         })
#                         # npcs_info.append({
#                         #     "uid": f"NPC-{npc_ids[i][0]}",
#                         #     "homeBuilding": npc_model.home_building,
#                         #     'asset': npc_configs.assets.index(npc_model.asset),
#                         #     "assetName": npc_model.asset,
#                         #     'model': npc_model.model,
#                         #     'memorySystem': npc_model.memorySystem,
#                         #     'planSystem': npc_model.planSystem,
#                         #     'workBuilding': npc_model.work_building,
#                         #     'nickname': npc_model.name,
#                         #     'bio': npc_model.bio,
#                         #     'goal': npc_model.goal,
#                         #     'cash': npc_model.cash,
#                         #     "x": npc_model.x,
#                         #     "y": npc_model.y
#                         # })
#
#                 model.save()
#         else:
#             print(uid, "login")
#             player_model.login_time = self.get_nowtime()
#             player_model.save()
#
#             buildings_model = self.get_single_model("Buildings", create=False)
#             if buildings_model:
#                 for building in buildings_model.buildings:
#                     buildings_info.append({
#                         "building_id": building["id"], "building_type": building["t"],
#                         "name": building["n"], "x": building["x"], "y": building["y"]
#                     })
#
#             npcs_model = self.get_single_model("NPCs", create=False)
#             if npcs_model:
#                 for npc in npcs_model.npcs:
#                     npc_model = self.get_single_model("NPC", npc["id"], create=False)
#                     if not npc_model:
#                         continue
#                     npcs_info.append({
#                         "uid": f'NPC-{npc["id"]}',
#                         "homeBuilding": npc_model.home_building,
#                         'asset': npc_configs.assets.index(npc_model.asset),
#                         "assetName": npc_model.asset,
#                         'model': npc_model.model,
#                         'memorySystem': npc_model.memorySystem,
#                         'planSystem': npc_model.planSystem,
#                         'workBuilding': npc_model.work_building,
#                         'nickname': npc_model.name,
#                         'bio': npc_model.bio,
#                         'goal': npc_model.goal,
#                         'cash': npc_model.cash,
#                         "x": npc_model.x,
#                         "y": npc_model.y
#                     })
#
#         self.reg_eval(uid)
#         return buildings_info, npcs_info
#             # print(uid, "first login")
#             # alan, alan_model = self.reg_npc(uid, "Alan", 50, 71, "premade_01", "Alan is a genius with outstanding talents and is the inventor of computer. Alan has an introverted personality and is only interested in the research he foucues on.", "Promoting the Process of Computer Research")
#             # fei, fei_model = self.reg_npc(uid, "pH", 52, 73, "premade_04", "pH is a positive, cheerful, optimistic but somewhat crazy girl who dares to try and explore. She loves food, loves life, and hopes to bring happiness to everyone.", "Taste all the delicious food and become a gourmet or chef.")
#             # wangzining, wangzining_model = self.reg_npc(uid, "wangzining", 55, 80, "premade_08",
#             #                               "wangzining is a positive, cheerful, optimistic man who dares to try and explore. He loves study, loves life, and hopes to study as he can.",
#             #                               "Study all the time as he can, unless he is tired.")
#         #     models = [
#         #         'Player',
#         #         'Map',
#         #         'Town',
#         #         'Buildings',
#         #         'Equipments',
#         #         'NPCs',
#         #     ]
#         #     for model_name in models:
#         #         model = self.get_single_model(model_name)
#         #         # if model_name == "NPCs":
#         #             # last_npcs = model.npcs
#         #             # for nid in last_npcs:
#         #             #     nuid = self.gen_token("NPC", nid)
#         #             #     if nuid in self.app.movings:
#         #             #         self.app.movings.remove(nuid)
#         #             #     if nuid in self.app.chatted:
#         #             #         self.app.chatted.remove(nuid)
#         #             #     if nuid in self.app.using:
#         #             #         self.app.using.remove(nuid)
#         #             #     if nuid in self.app.inited:
#         #             #         self.app.inited.remove(nuid)
#         #             #     self.app.cache = [c for c in self.app.cache if c["uid"] != nuid]
#         #             #     if nuid in self.app.actors:
#         #             #         del self.app.actors[nuid]
#         #         model.init()
#         #         if model_name == "Player":
#         #             model.name = nickname
#         #             model.x = 71
#         #             model.y = 41
#         #         if model_name == "Map":
#         #             model.init_map()
#         #             model.add_uid(71, 41, uid, nickname)
#         #             model.add_uid(50, 71, f"NPC-{alan}", "Alan")
#         #             model.add_uid(52, 73, f"NPC-{fei}", "Fei")
#         #             model.add_uid(55, 80, f"NPC-{wangzining}", "wangzining")
#         #         if model_name == "Buildings":
#         #             model.init_buildings()
#         #             for building in model.buildings:
#         #                 if building["lC"] > 0:
#         #                     model.add_tenent(building["id"], alan)
#         #                     model.add_tenent(building["id"], fei)
#         #                     model.add_tenent(building["id"], wangzining)
#         #                 buildings_info.append({"building_id": building["id"], "building_type": building["t"], "name": building["n"], "x": building["x"], "y": building["y"]})
#         #         if model_name == "Equipments":
#         #             model.init_equipments()
#         #         if model_name == "NPCs":
#         #             model.npcs = [{"id": alan, "name": "Alan"}, {"id": fei, "name": "Fei"}, {"id": wangzining, "name": "wangzining"}]
#         #             # for npc in model.npcs:
#         #             #     npc_model = self.get_single_model("NPC", npc["id"], create=False)
#         #             #     if not npc_model:
#         #             #         continue
#         #             #     home_building = self.get_single_model("Buildings", create=True).get_building(npc_model.home_building)
#         #             #     if not home_building:
#         #             #         continue
#         #             npcs_info.append({"uid": f"NPC-{alan}", "homeBuilding": alan_model.home_building, 'asset': npc_configs.assets.index(alan_model.asset), "assetName": alan_model.asset, 'model': alan_model.model, 'memorySystem': alan_model.memorySystem, 'planSystem': alan_model.planSystem, 'workBuilding': alan_model.work_building, 'nickname': alan_model.name, 'bio': alan_model.bio, 'goal': alan_model.goal, 'cash': alan_model.cash, "x": alan_model.x, "y": alan_model.y})
#         #             npcs_info.append({"uid": f"NPC-{fei}", "homeBuilding": fei_model.home_building, 'asset': npc_configs.assets.index(fei_model.asset), "assetName": fei_model.asset, 'model': fei_model.model, 'memorySystem': fei_model.memorySystem, 'planSystem': fei_model.planSystem, 'workBuilding': fei_model.work_building, 'nickname': fei_model.name, 'bio': fei_model.bio, 'goal': fei_model.goal, 'cash': fei_model.cash, "x": fei_model.x, "y": fei_model.y})
#         #             npcs_info.append({"uid": f"NPC-{wangzining}", "homeBuilding": wangzining_model.home_building,
#         #                           'asset': npc_configs.assets.index(wangzining_model.asset), "assetName": wangzining_model.asset,
#         #                           'model': wangzining_model.model, 'memorySystem': wangzining_model.memorySystem,
#         #                           'planSystem': wangzining_model.planSystem, 'workBuilding': wangzining_model.work_building,
#         #                           'nickname': wangzining_model.name, 'bio': wangzining_model.bio, 'goal': wangzining_model.goal,
#         #                           'cash': wangzining_model.cash, "x": wangzining_model.x, "y": wangzining_model.y})
#         #
#         #         model.save()
#         # else:
#         #     print(uid, "login")
#         #     player_model.login_time = self.get_nowtime()
#         #     player_model.save()
#         #
#         #     buildings_model = self.get_single_model("Buildings", create=False)
#         #     if buildings_model:
#         #         for building in buildings_model.buildings:
#         #             buildings_info.append({"building_id": building["id"], "building_type": building["t"], "name": building["n"], "x": building["x"], "y": building["y"]})
#         #
#         #     npcs_model = self.get_single_model("NPCs", create=False)
#         #     if npcs_model:
#         #         for npc in npcs_model.npcs:
#         #             npc_model = self.get_single_model("NPC", npc["id"], create=False)
#         #             if not npc_model:
#         #                 continue
#         #             npcs_info.append({"uid": f'NPC-{npc["id"]}', "homeBuilding": npc_model.home_building, 'asset': npc_configs.assets.index(npc_model.asset), "assetName": npc_model.asset, 'model': npc_model.model, 'memorySystem': npc_model.memorySystem, 'planSystem': npc_model.planSystem, 'workBuilding': npc_model.work_building, 'nickname': npc_model.name, 'bio': npc_model.bio, 'goal': npc_model.goal, 'cash': npc_model.cash, "x": npc_model.x, "y": npc_model.y})
#         #
#         # self.reg_eval(uid)
#         # return buildings_info, npcs_info
#
#     def is_check_token(self):
#         return False
