import os

class PathLayout:
    def __init__(self, base_path, version, game_type):
        self.base_path = base_path
        self.version = version
        self.game_type = game_type

    def game_root_dir(self):
        return os.path.join(self.base_path, 'minecraft')

    def game_versions_dir(self):
        return os.path.join(self.game_root_dir(), 'versions')

    def game_version_dir(self):
        return os.path.join(self.game_versions_dir(), self.version)

    def game_version_client_dir(self):
        return os.path.join(self.game_version_dir(), 'client', 'vanilla')

    def game_version_client_assets_dir(self):
        return os.path.join(self.game_version_client_dir(), 'assets')

    def game_version_client_assets_indexs_dir(self):
        return os.path.join(self.game_version_client_assets_dir(), 'indexes')

    def game_version_client_assets_objects_dir(self, hash):
        return os.path.join(self.game_version_client_assets_dir(), 'objects', hash[0:2])

    def game_version_client_library_dir(self, subpath = None):
        lib_dir = os.path.join(self.game_version_client_dir(), 'libraries')
        if subpath != None:
            subdir = os.path.dirname(subpath)
            lib_dir = os.path.join(lib_dir, subdir)
        return lib_dir

    def game_version_client_versions_dir(self):
        return os.path.join(self.game_version_client_dir(), 'versions')

    def game_version_client_versions_version_dir(self):
        return os.path.join(self.game_version_client_versions_dir(), self.version)

    def game_version_client_native_library_dir(self):
        return os.path.join(self.game_version_client_versions_version_dir(), self.version + '-natives')

    def game_version_server_dir(self):
        return os.path.join(self.game_version_dir(), 'server', self.game_type)

    def game_version_server_build_dir(self):
        return os.path.join(self.game_version_server_dir(), 'build')

    def game_ftp_server_base_dir(self):
        return os.path.join(self.base_path, 'minecraft_world_backup')

    def game_ftp_server_core_data_backup_dir(self):
        return os.path.join(self.game_ftp_server_base_dir(), 'mcserver')

    def game_ftp_server_core_data_plugin_dir(self):
        return os.path.join(self.game_ftp_server_core_data_backup_dir(), 'plugins')

    def game_version_server_world_backup_dir(self):
        return os.path.join(self.game_ftp_server_base_dir(), 'game_backup')

    def game_version_server_symlink_source_dir(self):
        return self.game_ftp_server_core_data_backup_dir()

    def game_version_client_mp3_dir(self):
        return os.path.join(self.game_ftp_server_base_dir(), 'client_music', self.version)

    def game_download_temp_dir(self):
        return os.path.join(self.game_root_dir(), 'download_tmp_dir')

    def game_config_dir(self):
        return os.path.join(self.game_root_dir(), 'configurations')

    def game_version_server_nginx_file_path(self):
        return os.path.join(self.game_config_dir(), 'nginx_minecraft.conf')

    def game_version_server_systemctl_conf_file_path(self):
        return os.path.join(self.game_config_dir(), 'minecraft.service')
