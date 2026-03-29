# -*- coding: utf8 -*-
import os
from .Config import Config
from ..utils.RichText import RichText
from ..infra.runner import CommandRunner
from ..infra.fs import FileStore

class Daemon:

    @classmethod
    def setup(cls, config):
        '''配置minecraft守护进程，使用systemctl管理'''

        if not config.yes:
            systemctl_conf_file_path = Config.game_version_server_systemctl_conf_file_path()
            RichText.info('Dry-run: systemd setup will be executed with --yes')
            RichText.info('Will write service file: %s' % systemctl_conf_file_path)
            RichText.info('Will link to /etc/systemd/system and reload/enable/restart service')
            return

        daemon_name = 'Joker Minecraft Server'
        daemon_user = os.getlogin()
        daemon_mc_version = config.version
        daemon_mc_min_mem = config.mem_min
        daemon_mc_max_mem = config.mem_max
        daemon_mc_server_type = config.game_type
        daemon_mc_title = 'jokermc'
        runner = CommandRunner()
        orzmc_bin_path = runner.read('which orzmc')
        screen_bin_path = runner.read('which screen')
        sleep_bin_path = runner.read('which sleep')
        daemon_mc_stop_secs = 10
        daemon_mc_restart = '60s'
        daemon_mc_work_dir = '~'
        systemctl_daemon_conf = f"""
[Unit]
Description={daemon_name}
After=network.target

[Service]
User={daemon_user}
WorkingDirectory={daemon_mc_work_dir}
Environment=TITLE='{daemon_mc_title}'
Environment=STOP_SHUTDOWN='服务器即将关闭, 正在保存地图...'
Environment=MC_VERSION='{daemon_mc_version}'
Environment=MC_MIN='{daemon_mc_min_mem}'
Environment=MC_MAX='{daemon_mc_max_mem}'
Environment=MC_SERVER_TYPE='{daemon_mc_server_type}'
ExecStart=/bin/sh -c '{screen_bin_path} -DmS $TITLE {orzmc_bin_path} -s -v ${{MC_VERSION}} -m ${{MC_MIN}} -x ${{MC_MAX}} -t ${{MC_SERVER_TYPE}}'
ExecReload={screen_bin_path} -p 0 -S $TITLE -X eval 'stuff "reload"\\015'
ExecStop={screen_bin_path} -p 0 -S $TITLE -X eval 'stuff "say ${{STOP_SHUTDOWN}}"\\015'
ExecStop={screen_bin_path} -p 0 -S $TITLE -X eval 'stuff "save-all"\\015'
ExecStop={screen_bin_path} -p 0 -S $TITLE -X eval 'stuff "stop"\\015'
ExecStop={sleep_bin_path} {daemon_mc_stop_secs}
Restart=on-failure
RestartSec={daemon_mc_restart}

[Install]
WantedBy=multi-user.target
"""
        try:
            systemctl_conf_file_path = Config.game_version_server_systemctl_conf_file_path()
            FileStore().ensure_dir(os.path.dirname(systemctl_conf_file_path))
            with open(systemctl_conf_file_path,'w',encoding='utf-8') as cfg:
                cfg.write(systemctl_daemon_conf)
                RichText.success('minecraft.service has been writen in location: %s' % systemctl_conf_file_path)

            systemctl_system_dir = '/etc/systemd/system'
            minecraft_systemctl_conf_filename = os.path.basename(systemctl_conf_file_path)
            if os.path.exists(systemctl_system_dir) and os.path.isdir(systemctl_system_dir):
                minecraft_service_file_path = os.path.join(systemctl_system_dir, minecraft_systemctl_conf_filename)
                cmd = 'sudo ln -snf {source} {dest} && sudo systemctl daemon-reload && sudo systemctl enable {service} && sudo systemctl restart {service}'.format(
                    source = systemctl_conf_file_path,
                    dest = minecraft_service_file_path,
                    service = minecraft_systemctl_conf_filename
                )
                ret = runner.run(cmd).code
                if ret == 0:
                    RichText.success('started service: %s' % minecraft_systemctl_conf_filename)
        except Exception as e:
            print(e)
            RichText.error('minecraft daemon configuration for systemctl failed!')

        
