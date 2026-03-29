import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from OrzMC.domain import RuntimeOptions, PathLayout, Step, Plan

class TestDomain(unittest.TestCase):
    def test_runtime_options(self):
        class Args:
            server = False
            version = '1.20.1'
            username = 'player'
            minmem = '512M'
            maxmem = '2G'
            extract_music = False
            symlink = True
            bmclapi = True
            nginx = False
            deamon = False
            skin_system = False
            jar_opts = None
            debug = False
            force_upgrade_world = True
            backup_world = False
            optifine = False
            fabric = False
            api = 'v2'
            force_download = False
            yes = True
            type = 'vanilla'
        opts = RuntimeOptions(Args)
        self.assertTrue(opts.is_client)
        self.assertEqual(opts.version, '1.20.1')
        self.assertTrue(opts.symlink)
        self.assertTrue(opts.force_upgrade)

    def test_path_layout(self):
        layout = PathLayout('/tmp', '1.20.1', 'vanilla')
        self.assertEqual(layout.game_root_dir(), '/tmp/minecraft')
        self.assertEqual(layout.game_version_server_dir(), '/tmp/minecraft/versions/1.20.1/server/vanilla')
        self.assertEqual(layout.game_version_server_systemctl_conf_file_path(), '/tmp/minecraft/configurations/minecraft.service')

    def test_plan_steps(self):
        steps = [
            Step('a', lambda ctx: {'value': 1}),
            Step('b', lambda ctx: {'value': ctx['value'] + 1})
        ]
        plan = Plan(steps)
        result = plan.run()
        self.assertEqual(result['value'], 2)

if __name__ == '__main__':
    unittest.main()
