version = "1.0.0"
title = f"[v{version}] ANCheat"

import win32gui, time, json, os, threading, psutil, win32process, win32api, win32con, random, requests, win32console, ctypes
import dearpygui.dearpygui as dpg
import pyMeow as pm
user32 = ctypes.WinDLL("user32")
configFilePath = f"{os.environ['LOCALAPPDATA']}\\temp\\ANCheat"
class configListener(dict):
    def __init__(self, initialDict):
        for k, v in initialDict.items():
            if isinstance(v, dict):
                initialDict[k] = configListener(v)
        super().__init__(initialDict)
    def __setitem__(self, item, value):
        if isinstance(value, dict):
            value = configListener(value)
        super().__setitem__(item, value)
        if hasattr(ANCheatClass, "config"):
            json.dump(ANCheatClass.config, open(configFilePath, "w", encoding="utf-8"), indent=4)
class Colors:
    white = pm.get_color("white")
    black = pm.get_color("black")
    blackFade = pm.fade_color(black, 0.6)
    red = pm.get_color("#e03636")
    green = pm.get_color("#43e06d")
class Offsets:
    m_pBoneArray = 480
class Entity:
    def __init__(self, ptr, pawnPtr, proc):
        self.ptr = ptr
        self.pawnPtr = pawnPtr
        self.proc = proc
        self.pos2d = None
        self.headPos2d = None
    @property
    def name(self):
        return pm.r_string(self.proc, self.ptr + Offsets.m_iszPlayerName)
    @property
    def health(self):
        return pm.r_int(self.proc, self.pawnPtr + Offsets.m_iHealth)
    @property
    def team(self):
        return pm.r_int(self.proc, self.pawnPtr + Offsets.m_iTeamNum)
    @property
    def pos(self):
        return pm.r_vec3(self.proc, self.pawnPtr + Offsets.m_vOldOrigin)
    @property
    def isDormant(self):
        return pm.r_bool(self.proc, self.pawnPtr + Offsets.m_bDormant)
    def bonePos(self, bone):
        gameScene = pm.r_int64(self.proc, self.pawnPtr + Offsets.m_pGameSceneNode)
        boneArrayPtr = pm.r_int64(self.proc, gameScene + Offsets.m_pBoneArray)
        return pm.r_vec3(self.proc, boneArrayPtr + bone * 32)
    def wts(self, viewMatrix):
        try:
            a, self.pos2d = pm.world_to_screen_noexc(viewMatrix, self.pos, 1)
            b, self.headPos2d = pm.world_to_screen_noexc(viewMatrix, self.bonePos(6), 1)
            if not a or not b:
                return False
            return True
        except:
            return False
