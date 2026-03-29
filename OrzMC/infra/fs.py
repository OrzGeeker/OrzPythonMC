import os
import shutil

class FileStore:
    def ensure_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok = True)

    def write_text(self, path, content):
        with open(path, 'w', encoding = 'utf-8') as f:
            f.write(content)

    def read_text(self, path):
        with open(path, 'r', encoding = 'utf-8') as f:
            return f.read()

    def exists(self, path):
        return os.path.exists(path)

    def remove(self, path):
        if os.path.exists(path):
            os.remove(path)

    def move(self, src, dest):
        shutil.move(src, dest)

    def ensure_symlink(self, source, destination, backup_suffix = '.before_symlink'):
        if os.path.islink(destination):
            target = os.readlink(destination)
            if os.path.normcase(target) == os.path.normcase(source):
                return

        if not os.path.exists(source):
            if os.path.exists(destination):
                self.move(destination, source)
            else:
                backup = destination + backup_suffix
                if os.path.exists(backup):
                    self.move(backup, destination)
                return

        if os.path.exists(destination):
            self.move(destination, destination + backup_suffix)

        os.symlink(source, destination, target_is_directory = os.path.isdir(source))
