# -*- coding: utf8 -*-

from .Config import Config
from .Console import Console
from .usecases import ClientUseCase, ServerUseCase

from ..utils.utils import *
from ..utils.ColorString import ColorString
from ..core.Oracle import Oracle
from .Downloader import Downloader

class Game:

    def __init__(self, config):
        self.config = config
        self.console = Console(self.config)
        self.usecase = ClientUseCase(self.config) if self.config.is_client else ServerUseCase(self.config)
        
    def start(self):

        # 检查是否安装JDK
        Oracle.install_jdk()

        # 控制台用户交互展示
        self.console.userInteraction()

        if self.config.debug:
            self.usecase.plan().run()
        else:
            try:
                #启动游戏
                self.usecase.plan().run()
                
            except Exception as e:
                print(e)
                print(ColorString.warn('Start Failed!!!'))