class ANCheat:
    def __init__(self):
        self.config = {
            "version": version,
            "triggerBot": {
                "enabled": False,
                "bind": 0,
                "onlyEnemies": True,
                "delay": 0,
            },
            "misc": {
                "fovchanger": False,
                "fov": 90,
                "noFlash": False,
                "transparentsmoke": False
            },
            "settings": {
                "saveSettings": True
            }     
        }
        if os.path.isfile(configFilePath):
            try:
                config = json.loads(open(configFilePath, encoding="utf-8").read())
                isConfigOk = True
                for key in self.config:
                    if not key in config or len(self.config[key]) != len(config[key]):
                        isConfigOk = False

                        break
                if isConfigOk:
                    if not config["settings"]["saveSettings"]:
                        self.config["settings"]["saveSettings"] = False
                    else:
                        if config["version"] == version:
                            self.config = config
            except:
                pass
        self.config = configListener(self.config)
        self.guiWindowHandle = None
        self.overlayWindowHandle = None
        self.overlayThreadExists = False
        self.localTeam = None
        self.run()
    def isCsOpened(self):
        while True:
            if not pm.process_running(self.proc):
                os._exit(0)

            time.sleep(3)
    def windowListener(self):
        while True:
            try:
                self.focusedProcess = psutil.Process(win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[-1]).name()
            except:
                self.focusedProcess = ""
            time.sleep(0.5)
    def run(self):
        print("Waiting for CS2...")
        while True:
            time.sleep(1)
            try:
                self.proc = pm.open_process("cs2.exe")
                self.mod = pm.get_module(self.proc, "client.dll")["base"]

                break
            except:
                pass
        print("Starting ANCheat!")
        os.system("cls") 
        try:
            offsetsName = ["dwViewMatrix", "dwEntityList", "dwLocalPlayerController", "dwLocalPlayerPawn"] 
            offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
            [setattr(Offsets, k, offsets["client.dll"][k]) for k in offsetsName]

            clientDllName = {
                "m_iIDEntIndex": "C_CSPlayerPawnBase",
                "m_flFlashMaxAlpha": "C_CSPlayerPawnBase",
                "m_bSpotted": "EntitySpottedState_t",
                "m_hPlayerPawn": "CCSPlayerController",
                "m_fFlags": "C_BaseEntity",
                "m_iszPlayerName": "CBasePlayerController",
                "m_iHealth": "C_BaseEntity",
                "m_iTeamNum": "C_BaseEntity",
                "m_vOldOrigin": "C_BasePlayerPawn",
                "m_pGameSceneNode": "C_BaseEntity",
                "m_bDormant": "CGameSceneNode",
                "m_pCameraServices": "C_BasePlayerPawn",
                "m_iFOV": "CCSPlayerBase_CameraServices"
            }
            clientDll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client.dll.json").json()
            [setattr(Offsets, k, clientDll["client.dll"]["classes"][clientDllName[k]]["fields"][k]) for k in clientDllName]
        except Exception as e:
            print(e)
            input("Can't retrieve offsets. Press any key to exit!")

            os._exit(0)
        threading.Thread(target=self.isCsOpened, daemon=True).start()
        threading.Thread(target=self.windowListener, daemon=True).start()
        if self.config["triggerBot"]["enabled"]:
            threading.Thread(target=self.triggerBot, daemon=True).start()

        if self.config["misc"]["fovchanger"]:
            threading.Thread(target=self.fovchanger, daemon=True).start()
            
        if self.config["misc"]["noFlash"]:
            self.noFlash()
    def triggerBot(self):
        while not hasattr(self, "focusedProcess"):
            time.sleep(0.1)

        while True:
            time.sleep(0.001)

            if not self.config["triggerBot"]["enabled"]: break

            if self.focusedProcess != "cs2.exe":
                time.sleep(1)
                
                continue

            if win32api.GetAsyncKeyState(self.config["triggerBot"]["bind"]) == 0: continue

            try:
                player = pm.r_int64(self.proc, self.mod + Offsets.dwLocalPlayerPawn)
                entityId = pm.r_int(self.proc, player + Offsets.m_iIDEntIndex)

                if entityId > 0:
                    entList = pm.r_int64(self.proc, self.mod + Offsets.dwEntityList)
                    entEntry = pm.r_int64(self.proc, entList + 0x8 * (entityId >> 9) + 0x10)
                    entity = pm.r_int64(self.proc, entEntry + 120 * (entityId & 0x1FF))

                    entityTeam = pm.r_int(self.proc, entity + Offsets.m_iTeamNum)
                    playerTeam = pm.r_int(self.proc, player + Offsets.m_iTeamNum)


                    if self.config["triggerBot"]["onlyEnemies"] and playerTeam == entityTeam: continue

                    entityHp = pm.r_int(self.proc, entity + Offsets.m_iHealth)

                    if entityHp > 0:
                        time.sleep(self.config["triggerBot"]["delay"])
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                        time.sleep(0.01)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            except:
                pass
    def fovchanger(self):
        FOV = self.config["misc"]["fov"]
        proc = pm.open_process("cs2.exe")
        client = pm.get_module(proc, "client.dll")["base"]
        _localPlayer = pm.r_int64(proc, client + Offsets.dwLocalPlayerPawn )
        _cameraServies = pm.r_int64(proc, _localPlayer + Offsets.m_pCameraServices)
        while True:
            if FOV!= self.config["misc"]["fov"]:
                FOV = self.config["misc"]["fov"]
            pm.w_uint(proc, _cameraServies + Offsets.m_iFOV, FOV)
    def noFlash(self):
        proc = pm.open_process("cs2.exe")
        client = pm.get_module(proc, "client.dll")["base"]
        while True:
            _localPlayer = pm.r_int64(proc, client + Offsets.dwLocalPlayerPawn )
            if _localPlayer:
                flash_alpha = pm.r_float(proc, _localPlayer + Offsets.m_flFlashMaxAlpha)
                if flash_alpha > 0.0:
                    pm.w_float(proc, _localPlayer + Offsets.m_flFlashMaxAlpha, 0.0)
