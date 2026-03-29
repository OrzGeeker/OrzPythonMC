# -*- coding: utf8 -*-
from .Config import Config
from ..utils.RichText import RichText
from ..infra.runner import CommandRunner
from ..infra.fs import FileStore
import os

class Nginx:
    @classmethod
    def setup(cls, config):
        '''配置并启动nginx'''
        nginx_config_file = Config.game_version_server_nginx_file_path()
        if not config.yes:
            RichText.info('Dry-run: nginx setup will be executed with --yes')
            RichText.info('Will write config: %s' % nginx_config_file)
            RichText.info('Will link to /etc/nginx/conf.d and reload/start nginx')
            RichText.info('Will run certbot nginx https setup')
            return
        try:
            runner = CommandRunner()
            fs = FileStore()
            fs.ensure_dir(os.path.dirname(nginx_config_file))
            with open(nginx_config_file, 'w', encoding='utf-8') as cfg:
                cfg.write('\n'.join(filter(lambda x: x != None,[
                    Nginx.web_file_server_conf(), 
                    Nginx.web_live_map_conf(), 
                    Nginx.web_live_blue_map_conf(),
                    Nginx.web_opq_qq_bot_conf(),
                    Nginx.web_skin_system_conf(),
                    Nginx.web_mc_client(),
                ])))
                RichText.success('Nginx conf file location: %s' % nginx_config_file)
            
            # 创建nginx配置文件软链接
            nginx_conf_dir = '/etc/nginx/conf.d'
            if os.path.exists(nginx_conf_dir) and os.path.isdir(nginx_conf_dir):
                minecraft_nginx_conf_file = os.path.join(nginx_conf_dir, os.path.basename(nginx_config_file))
                cmd = 'sudo ln -snf %s %s' % (nginx_config_file, minecraft_nginx_conf_file)
                ret = runner.run(cmd).code
                if ret == 0:
                    RichText.success('Create symbol link file: %s' % minecraft_nginx_conf_file)

                nginx_process_number = int(runner.read('ps -ef | grep nginx | grep -v grep | wc -l') or '0')
                cmd = None
                if nginx_process_number > 0:
                    cmd = 'sudo nginx -s reload'
                else:
                    cmd = 'sudo nginx'

                if cmd:
                    ret = runner.run(cmd).code
                    if ret == 0:
                        RichText.success('minecraft nginx config successfully!')
                    else:
                        RichText.error('minecraft nginx config failed!')
                # 配置HTTPS
                Nginx.setupSSL()
        except Exception as e:
            print(e)
            RichText.error('Config Nginx for Minecraft Failed!!!')
            exit(-1)

    @classmethod
    def setupSSL(cls):
        '''配置nginx服务支持https'''

        cmd = 'sudo apt-get update ||'\
        'sudo apt-get install -y software-properties-common &&'\
        'sudo add-apt-repository -y universe &&'\
        'sudo add-apt-repository -y ppa:certbot/certbot &&'\
        'sudo apt-get update ||'\
        'sudo apt-get install -y certbot python3-certbot-nginx &&'\
        'sudo certbot --nginx'
        if CommandRunner().run(cmd).code == 0:
            RichText.success('Config HTTPS successfully!')
        else:
            RichText.error("Config HTTPS failed!")

    @classmethod
    def proxy_server_conf(cls, server_domain, upstream_url, port = 80, extra_headers = None):
        header_lines = ''
        if extra_headers:
            header_lines = '\n'.join(['        ' + h for h in extra_headers]) + '\n'
        return f"""
server {{
    listen {port};
    server_name {server_domain};
    location / {{
        proxy_pass      {upstream_url};
{header_lines}    }}
}}
"""

    @classmethod
    def upstream_conf(cls, name, servers):
        lines = '\n'.join(['    server %s;' % s for s in servers])
        return f"""
upstream {name} {{
{lines}
}}
"""

    
    @classmethod
    def web_file_server_conf(cls):
        '''配置minecraft文件服务器'''
        port=80
        file_server_root_dir = Config.game_ftp_server_base_dir()
        server_domain = 'download.jokerhub.cn'

        return f"""
# 我的世界文件服务器
server {{
    listen {port};
    server_name {server_domain};
    root {file_server_root_dir};

    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""

    @classmethod
    def web_skin_system_conf(cls):
        '''配置minecraft皮肤系统'''
        port=80
        file_server_root_dir = '/var/www/SkinSystem'
        server_domain = 'skin.jokerhub.cn'
        php_fpm_bin_path = CommandRunner().read("whereis php-fpm | cut -d ' ' -f 2")
        if not os.path.exists(php_fpm_bin_path):
            RichText.error('You have not install php environment!!!')
            return None
        php_fpm_version = os.path.basename(php_fpm_bin_path).replace('php-fpm','')
        fastcgi_pass = f'unix:/run/php/php{php_fpm_version}-fpm.sock'
        return f"""
# Minecraft SkinSystem
server {{
    listen {port};
    server_name {server_domain};
    root {file_server_root_dir};

    # Add index.php to the list if you are using PHP
    index index.php index.html index.htm index.nginx-debian.html;
    location / {{
        try_files $uri $uri/ =404;
    }}

    # pass PHP scripts to FastCGI server
    location ~ \\.php$ {{
        include snippets/fastcgi-php.conf;
        # With php-fpm (or other unix sockets):
        fastcgi_pass {fastcgi_pass};
    }}
}}
"""

    @classmethod
    def web_live_map_conf(cls):
        '''配置minecraft地图'''
        return Nginx.proxy_server_conf('map.jokerhub.cn', 'http://localhost:8123')

    @classmethod
    def web_live_blue_map_conf(cls):
        '''配置minecraft 3D高清地图'''
        return Nginx.proxy_server_conf('world.jokerhub.cn', 'http://localhost:8100')

    @classmethod
    def web_opq_qq_bot_conf(cls):
        '''配置QQ群管理机器人'''
        return Nginx.proxy_server_conf('qqbot.jokerhub.cn', 'http://localhost:8200')

    @classmethod
    def web_mc_client(cls):
        '''web端客户端'''
        server_domain = 'webmc.jokerhub.cn'
        proxy_domain = 'proxy.jokerhub.cn'
        upstream = Nginx.upstream_conf('mineproxy', ['localhost:8300'])
        webmc = Nginx.proxy_server_conf(server_domain, 'http://localhost:8300')
        proxy = Nginx.proxy_server_conf(proxy_domain, 'http://mineproxy', extra_headers = [
            'proxy_http_version 1.1;',
            'proxy_set_header Upgrade $http_upgrade;',
            'proxy_set_header Connection upgrade;',
            'proxy_set_header Host $host;'
        ])
        return webmc + upstream + proxy
