# -*- coding: utf8 -*-

import os, json
from ..utils.utils import *
from ..core.Forge import Forge
from ..domain import RuntimeOptions, PathLayout

class Config:
    '''Public Definitions'''
    GAME_DEFAULT_USERNAME = "guest"
    GAME_TYPE_PURE = 'vanilla'
    GAME_TYPE_SPIGOT = 'spigot'
    GAME_TYPE_FORGE = 'forge'
    GAME_TYPE_PAPER = 'paper'
    
    '''Private Definitions'''
    BASE_PATH = os.path.expanduser('~')
    GAME_ROOT_DIR = os.path.join(BASE_PATH,'minecraft')
    GAME_VERSIONS_DIR = os.path.join(GAME_ROOT_DIR,'versions')


    def __init__(self,args):

        # 调试信息
        if args.debug:
            print(args)

        self.options = RuntimeOptions(args)

        self.is_client = self.options.is_client
        self.version = self.options.version
        self.username = self.options.username
        self.mem_min = self.options.mem_min
        self.mem_max = self.options.mem_max
        self.is_extract_music = self.options.is_extract_music
        self.symlink = self.options.symlink
        self.bmclapi = self.options.bmclapi
        self.nginx = self.options.nginx
        self.deamon = self.options.deamon
        self.skin_system = self.options.skin_system
        self.jar_opts = self.options.jar_opts
        self.yes = self.options.yes

        game_type = self.options.type
        self.isPure = (game_type == Config.GAME_TYPE_PURE)
        self.isSpigot = (game_type == Config.GAME_TYPE_SPIGOT)
        self.isForge = (game_type == Config.GAME_TYPE_FORGE)
        self.isPaper = (game_type == Config.GAME_TYPE_PAPER)
        if self.isPure:
            self.game_type = Config.GAME_TYPE_PURE
        elif self.isSpigot:
            self.game_type = Config.GAME_TYPE_SPIGOT
        elif self.isPaper:
            self.game_type = Config.GAME_TYPE_PAPER
        elif self.isForge: 
            self.game_type = Config.GAME_TYPE_FORGE
        else:
            self.game_type = ''

        self.debug = self.options.debug
        self.force_upgrade = self.options.force_upgrade
        self.backup = self.options.backup
        self.optifine = self.options.optifine
        self.fabric = self.options.fabric
        self.api = self.options.api
        self.force_download = self.options.force_download
        self.paths = PathLayout(Config.BASE_PATH, self.version, self.game_type)

    def set_version(self, version):
        self.version = version
        self.paths.version = version

    def getForgeInfo(self):
        if self.isForge:
            self.forgeInfo = Forge(version = self.version)
        else:
            self.forgeInfo = None

    def java_class_path_list_separator(self):
        return ';' if platformType() == 'windows' else ':'

    @classmethod
    def game_root_dir(cls):
        '''Game Root Dir'''
        return Config.GAME_ROOT_DIR

    def game_versions_dir(self):
        '''Game Versions Dir'''
        return self.paths.game_versions_dir()

    def game_version_dir(self):
        '''Version Related Directory'''
        return self.paths.game_version_dir()

    ### Client
    def game_version_client_dir(self):
        return self.paths.game_version_client_dir()

    def game_version_client_assets_dir(self):
        return self.paths.game_version_client_assets_dir()

    def game_version_client_assets_indexs_dir(self):
        return self.paths.game_version_client_assets_indexs_dir()

    def game_version_client_assets_objects_dir(self, hash):
        return self.paths.game_version_client_assets_objects_dir(hash)

    def game_version_client_library_dir(self, subpath = None):
        return self.paths.game_version_client_library_dir(subpath)
    
    def game_version_client_versions_dir(self):
        return self.paths.game_version_client_versions_dir()

    def game_version_client_versions_version_dir(self):
        return self.paths.game_version_client_versions_version_dir()

    def game_version_client_native_library_dir(self):
        return self.paths.game_version_client_native_library_dir()

    def game_version_json_file_path(self):
        return os.path.join(self.game_version_client_versions_version_dir(), self.version + '.json')

    def game_version_client_jar_filename(self):
        return self.version + '.jar'

    def game_version_client_jar_file_path(self):
        jar_file_path = os.path.join(self.game_version_client_versions_version_dir(), self.game_version_client_jar_filename())
        return jar_file_path

    def game_version_forge_json_file_path(self):
        forge_json_file_name = '-'.join([self.version, self.forgeInfo.briefVersion]) + '.json'
        return os.path.join(self.game_version_client_dir(), forge_json_file_name)
    
    def game_version_launcher_profiles_json_path(self):
        return os.path.join(self.game_version_client_dir(), 'launcher_profiles.json')

    def game_version_json_obj(self):
        return loadJSON(self.game_version_forge_json_file_path() if self.isForge else self.game_version_json_file_path())

    def game_version_json_assets_obj(self):
        index_json_url = self.game_version_json_obj().get('assetIndex').get('url')
        index_json_path = os.path.join(self.game_version_client_assets_indexs_dir(), os.path.basename(index_json_url))
        return loadJSON(index_json_path)

    ### Server
    def game_version_server_dir(self):
        return self.paths.game_version_server_dir()

    def game_version_server_jar_filename(self):
        if self.isForge:
            return self.forgeInfo.fullVersion + '.jar'
        elif self.isSpigot:
            return 'spigot-' + self.version + '.jar'
        elif self.isPaper:
            return 'paper-' + self.version + '.jar'
        elif self.isPure:
            return self.version + '.jar'
        else:
            return ''

    def game_version_server_jar_file_path(self, isInBuildDir=False):
        jar_file_path = os.path.join(self.game_version_server_build_dir() if isInBuildDir else self.game_version_server_dir(), self.game_version_server_jar_filename())
        return jar_file_path

    def game_version_server_eula_file_path(self):
        return os.path.join(self.game_version_server_dir(), 'eula.txt')

    def game_version_server_bukkit_command_yaml_file_path(self):
        return os.path.join(self.game_version_server_dir(), 'commands.yml')

    def game_version_server_properties_file_path(self):
        return os.path.join(self.game_version_server_dir(), 'server.properties')

    def game_version_server_whitelist_file_path(self):
        return os.path.join(self.game_version_server_dir(), 'whitelist.json')

    def game_version_server_build_dir(self):
        return self.paths.game_version_server_build_dir()
    
    def game_version_server_world_dirs(self):
        worldName = 'world'
        properties_file_path = self.game_version_server_properties_file_path()

        if os.path.exists(properties_file_path):
            with open(properties_file_path, 'r') as f:
                for line in f.readlines():
                    if 'level-name' in line:
                        worldName = line.strip('\n').split('=')[1]
        else:
            return None

        game_dir = self.game_version_server_dir()

        world_dirs = []
        world_dir = os.path.join(game_dir,worldName)
        if world_dir and os.path.exists(world_dir):
            world_dirs.append(world_dir)

        if self.isSpigot or self.isPaper:
            world_nether_dir = world_dir + '_nether'
            world_the_end_dir = world_dir + '_the_end'
            if world_nether_dir and os.path.exists(world_nether_dir):
                world_dirs.append(world_nether_dir)
            if world_the_end_dir and os.path.exists(world_the_end_dir):
                world_dirs.append(world_the_end_dir)

        if len(world_dirs):
            return world_dirs
        else:
            return None

    def game_version_server_icon_file_path(self):
        return os.path.join(self.game_version_server_dir(), 'server-icon.png')

    def game_version_server_plugin_dir(self):
        return os.path.join(self.game_version_server_dir(),'plugins') if self.isPaper else None

    def game_version_server_world_backup_dir(self):
        return self.paths.game_version_server_world_backup_dir()
    
    def game_version_server_symlink_source_dir(self):
        return self.paths.game_version_server_symlink_source_dir()

    def game_version_client_mp3_dir(self):
        return self.paths.game_version_client_mp3_dir()
        
    def game_download_temp_dir(self):
        return self.paths.game_download_temp_dir()

    @classmethod
    def game_ftp_server_base_dir(cls):
        return os.path.join(Config.BASE_PATH, 'minecraft_world_backup')
        
    @classmethod
    def game_ftp_server_core_data_backup_dir(cls):
        return os.path.join(Config.game_ftp_server_base_dir(),'mcserver')

    @classmethod
    def game_ftp_server_core_data_plugin_dir(cls):
        return os.path.join(Config.game_ftp_server_core_data_backup_dir(), 'plugins')

    @classmethod
    def game_config_dir(cls):
        return os.path.join(Config.GAME_ROOT_DIR, 'configurations')

    @classmethod
    def game_version_server_nginx_file_path(cls):
        return os.path.join(Config.game_config_dir(),'nginx_minecraft.conf')

    @classmethod
    def game_version_server_systemctl_conf_file_path(cls):
        return os.path.join(Config.game_config_dir(),'minecraft.service')
