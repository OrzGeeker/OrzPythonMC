# -*- coding: utf8 -*-
from json import decoder
from ..utils.utils import *
from ..utils.ColorString import ColorString
from ..core.PaperAPI import PaperAPI
from ..core.Mojang import Mojang
from ..core.Spigot import Spigot
from ..core.Forge import Forge
from ..core.OptiFine import OptiFine
from ..core.Fabric import Fabric
from ..core.BMCLAPI import BMCLAPI
from ..infra.http import HttpClient
from ..infra.fs import FileStore
from ..domain import resolve_libraries

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
import shutil
import time
import hashlib

class Downloader:

    def __init__(self, config):
        self.config = config
        self.http = HttpClient(timeout = 10)
        self.fs = FileStore()
        self.max_workers = max(8, min(32, (os.cpu_count() or 4) * 4))
        self.chunk_size = 1024 * 1024
        self._tuned = False

    def downloadGameJSON(self):
        '''Download Game Json Configure File'''

        if is_sigint_up():
            return

        version_json_path = self.config.game_version_json_file_path()
        (url, hash) = Mojang.get_release_game_json(self.config.version)
        if not checkFileExist(version_json_path, hash):
            print("Download Game Json Configure File!")
            jsonStr = self.http.get(url).text
            self.fs.ensure_dir(os.path.dirname(version_json_path))
            writeContentToFile(jsonStr, version_json_path)
        else: 
            print("Game Json Configure File have been downloaded!")

    def downloadClient(self):
        '''Download Client Jar File'''
        if is_sigint_up():
            return  

        client = self.config.game_version_json_obj().get('downloads').get('client')
        clientUrl = client.get('url')
        sha1 = client.get('sha1')
        clientJARFilePath = self.config.game_version_client_jar_file_path()
        if not checkFileExist(clientJARFilePath, sha1):
            self.download(
                clientUrl,
                os.path.dirname(clientJARFilePath), 
                self.config.game_version_client_jar_filename(), 
                prefix_desc='client jar file'
            )
        else:
            print("client jar file existed!")

    
    def downloadAssetIndex(self):
        '''Download Game Asset Index JSON file'''
        if is_sigint_up():
            return

        assetIndex = self.config.game_version_json_obj().get('assetIndex')
        index_json_url = assetIndex.get('url')
        index_json_sha1 = assetIndex.get('sha1')
        index_json_path= os.path.join(self.config.game_version_client_assets_indexs_dir(), os.path.basename(index_json_url))
        if not checkFileExist(index_json_path,index_json_sha1):
            print("Download assetIndex JSON File")
            index_json_str = self.http.get(index_json_url).text
            self.fs.ensure_dir(os.path.dirname(index_json_path))
            with open(index_json_path,'w',encoding='utf-8') as f:
                f.write(index_json_str)
        else:
            print("assetIndex JSON File have been downloaded")
    
    def downloadAssetObjects(self):
        '''Download Game Asset Objects'''
        objects = self.config.game_version_json_assets_obj().get('objects')
        first_url = None
        for (_, object) in objects.items():
            hash = object.get('hash')
            url = Mojang.assets_objects_url(hash)
            object_dir = self.config.game_version_client_assets_objects_dir(hash)
            object_filePath = os.path.join(object_dir,os.path.basename(url))
            if not checkFileExist(object_filePath, hash):
                first_url = url
                break

        if first_url:
            self._ensure_tuned(first_url)
            asset_workers = min(64, self.max_workers * 2)
            with ThreadPoolExecutor(max_workers = asset_workers) as executor:
                in_flight = set()
                limit = asset_workers * 8
                total = 0
                for (_, object) in objects.items():
                    hash = object.get('hash')
                    url = Mojang.assets_objects_url(hash)
                    object_dir = self.config.game_version_client_assets_objects_dir(hash)
                    object_filePath = os.path.join(object_dir,os.path.basename(url))
                    if not checkFileExist(object_filePath, hash):
                        total += 1
                progress = tqdm(total = total, unit = 'files', desc = 'assets')
                for (_, object) in objects.items():
                    if is_sigint_up():
                        return
                    hash = object.get('hash')
                    url = Mojang.assets_objects_url(hash)
                    object_dir = self.config.game_version_client_assets_objects_dir(hash)
                    object_filePath = os.path.join(object_dir,os.path.basename(url))
                    if checkFileExist(object_filePath, hash):
                        continue
                    while len(in_flight) >= limit:
                        done, in_flight = wait(in_flight, return_when = FIRST_COMPLETED)
                        for f in done:
                            f.result()
                            progress.update(1)
                    in_flight.add(executor.submit(self.download, url, object_dir, None, None, False))
                for f in as_completed(in_flight):
                    f.result()
                    progress.update(1)
                progress.close()

        if self.config.is_extract_music:
            for (name, object) in objects.items():
                path, type = os.path.splitext(name)
                filename = path.replace(os.sep, '_') + '.mp3'
                if type == '.ogg':
                    hash = object.get('hash')
                    url = Mojang.assets_objects_url(hash)
                    object_dir = self.config.game_version_client_assets_objects_dir(hash)
                    object_filePath = os.path.join(object_dir,os.path.basename(url))
                    if os.path.exists(object_filePath):
                        target_file_path = os.path.join(self.config.game_version_client_mp3_dir(),filename)
                        self.fs.ensure_dir(os.path.dirname(target_file_path))
                        convertOggToMap3(object_filePath, target_file_path)

        if self.config.is_extract_music:
            music_dir = os.path.dirname(self.config.game_version_client_mp3_dir())
            print(ColorString.confirm('music has been extracted to dir: %s' % music_dir))
            exit(0)

    def donwloadLibraries(self):
        ''' download libraries'''
        libs = resolve_libraries(self.config.game_version_json_obj(), platformType())
        first_url = None
        for lib in libs:
            if is_sigint_up():
                return
            url = lib.get('url')
            sha1 = lib.get('sha1')
            if lib.get('kind') == 'native':
                nativeFilePath = os.path.join(self.config.game_version_client_native_library_dir(),os.path.basename(url))
                if not checkFileExist(nativeFilePath,sha1):
                    first_url = first_url or url
            else:
                libPath = lib.get('path')
                fileDir = self.config.game_version_client_library_dir(libPath)
                filePath=os.path.join(fileDir,os.path.basename(url))
                if not checkFileExist(filePath,sha1):
                    first_url = first_url or url

        if first_url:
            self._ensure_tuned(first_url)
            with ThreadPoolExecutor(max_workers = self.max_workers) as executor:
                in_flight = set()
                limit = self.max_workers * 8
                total = 0
                for lib in libs:
                    url = lib.get('url')
                    sha1 = lib.get('sha1')
                    if lib.get('kind') == 'native':
                        dir_path = self.config.game_version_client_native_library_dir()
                        nativeFilePath = os.path.join(dir_path, os.path.basename(url))
                        if not checkFileExist(nativeFilePath, sha1):
                            total += 1
                    else:
                        libPath = lib.get('path')
                        dir_path = self.config.game_version_client_library_dir(libPath)
                        filePath = os.path.join(dir_path, os.path.basename(url))
                        if not checkFileExist(filePath, sha1):
                            total += 1
                progress = tqdm(total = total, unit = 'files', desc = 'libraries')
                for lib in libs:
                    if is_sigint_up():
                        return
                    url = lib.get('url')
                    sha1 = lib.get('sha1')
                    if lib.get('kind') == 'native':
                        dir_path = self.config.game_version_client_native_library_dir()
                        nativeFilePath = os.path.join(dir_path, os.path.basename(url))
                        if checkFileExist(nativeFilePath, sha1):
                            continue
                    else:
                        libPath = lib.get('path')
                        dir_path = self.config.game_version_client_library_dir(libPath)
                        filePath = os.path.join(dir_path, os.path.basename(url))
                        if checkFileExist(filePath, sha1):
                            continue

                    while len(in_flight) >= limit:
                        done, in_flight = wait(in_flight, return_when = FIRST_COMPLETED)
                        for f in done:
                            f.result()
                            progress.update(1)
                    in_flight.add(executor.submit(self.download, url, dir_path, None, None, False))
                for f in as_completed(in_flight):
                    f.result()
                    progress.update(1)
                progress.close()
        
        self.downloadFabricLibraries()

    def downloadPaperServerJarFile(self):
        '''下载Paper服务端JAR文件'''
        url = None
        if self.config.api == 'v1':
            url = PaperAPI.downloadURLV1(
                project_name = 'paper',
                project_version = self.config.version,
                build_id = 'latest'
            )
        elif self.config.api == 'v2':
            url = PaperAPI.downloadURLV2(
                version = self.config.version
            )

        if url and len(url) > 0:
            self.download(
                url, 
                self.config.game_version_server_dir(), 
                self.config.game_version_server_jar_filename(), 
                prefix_desc='paper server file'
            )


    def download(self, url, dir, name = None, prefix_desc = None, use_progress = True, headers = None, cookies = None):
        '''通用下载方法'''
        url = self.redirectUrl(url=url)

        if is_sigint_up():
            return

        if name == None:
            filename = os.path.basename(url)
        else:
            filename = name
        
        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                target_file = os.path.join(dir,filename)
                temp_key = hashlib.sha1(url.encode('utf-8')).hexdigest()
                download_temp_file = os.path.join(self.config.game_download_temp_dir(), temp_key + '_' + filename)
                self.fs.ensure_dir(dir)
                self.fs.ensure_dir(self.config.game_download_temp_dir())

                temp_size = os.path.getsize(download_temp_file) if os.path.exists(download_temp_file) else 0
                range_headers = {}
                if temp_size > 0:
                    range_headers['Range'] = 'bytes=%d-' % temp_size
                if headers:
                    range_headers.update(headers)

                res = self.http.get(url, stream = True, headers = range_headers if range_headers else headers, cookies = cookies)
                if res.status_code >= 400:
                    raise RuntimeError('download failed: %s' % res.status_code)

                use_append = temp_size > 0 and res.status_code == 206
                mode = 'ab' if use_append else 'wb'
                total_for_progress = None
                content_length = res.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    total_for_progress = int(content_length)
                if use_progress:
                    desc = ((prefix_desc + ' - ') if prefix_desc else  '') + 'downloading: %s' % filename
                    progress = tqdm(total = total_for_progress, unit = 'B', unit_scale = True, desc = desc) if total_for_progress else None
                else:
                    progress = None

                with open(download_temp_file, mode) as f:
                    for chunk in res.iter_content(self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            if progress:
                                progress.update(len(chunk))
                res.close()

                if progress:
                    progress.close()

                if os.path.exists(target_file):
                    os.remove(target_file)
                shutil.move(download_temp_file, target_file)
                return
            except Exception as e:
                print(e)
                print(ColorString.error('download failed: %s' % url))
                sleep(1)
                if attempts >= 3:
                    print(ColorString.error('retry 3 times and failed! jump to donwload next url'))
                    return

    def _ensure_tuned(self, test_url):
        if self._tuned:
            return
        mbps = self._probe_mbps(test_url)
        cpu = os.cpu_count() or 4
        if mbps < 2:
            workers = 8
        elif mbps < 8:
            workers = 16
        elif mbps < 20:
            workers = 32
        else:
            workers = 48
        self.max_workers = min(64, max(8, min(workers, cpu * 8)))
        if mbps > 30:
            self.chunk_size = 4 * 1024 * 1024
        elif mbps > 10:
            self.chunk_size = 2 * 1024 * 1024
        else:
            self.chunk_size = 1024 * 1024
        pool = max(64, self.max_workers * 4)
        self.http = HttpClient(timeout = 10, pool_connections = pool, pool_maxsize = pool)
        self._tuned = True

    def _probe_mbps(self, url, bytes_limit = 1024 * 1024):
        start = time.perf_counter()
        read_bytes = 0
        headers = {'Range': 'bytes=0-%d' % (bytes_limit - 1)}
        try:
            res = self.http.get(url, stream = True, headers = headers)
            for chunk in res.iter_content(64 * 1024):
                if not chunk:
                    continue
                read_bytes += len(chunk)
                if read_bytes >= bytes_limit:
                    break
            res.close()
        except Exception:
            return 0
        elapsed = time.perf_counter() - start
        if elapsed <= 0:
            return 0
        return (read_bytes / 1024.0 / 1024.0) / elapsed

    def redirectUrl(self,url):

        domain = getUrlDomain(url)
        if domain and self.config.is_client and self.config.bmclapi:
            redirected_url = changeUrlDomain(url, BMCLAPI.mojang_bmclapi_domain_map[domain])
            if self.config.debug:
                print(redirected_url)
            return redirected_url

        return url

    def downloadFabricLibraries(self):
        if self.config.isPure and self.config.fabric:
            for (url, file_path) in Fabric.downloadLibrariesMap(self.config).items():
                dir_path = os.path.dirname(file_path)
                if not os.path.exists(dir_path):
                    self.download(
                        url,
                        dir_path,
                        prefix_desc = 'Fabric:'
                    )
