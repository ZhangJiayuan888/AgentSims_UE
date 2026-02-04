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

        npc_model.server = npc_uid
        npc_model.cash = 10000
        npc_model.x = x
        npc_model.y = y
        npc_model.rotation = 0
        npc_model.asset = asset
        npc_model.save()

        # buildings_model = self.get_single_model("Buildings", create=False)
        buildings = ["dessert shop", "office", "houseZ", "park"]

        # 自定义模型配置
        model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        memorySystem = "LongShortTermMemories"
        planSystem = "QAFramework"

        npc_model.model = model
        npc_model.memorySystem = memorySystem
        npc_model.planSystem = planSystem
        npc_model.bio = bio
        npc_model.goal = goal
        # 设置默认居住地和工作地
        npc_model.home_building = 3
        npc_model.work_building = 0

        # 内存初始化：实例化 Actor
        self.app.actors[npc_uid] = Actor(nickname, bio, goal, model, memorySystem, planSystem, buildings, 10000,
                                         self.app.last_game_time)
        self.app.inited.add(npc_uid)

        # 返回 ID 和 模型，供后续 Map/Building 注册使用
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

        # === 30个智能体配置列表 (坐标已分散) ===
        agent_configs = [
            # 1. 沉浸专注型 (Quiet Zones: HouseZ, Remote Park)
            {"name": "SongJunbo", "x": 26, "y": 44, "asset": "premade_01",
             "bio": "Physics PhD. High noise sensitivity. Requires absolute isolation.",
             "goal": "Find the most silent corner in HouseZ to think deeply for 3 hours."},
            {"name": "ZhaoLei", "x": 28, "y": 46, "asset": "premade_08",
             "bio": "Medical Student. Rote learner. Carrying heavy books.",
             "goal": "Find an ergonomic chair in a well-lit area of HouseZ to memorize anatomy."},
            {"name": "LiWenpeng", "x": 30, "y": 48, "asset": "premade_20",
             "bio": "Traditional Scholar. Dislikes open spaces.",
             "goal": "Find a spot in HouseZ that feels like a library carrel."},
            {"name": "ZhangJiayuan", "x": 32, "y": 50, "asset": "premade_22",
             "bio": "Grad student. Deadline in 2 hours.", "goal": "Find any seat immediately to type furiously."},
            {"name": "WangXiaoyang", "x": 34, "y": 52, "asset": "premade_02", "bio": "Researcher. Multi-device user.",
             "goal": "Find a large table in HouseZ to spread out laptop and papers."},
            {"name": "ZhangYizhe", "x": 10, "y": 80, "asset": "premade_05",
             "bio": "Literature Student. Seeks aesthetics.", "goal": "Find a scenic spot in the Park to read poetry."},
            {"name": "KongYue", "x": 12, "y": 82, "asset": "premade_21", "bio": "Musician. Auditory learner.",
             "goal": "Sit in the Park facing a wall to minimize visual distraction."},
            {"name": "LiLinfan", "x": 14, "y": 84, "asset": "premade_03", "bio": "Job Seeker. Anxious.",
             "goal": "Find a secluded corner in the Park to practice interview answers."},

            # 2. 协作交互型 (Social Zones: Dessert Shop, Park Central)
            {"name": "WangZhonghao", "x": 55, "y": 60, "asset": "premade_06",
             "bio": "Startup Founder. Loud and dominant.", "goal": "Hold a loud strategy session in the Dessert Shop."},
            {"name": "RenZhuo", "x": 57, "y": 62, "asset": "premade_07", "bio": "Follower. Anxious in chaos.",
             "goal": "Find Mike in the Dessert Shop for the meeting."},
            {"name": "LinGuangting", "x": 60, "y": 65, "asset": "premade_12",
             "bio": "Model Maker. Messy with glue.",
             "goal": "Find a large table in the Dessert Shop to assemble a model."},
            {"name": "GuoZhiyuan", "x": 62, "y": 67, "asset": "premade_13", "bio": "Critic. Loves debate.",
             "goal": "Find Student A to critique their model design."},
            {"name": "Li_Hua", "x": 65, "y": 70, "asset": "premade_03", "bio": "Student Union President. Extroverted.",
             "goal": "Wander high-traffic areas of Dessert Shop to greet people."},
            {"name": "KeMeixiang", "x": 68, "y": 72, "asset": "premade_16", "bio": "Peer Tutor. Wants to be visible.",
             "goal": "Sit in a visible spot in the Dessert Shop to wait for students."},
            {"name": "Alice", "x": 70, "y": 74, "asset": "premade_17", "bio": "Struggling Student. Panicked.",
             "goal": "Search the Dessert Shop for Tutor John."},

            # 3. 休闲社交型 (Transit Zones, Cafe)
            {"name": "Zhang_Wei", "x": 80, "y": 20, "asset": "premade_04",
             "bio": "CS Undergrad. Needs power and caffeine.",
             "goal": "Find a spot with a power outlet and coffee in the Dessert Shop."},
            {"name": "ChenLang", "x": 82, "y": 22, "asset": "premade_14", "bio": "Connoisseur. Judgemental.",
             "goal": "Sip a premium coffee and judge the cafe's interior."},
            {"name": "WangZining", "x": 84, "y": 24, "asset": "premade_15", "bio": "Exhausted. Needs rest.",
             "goal": "Find a soft sofa in the Dessert Shop to nap."},
            {"name": "CaiJianhua", "x": 86, "y": 26, "asset": "premade_18", "bio": "Boyfriend. Focused on intimacy.",
             "goal": "Find a private table to talk romantically."},
            {"name": "MaJiangping", "x": 88, "y": 28, "asset": "premade_19",
             "bio": "Girlfriend. Socially performative.", "goal": "Take cute photos in the Dessert Shop."},
            {"name": "ZhaoZheng", "x": 50, "y": 50, "asset": "premade_09", "bio": "Freshman. Lonely.",
             "goal": "Sit in the crowd at the Park just to feel present."},
            {"name": "YangZhaoyu", "x": 52, "y": 52, "asset": "premade_11", "bio": "Casual Gamer. Lazy.",
             "goal": "Slouch on a bench in the Park and play mobile games."},
            {"name": "LiuChang", "x": 54, "y": 54, "asset": "premade_24", "bio": "Wellness Enthusiast.",
             "goal": "Find open space in the Park to stretch."},
            {"name": "YuanJiameng", "x": 56, "y": 56, "asset": "premade_25", "bio": "Business Student. Loud.",
             "goal": "Pace around the Park talking loudly on the phone."},
            {"name": "LiBoyu", "x": 58, "y": 58, "asset": "premade_26", "bio": "Visual Artist. Observer.",
             "goal": "Find a vantage point in the Park to sketch people."},
            {"name": "GuanTao", "x": 40, "y": 40, "asset": "premade_01", "bio": "New Student. Disoriented.",
             "goal": "Wander between buildings looking for signs."},

            # 4. 管理与观察型 (Admin/Staff)
            {"name": "Prof_ChenWeiya", "x": 5, "y": 10, "asset": "premade_02", "bio": "Architecture Professor. Researcher.",
             "goal": "Patrol campus to observe furniture usage."},
            {"name": "Prof_Liu", "x": 20, "y": 10, "asset": "premade_10", "bio": "Administrator. Rule enforcer.",
             "goal": "Patrol public areas to enforce rules."},
            {"name": "Prof_Bob", "x": 25, "y": 15, "asset": "premade_04", "bio": "Janitor. Friendly.",
             "goal": "Clean public areas and greet students."},
            {"name": "Admin_Zhang", "x": 30, "y": 20, "asset": "premade_23", "bio": "Parent. Critical evaluator.",
             "goal": "Inspect facilities for safety and quality."}
        ]

        if player_model is None:
            print(uid, "first login - Initializing Experiment Agents")

            registered_npcs = []

            # 1. 批量注册 NPC
            for cfg in agent_configs:
                try:
                    nid, n_model = self.reg_npc(
                        uid, cfg["name"], cfg["x"], cfg["y"], cfg["asset"], cfg["bio"], cfg["goal"]
                    )
                    registered_npcs.append({"id": nid, "model": n_model})
                    print(f"Registered Agent: {cfg['name']} (ID: {nid})")
                except Exception as e:
                    print(f"Error registering {cfg['name']}: {e}")

            # 2. 初始化各个系统模型
            models = ['Player', 'Map', 'Town', 'Buildings', 'Equipments', 'NPCs']

            for model_name in models:
                model = self.get_single_model(model_name)
                model.init()

                if model_name == "Player":
                    model.name = nickname
                    model.x = 71
                    model.y = 41

                if model_name == "Map":
                    model.init_map()
                    model.add_uid(71, 41, uid, nickname)

                    # [修复] 将 NPC 加入地图
                    for npc_entry in registered_npcs:
                        nid = npc_entry["id"]
                        n_model = npc_entry["model"]
                        model.add_uid(n_model.x, n_model.y, f"NPC-{nid}", n_model.name)

                if model_name == "Buildings":
                    model.init_buildings()
                    for building in model.buildings:
                        if building["lC"] > 0:
                            # [修复] 将 NPC 加入建筑租户
                            for npc_entry in registered_npcs:
                                nid = npc_entry["id"]
                                model.add_tenent(building["id"], nid)

                        buildings_info.append(
                            {"building_id": building["id"], "building_type": building["t"], "name": building["n"],
                             "x": building["x"], "y": building["y"]})

                if model_name == "Equipments":
                    model.init_equipments()

                if model_name == "NPCs":
                    # [修复] 构建 NPCsModel 列表
                    model.npcs = []
                    for npc_entry in registered_npcs:
                        model.npcs.append({"id": npc_entry["id"], "name": npc_entry["model"].name})

                    model.save()

                    # [关键修复 !!!] 填充 npcs_info 以便首次登录返回给客户端
                    # 如果缺少这一步，UE 将收不到 NPC 列表，导致画面上没人
                    for npc_entry in registered_npcs:
                        n_model = npc_entry["model"]
                        nid = npc_entry["id"]
                        npcs_info.append({
                            "uid": f'NPC-{nid}',
                            "homeBuilding": n_model.home_building,
                            'asset': npc_configs.assets.index(n_model.asset),
                            "assetName": n_model.asset,
                            'model': n_model.model,
                            'memorySystem': n_model.memorySystem,
                            'planSystem': n_model.planSystem,
                            'workBuilding': n_model.work_building,
                            'nickname': n_model.name,
                            'bio': n_model.bio,
                            'goal': n_model.goal,
                            'cash': n_model.cash,
                            "x": n_model.x,
                            "y": n_model.y
                        })

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
                    # 构建返回给客户端的信息
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
#         self.app.actors[npc_uid] = Actor(nickname, bio, goal, model, memorySystem, planSystem, buildings, 10000,
#                                          self.app.last_game_time)
#         self.app.inited.add(npc_uid)
#         return id, npc_model
#
#     def reg_eval(self, uid):
#         for eval_des, eval_cfg in self.app.eval_configs.items():
#             eval_model = self.get_single_model('Eval', id=uid, create=True, eval_cfg=eval_cfg)
#             self.app.evals[eval_des] = eval_model
#         return eval_model
#
#     # Common login logic.
#     def handle_login(self, nickname, uid):
#         buildings_info = []
#         npcs_info = []
#         player_model = self.get_single_model('Player', create=False)
#         npc_configs = self.app.get_npc_config()
#         # First time login, create all data to avoid creating them in scene server.
#         # Otherwise, to update login time.
#         if player_model is None:
#             print(uid, "first login")
#             # alan, alan_model = self.reg_npc(uid, "ProfChenWeiya", 0, 12, "premade_01",
#             #                                 "ChenWeiya is a structural engineering professor who enjoys sparking conversations in the atrium.",
#             #                                 "Wander the atrium after class to meet colleagues and discuss research.")
#             # fei, fei_model = self.reg_npc(uid, "pH", 5, 13, "premade_02",
#             #                               "Tom is an introverted professor who prefers to avoid crowds.",
#             #                               "Head straight to his office to grade papers, minimizing social interactions.")
#             # wangzining, wangzining_model = self.reg_npc(uid, "wangzining", 55, 80, "premade_03",
#             #                                             "Ada is an outgoing student who loves chatting with anyone she meets.",
#             #                                             "Study all the time as he can, unless he is tired.")
#
#             chen, chen_model = self.reg_npc(uid, "ProfChenWeiya", 5, 10, "premade_01",
#                                             "Chen Weiya is a structural engineering professor who enjoys sparking conversations in the rest area.",
#                                             "Wander the rest area after class to meet colleagues or students and discuss research.")
#
#             zhou, zhou_model = self.reg_npc(uid, "ProfZhouCheng", 4, 8, "premade_02",
#                                             "Zhou Cheng is a civil engineering professor known for his engaging office hours.",
#                                             "Hold impromptu Q&A sessions in the lounge to help students with their projects.")
#
#             luo, luo_model = self.reg_npc(uid, "ProfLuohanbin", 20, 10, "premade_03",
#                                           "Luo Hanbin is an introverted professor who prefers small-group discussions.",
#                                           "Seek out one or two colleagues for deep technical talks in quiet corners.")
#
#             # Students
#             zhang, zhang_model = self.reg_npc(uid, "ZhangJiayuan", 20, 16, "premade_04",
#                                               "Zhang Jiayuan is an outgoing student who loves exploring public spaces.",
#                                               "Roam the rest area to find classmates for group study sessions.")
#
#             wang, wang_model = self.reg_npc(uid, "WangZining", 77, 52, "premade_05",
#                                             "Wang Zining is a serious student who keeps to herself.",
#                                             "Head straight to the office and avoid idle chit-chat.")
#
#             ma, ma_model = self.reg_npc(uid, "MaJiangping", 51, 63, "premade_06",
#                                         "Ma Jiangping is a curious student who enjoys spontaneous meetups.",
#                                         "Wander through the corridor looking for chance encounters with peers.")
#
#             # Staff
#             cai, cai_model = self.reg_npc(uid, "CaiJianhua", 59, 59, "premade_07",
#                                           "Cai Jianhua is a friendly administrator who chats while on duty.",
#                                           "Deliver mail across offices and greet colleagues in the hallway.")
#
#             li, li_model = self.reg_npc(uid, "LiWenpeng", 77, 77, "premade_08",
#                                         "Li Wenpeng is a no-nonsense staff member focused on efficiency.",
#                                         "Move directly between offices to complete tasks with minimal stops.")
#             song, song_model = self.reg_npc(uid, "SongJunbo", 26, 44, "premade_09",
#                                         "SongJunbo is a task-oriented scholar limiting social engagement to essentials, pursuing maximally efficient routes.",
#                                         "Take shortest path from study room to advisor's office for thesis consultation while declining all non-essential interactions during transit.")
#
#             models = [
#                 'Player',
#                 'Map',
#                 'Town',
#                 'Buildings',
#                 'Equipments',
#                 'NPCs',
#             ]
#             for model_name in models:
#                 model = self.get_single_model(model_name)
#                 # if model_name == "NPCs":
#                 # last_npcs = model.npcs
#                 # for nid in last_npcs:
#                 #     nuid = self.gen_token("NPC", nid)
#                 #     if nuid in self.app.movings:
#                 #         self.app.movings.remove(nuid)
#                 #     if nuid in self.app.chatted:
#                 #         self.app.chatted.remove(nuid)
#                 #     if nuid in self.app.using:
#                 #         self.app.using.remove(nuid)
#                 #     if nuid in self.app.inited:
#                 #         self.app.inited.remove(nuid)
#                 #     self.app.cache = [c for c in self.app.cache if c["uid"] != nuid]
#                 #     if nuid in self.app.actors:
#                 #         del self.app.actors[nuid]
#                 model.init()
#                 if model_name == "Player":
#                     model.name = nickname
#                     model.x = 71
#                     model.y = 41
#                 if model_name == "Map":
#                     model.init_map()
#                     model.add_uid(71, 41, uid, nickname)
#                     # model.add_uid(50, 71, f"NPC-{alan}", "Alan")
#                     # model.add_uid(52, 73, f"NPC-{fei}", "Fei")
#                     # model.add_uid(55, 80, f"NPC-{wangzining}", "wangzining")
#                     model.add_uid(5, 10, f"NPC-{chen}", "ProfChenWeiya")
#                     model.add_uid(4, 8, f"NPC-{zhou}", "ProfZhouCheng")
#                     model.add_uid(20, 10, f"NPC-{luo}", "ProfLuohanbin")
#                     # Place Students
#                     model.add_uid(20, 16, f"NPC-{zhang}", "ZhangJiayuan")
#                     model.add_uid(77, 52, f"NPC-{wang}", "WangZining")
#                     model.add_uid(51, 63, f"NPC-{ma}", "MaJiangping")
#                     # Place Staff
#                     model.add_uid(59, 59, f"NPC-{cai}", "CaiJianhua")
#                     model.add_uid(77, 77, f"NPC-{li}", "LiWenpeng")
#                     model.add_uid(26, 44, f"NPC-{song}", "SongJunbo")
#                 if model_name == "Buildings":
#                     model.init_buildings()
#                     for building in model.buildings:
#                         if building["lC"] > 0:
#                             # model.add_tenent(building["id"], alan)
#                             # model.add_tenent(building["id"], fei)
#                             # model.add_tenent(building["id"], wangzining)
#                             model.add_tenent(building["id"], chen)
#                             model.add_tenent(building["id"], zhou)
#                             model.add_tenent(building["id"], luo)
#                             model.add_tenent(building["id"], zhang)
#                             model.add_tenent(building["id"], wang)
#                             model.add_tenent(building["id"], ma)
#                             model.add_tenent(building["id"], cai)
#                             model.add_tenent(building["id"], li)
#                             model.add_tenent(building["id"], song)
#                         buildings_info.append(
#                             {"building_id": building["id"], "building_type": building["t"], "name": building["n"],
#                              "x": building["x"], "y": building["y"]})
#                 if model_name == "Equipments":
#                     model.init_equipments()
#                 if model_name == "NPCs":
#                     # model.npcs = [{"id": alan, "name": "Alan"}, {"id": fei, "name": "Fei"},
#                     #               {"id": wangzining, "name": "wangzining"}]
#                     model.npcs = [
#                         {"id": chen, "name": "ProfChenWeiya"},
#                         {"id": zhou, "name": "ProfZhouCheng"},
#                         {"id": luo, "name": "ProfLuohanbin"},
#                         {"id": zhang, "name": "ZhangJiayuan"},
#                         {"id": wang, "name": "WangZining"},
#                         {"id": ma, "name": "MaJiangping"},
#                         {"id": cai, "name": "CaiJianhua"},
#                         {"id": li, "name": "LiWenpeng"},
#                         {"id": song, "name": "SongJunbo"}
#                     ]
#                     # for npc in model.npcs:
#                     #     npc_model = self.get_single_model("NPC", npc["id"], create=False)
#                     #     if not npc_model:
#                     #         continue
#                     #     home_building = self.get_single_model("Buildings", create=True).get_building(npc_model.home_building)
#                     #     if not home_building:
#                     #         continue
#
#                     # npcs_info.append({"uid": f"NPC-{alan}", "homeBuilding": alan_model.home_building,
#                     #                   'asset': npc_configs.assets.index(alan_model.asset),
#                     #                   "assetName": alan_model.asset, 'model': alan_model.model,
#                     #                   'memorySystem': alan_model.memorySystem, 'planSystem': alan_model.planSystem,
#                     #                   'workBuilding': alan_model.work_building, 'nickname': alan_model.name,
#                     #                   'bio': alan_model.bio, 'goal': alan_model.goal, 'cash': alan_model.cash,
#                     #                   "x": alan_model.x, "y": alan_model.y})
#                     # npcs_info.append({"uid": f"NPC-{fei}", "homeBuilding": fei_model.home_building,
#                     #                   'asset': npc_configs.assets.index(fei_model.asset), "assetName": fei_model.asset,
#                     #                   'model': fei_model.model, 'memorySystem': fei_model.memorySystem,
#                     #                   'planSystem': fei_model.planSystem, 'workBuilding': fei_model.work_building,
#                     #                   'nickname': fei_model.name, 'bio': fei_model.bio, 'goal': fei_model.goal,
#                     #                   'cash': fei_model.cash, "x": fei_model.x, "y": fei_model.y})
#                     # npcs_info.append({"uid": f"NPC-{wangzining}", "homeBuilding": wangzining_model.home_building,
#                     #                   'asset': npc_configs.assets.index(wangzining_model.asset),
#                     #                   "assetName": wangzining_model.asset,
#                     #                   'model': wangzining_model.model, 'memorySystem': wangzining_model.memorySystem,
#                     #                   'planSystem': wangzining_model.planSystem,
#                     #                   'workBuilding': wangzining_model.work_building,
#                     #                   'nickname': wangzining_model.name, 'bio': wangzining_model.bio,
#                     #                   'goal': wangzining_model.goal,
#                     #                   'cash': wangzining_model.cash, "x": wangzining_model.x, "y": wangzining_model.y})
#                 npcs_info.append({
#                     "uid": f"NPC-{chen}",
#                     "homeBuilding": chen_model.home_building,
#                     "asset": npc_configs.assets.index(chen_model.asset),
#                     "assetName": chen_model.asset,
#                     "model": chen_model.model,
#                     "memorySystem": chen_model.memorySystem,
#                     "planSystem": chen_model.planSystem,
#                     "workBuilding": chen_model.work_building,
#                     "nickname": chen_model.name,
#                     "bio": chen_model.bio,
#                     "goal": chen_model.goal,
#                     "cash": chen_model.cash,
#                     "x": chen_model.x,
#                     "y": chen_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{zhou}",
#                     "homeBuilding": zhou_model.home_building,
#                     "asset": npc_configs.assets.index(zhou_model.asset),
#                     "assetName": zhou_model.asset,
#                     "model": zhou_model.model,
#                     "memorySystem": zhou_model.memorySystem,
#                     "planSystem": zhou_model.planSystem,
#                     "workBuilding": zhou_model.work_building,
#                     "nickname": zhou_model.name,
#                     "bio": zhou_model.bio,
#                     "goal": zhou_model.goal,
#                     "cash": zhou_model.cash,
#                     "x": zhou_model.x,
#                     "y": zhou_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{luo}",
#                     "homeBuilding": luo_model.home_building,
#                     "asset": npc_configs.assets.index(luo_model.asset),
#                     "assetName": luo_model.asset,
#                     "model": luo_model.model,
#                     "memorySystem": luo_model.memorySystem,
#                     "planSystem": luo_model.planSystem,
#                     "workBuilding": luo_model.work_building,
#                     "nickname": luo_model.name,
#                     "bio": luo_model.bio,
#                     "goal": luo_model.goal,
#                     "cash": luo_model.cash,
#                     "x": luo_model.x,
#                     "y": luo_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{zhang}",
#                     "homeBuilding": zhang_model.home_building,
#                     "asset": npc_configs.assets.index(zhang_model.asset),
#                     "assetName": zhang_model.asset,
#                     "model": zhang_model.model,
#                     "memorySystem": zhang_model.memorySystem,
#                     "planSystem": zhang_model.planSystem,
#                     "workBuilding": zhang_model.work_building,
#                     "nickname": zhang_model.name,
#                     "bio": zhang_model.bio,
#                     "goal": zhang_model.goal,
#                     "cash": zhang_model.cash,
#                     "x": zhang_model.x,
#                     "y": zhang_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{wang}",
#                     "homeBuilding": wang_model.home_building,
#                     "asset": npc_configs.assets.index(wang_model.asset),
#                     "assetName": wang_model.asset,
#                     "model": wang_model.model,
#                     "memorySystem": wang_model.memorySystem,
#                     "planSystem": wang_model.planSystem,
#                     "workBuilding": wang_model.work_building,
#                     "nickname": wang_model.name,
#                     "bio": wang_model.bio,
#                     "goal": wang_model.goal,
#                     "cash": wang_model.cash,
#                     "x": wang_model.x,
#                     "y": wang_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{ma}",
#                     "homeBuilding": ma_model.home_building,
#                     "asset": npc_configs.assets.index(ma_model.asset),
#                     "assetName": ma_model.asset,
#                     "model": ma_model.model,
#                     "memorySystem": ma_model.memorySystem,
#                     "planSystem": ma_model.planSystem,
#                     "workBuilding": ma_model.work_building,
#                     "nickname": ma_model.name,
#                     "bio": ma_model.bio,
#                     "goal": ma_model.goal,
#                     "cash": ma_model.cash,
#                     "x": ma_model.x,
#                     "y": ma_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{cai}",
#                     "homeBuilding": cai_model.home_building,
#                     "asset": npc_configs.assets.index(cai_model.asset),
#                     "assetName": cai_model.asset,
#                     "model": cai_model.model,
#                     "memorySystem": cai_model.memorySystem,
#                     "planSystem": cai_model.planSystem,
#                     "workBuilding": cai_model.work_building,
#                     "nickname": cai_model.name,
#                     "bio": cai_model.bio,
#                     "goal": cai_model.goal,
#                     "cash": cai_model.cash,
#                     "x": cai_model.x,
#                     "y": cai_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{li}",
#                     "homeBuilding": li_model.home_building,
#                     "asset": npc_configs.assets.index(li_model.asset),
#                     "assetName": li_model.asset,
#                     "model": li_model.model,
#                     "memorySystem": li_model.memorySystem,
#                     "planSystem": li_model.planSystem,
#                     "workBuilding": li_model.work_building,
#                     "nickname": li_model.name,
#                     "bio": li_model.bio,
#                     "goal": li_model.goal,
#                     "cash": li_model.cash,
#                     "x": li_model.x,
#                     "y": li_model.y
#                 })
#                 npcs_info.append({
#                     "uid": f"NPC-{song}",
#                     "homeBuilding": song_model.home_building,
#                     "asset": npc_configs.assets.index(song_model.asset),
#                     "assetName": song_model.asset,
#                     "model": song_model.model,
#                     "memorySystem": song_model.memorySystem,
#                     "planSystem": song_model.planSystem,
#                     "workBuilding": song_model.work_building,
#                     "nickname": song_model.name,
#                     "bio": song_model.bio,
#                     "goal": song_model.goal,
#                     "cash": song_model.cash,
#                     "x": song_model.x,
#                     "y": song_model.y
#                 })
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
#                     buildings_info.append(
#                         {"building_id": building["id"], "building_type": building["t"], "name": building["n"],
#                          "x": building["x"], "y": building["y"]})
#
#             npcs_model = self.get_single_model("NPCs", create=False)
#             if npcs_model:
#                 for npc in npcs_model.npcs:
#                     npc_model = self.get_single_model("NPC", npc["id"], create=False)
#                     if not npc_model:
#                         continue
#                     npcs_info.append({"uid": f'NPC-{npc["id"]}', "homeBuilding": npc_model.home_building,
#                                       'asset': npc_configs.assets.index(npc_model.asset), "assetName": npc_model.asset,
#                                       'model': npc_model.model, 'memorySystem': npc_model.memorySystem,
#                                       'planSystem': npc_model.planSystem, 'workBuilding': npc_model.work_building,
#                                       'nickname': npc_model.name, 'bio': npc_model.bio, 'goal': npc_model.goal,
#                                       'cash': npc_model.cash, "x": npc_model.x, "y": npc_model.y})
#
#         self.reg_eval(uid)
#         return buildings_info, npcs_info
#
#     def is_check_token(self):
#         return False
#
