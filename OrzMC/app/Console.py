# -*- coding: utf8 -*-
from .Config import Config
from ..core.Mojang import Mojang
from .Constants import *
from ..utils.RichText import RichText

import os
import json

class Console:
    
    def __init__(self, config):
        '''初始化控制台实例'''
        self.config = config
        
    def userInteraction(self):
        '''控制台展示用户交互界面'''
        if self.config.version == None:
            # 如果没有提示版本参数，则展示可选版本号供用户选择
            self.showVersionList()

        if self.config.username == Config.GAME_DEFAULT_USERNAME and not self.config.is_extract_music:
            # 如果用户名为默认值时，提示用户选择一个自己的用户名进行游戏
            self.showUserName()

        # 客户端启动方式
        self.selectLauncherProfile()

    def showVersionList(self):
        '''控制台交互显示可选客户端版本号'''
        
        releaseVersions = Mojang.get_release_version_id_list(update = True)
        if not releaseVersions or len(releaseVersions) == 0:
            RichText.error('No supported versions fetched')
            exit(-1)
        releaseVersions = releaseVersions[0:releaseVersions.index('1.13')+1]
        column = 6
        table_versions = [releaseVersions[i:i+column] for i in range(0, len(releaseVersions), column)]
        RichText.table(
            title = '目前支持的游戏版本', 
            table_data = table_versions)

        if len(releaseVersions) > 0:
            self.config.set_version(releaseVersions[0])

        while True:
            select = RichText.prompt('选择版本号', default = self.config.version)
            if select in releaseVersions:
                self.config.set_version(select)
                RichText.info('You choose the version: %s' % self.config.version)
                break
            RichText.warn('There is no such a release version game, Please try again!')
    
    def showUserName(self):
        '''控制台交互输入玩家用户名'''
        
        # 只针对客户端有效
        if not self.config.is_client:
            return 

        self.config.username = RichText.prompt('输入用户名', default = self.config.username)
        RichText.info('You username in game is: %s' % self.config.username)


    def selectLauncherProfile(self):

        if not self.config.is_client or not self.config.isPure:
            return 

        if not (self.config.optifine or self.config.fabric):
            return

        launcher_profiles_json_file_path = self.config.game_version_launcher_profiles_json_path()
        if os.path.exists(launcher_profiles_json_file_path):
            content = None
            with open(launcher_profiles_json_file_path, 'r') as f:
                content = json.load(f)
                profiles = content.get('profiles', None)
                count = len(profiles) if profiles else 0
                if count > 0:
                    keys = list(profiles.keys())
                    selected_key = content.get('selectedProfile')
                    selectedIndex = (keys.index(selected_key) + 1) if selected_key in keys else 1
                    for i, key in enumerate(keys, start = 1):
                        prefix = '*' if i == selectedIndex else ' '
                        RichText.console.print('%s %d. %s' % (prefix, i, key))

                    which = RichText.prompt('选择启动配置', choices = [str(i) for i in range(1, count + 1)], default = str(selectedIndex))
                    selected_key = keys[int(which) - 1]
                    self.config.lastVersionId = profiles.get(selected_key).get('lastVersionId')
                    content['selectedProfile'] = selected_key

            if content != None: 
                with open(launcher_profiles_json_file_path, 'w') as f: 
                    json.dump(content, f)