if __name__ == "__main__":
    if os.name != "nt":
        input("ANCheat is only working on Windows.")
        os._exit(0)
    ANCheatClass = ANCheat()
    win32gui.ShowWindow(win32console.GetConsoleWindow(), win32con.SW_HIDE)
    uiWidth = 650
    uiHeight = 350
    dpg.create_context()
    
    def setFovValue(id, value):
        ANCheatClass.config["misc"]["fov"] = value
    def toggleTriggerBot(id, value):
        ANCheatClass.config["triggerBot"]["enabled"] = value
        if value:
            threading.Thread(target=ANCheatClass.triggerBot, daemon=True).start()
    waitingForKeyTriggerBot = False
    def statusBindTriggerBot(id):
        global waitingForKeyTriggerBot
        if not waitingForKeyTriggerBot:
            with dpg.handler_registry(tag="TriggerBot Bind Handler"):
                dpg.add_key_press_handler(callback=setBindTriggerBot)
            dpg.set_item_label(buttonBindTriggerBot, "...")
            waitingForKeyTriggerBot = True
    def setBindTriggerBot(id, value):
        global waitingForKeyTriggerBot
        if waitingForKeyTriggerBot:
            ANCheatClass.config["triggerBot"]["bind"] = value
            dpg.set_item_label(buttonBindTriggerBot, f"Bind: {chr(value)}")
            dpg.delete_item("TriggerBot Bind Handler")
            waitingForKeyTriggerBot = False
    def toggleTriggerBotOnlyEnemies(id, value):
        ANCheatClass.config["triggerBot"]["onlyEnemies"] = value
    def sliderTriggerBotDelay(id, value):
        ANCheatClass.config["triggerBot"]["delay"] = value
    def togglefovchanger(id, value):
        ANCheatClass.config["misc"]["fovchanger"] = value       
        if value:
            threading.Thread(target=ANCheatClass.fovchanger, daemon=True).start()    
    def toggleNoFlash(id, value):
        ANCheatClass.config["misc"]["noFlash"] = value       
        ANCheatClass.noFlash()
    def toggleSaveSettings(id, value):
        ANCheatClass.config["settings"]["saveSettings"] = value
    def toggleAlwaysOnTop(id, value):
        if value:
            win32gui.SetWindowPos(ANCheatClass.guiWindowHandle, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        else:
            win32gui.SetWindowPos(ANCheatClass.guiWindowHandle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    with dpg.window(label=title, width=uiWidth, height=uiHeight, no_collapse=True, no_move=True, no_resize=True, on_close=lambda: os._exit(0)) as window:
        with dpg.tab_bar():
            with dpg.tab(label="TriggerBot"):
                dpg.add_spacer(width=75)
                with dpg.group(horizontal=True):
                    checkboxToggleTriggerBot = dpg.add_checkbox(label="Toggle", default_value=ANCheatClass.config["triggerBot"]["enabled"], callback=toggleTriggerBot)
                    buttonBindTriggerBot = dpg.add_button(label="Click to Bind", callback=statusBindTriggerBot)
                    bind = ANCheatClass.config["triggerBot"]["bind"]
                    if bind != 0:
                        dpg.set_item_label(buttonBindTriggerBot, f"Bind: {chr(bind)}")   
                dpg.add_spacer(width=75)
                dpg.add_separator()
                dpg.add_spacer(width=75)
                checkboxTriggerBotOnlyEnemies = dpg.add_checkbox(label="Only Enemies", default_value=ANCheatClass.config["triggerBot"]["onlyEnemies"], callback=toggleTriggerBotOnlyEnemies)
                dpg.add_spacer(width=75)
                dpg.add_separator()
                dpg.add_spacer(width=75)
                sliderDelayTriggerBot = dpg.add_slider_float(label="Shot Delay", default_value=ANCheatClass.config["triggerBot"]["delay"], max_value=1, callback=sliderTriggerBotDelay, width=250, clamped=True, format="%.1f")
            ###
            with dpg.tab(label="Misc"):
                dpg.add_spacer(width=75)
                with dpg.group(horizontal=True):
                    checkboxFovchanger = dpg.add_checkbox(label="Fovchanger", default_value=ANCheatClass.config["misc"]["fovchanger"], callback=togglefovchanger)
                sliderFovchanger = dpg.add_slider_int(label="Fov Value", default_value=ANCheatClass.config["misc"]["fov"], max_value=180, min_value=60, callback=setFovValue)
                checkboxNoFlash = dpg.add_checkbox(label="NoFlash", default_value=ANCheatClass.config["misc"]["noFlash"], callback=toggleNoFlash)
            with dpg.tab(label="Settings"):
                dpg.add_spacer(width=75)
                checkboxSaveSettings = dpg.add_checkbox(label="Save Settings", default_value=ANCheatClass.config["settings"]["saveSettings"], callback=toggleSaveSettings)
                dpg.add_spacer(width=75)
                checkboxAlwaysOnTop = dpg.add_checkbox(label="Menu Always On Top", callback=toggleAlwaysOnTop)
                dpg.add_spacer(width=75)
                dpg.add_separator()
                dpg.add_spacer(width=75)
                creditsText = dpg.add_text(default_value="Credits: AI, Anarchowitz and PyMeow Community")
                githubText = dpg.add_text(default_value="https://github.com/anarchowitz/pozvhe nazvanie")
    def dragViewport(sender, appData, userData):
        if dpg.get_mouse_pos(local=False)[1] <= 40:
            dragDeltas = appData
            viewportPos = dpg.get_viewport_pos()
            newX = viewportPos[0] + dragDeltas[1]
            newY = max(viewportPos[1] + dragDeltas[2], 0)
            dpg.set_viewport_pos([newX, newY])
    with dpg.handler_registry():
        dpg.add_mouse_drag_handler(button=0, threshold=0.0, callback=dragViewport)
    with dpg.theme() as globalTheme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (21, 19, 21, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (21, 19, 21, 255))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (225, 225, 225, 255))

            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
    dpg.bind_theme(globalTheme)
    dpg.create_viewport(title=title, width=uiWidth, height=uiHeight, decorated=False, resizable=False)
    dpg.show_viewport()
    ANCheatClass.guiWindowHandle = win32gui.FindWindow(title, None)
    dpg.setup_dearpygui()
    dpg.start_dearpygui()
