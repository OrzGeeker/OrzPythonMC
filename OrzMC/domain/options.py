class RuntimeOptions:
    def __init__(self, args):
        self.is_client = not args.server
        self.version = args.version
        self.username = args.username
        self.mem_min = args.minmem
        self.mem_max = args.maxmem
        self.is_extract_music = args.extract_music
        self.symlink = args.symlink
        self.bmclapi = args.bmclapi
        self.nginx = args.nginx
        self.deamon = args.deamon
        self.skin_system = args.skin_system
        self.jar_opts = args.jar_opts
        self.debug = args.debug
        self.force_upgrade = args.force_upgrade_world
        self.backup = args.backup_world
        self.optifine = args.optifine
        self.fabric = args.fabric
        self.api = args.api
        self.force_download = args.force_download
        self.yes = args.yes
        self.type = args.type
