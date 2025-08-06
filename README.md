# OrzPythonMC

OrzMC Writed by Python Language

## 命令行工具

使用 Python3 编写，可以运行在`Ubuntu/MacOS`系统上（系统需要配置有`JAVA`和`Python3`运行环境），功能包括:

1. 部署`Minecraft`私人服务器(Vanilla/Paper/spigot/forge)
2. 启动`Minecraft`客户端功能（Vanilla)
3. 支持的`1.13`以上正式版

工具已上传到`Python`包管理网站 [PyPi][orzmc-pypi]，可以使用`pip`进行安装

```python
$ python3 -m pip install orzmc
$ orzmc -h # 查看使用帮助
```

如果你有兴趣和我一起开发这个Python项目，拉项目到本地, 并配置开发环境，运行下面命令即可配置好开发环境：🤒

```bash
$ git clone --recurse-submodules \
      https://github.com/OrzGeeker/OrzPythonMC.git && \
      cd OrzPythonMC && ./setup && pipenv shell
```

## 使用说明

### 安装

```bash
$ pip install orzmc
```
在`Shell`中执行命令: `orzmc -h` 查看该工具的帮助信息

### OrzMC的能力 

- 使用`Mojang`官方的API下载客户端及相关资源文件并启动Minecraft客户端
- 在`Ubuntu`云服务器上部署你的私人服务器
- 备份私人服务器的地图文件
- 使用`Bukkit`服务端的`ForceUpgrade`选项启动，把低版本的世界地图更新到高版本的世界地图

#### 运行客户端

##### 运行纯净版客户端（交互模式）

```bash
$ pip install orzmc
$ orzmc
```

##### 运行纯净版客户端（命令一键模式）

```bash
$ pip install orzmc
$ orzmc -v 1.14.4 -u player_name
```

##### 运行forge客户端

```bash
$ pip install orzmc
$ orzmc -t forge
```

#### 部署服务端(Ubuntu/MacOS)

##### 使用默认设置部署纯净服

默认设置`JVM`的初始内存为`512M`，最大内存为`2G`

```bash
$ pip install orzmc
$ orzmc -s
```

##### 部署服务端并指定JVM内存分配策略

使用选项手动指定分配给`JVM`的初始内存(`-m`)和最大内存(`-x`)值

```bash
$ pip install orzmc
$ orzmc -s -m 512M -x 2G -v 1.14.4
```

##### 使用`-t`选项部署`Spigot`/`Forge`服务端

###### Spigot服务端部署

- 部署前需要安装`jre`和`git`这两个工具

```bash
$ pip install orzmc
$ orzmc -s -t spigot -m 512M -x 1G -v 1.14.2
```

###### Forge服务端部署

```bash
$ pip install orzmc
$ orzmc -s -t forge -m 512M -x 1G -v 1.14.2
```

由于Forge包是用JDK 8编译的，所以建安装的JDK环境为JDK8系统，不要太高，目前不兼容，会出现无法部署Forge服务器的情况。

---

游戏目录存放在当前用户的家目录下面：`~/minecraft`

## 项目待办

- [ ] 自动安装JRE运行环境
- [ ] 并发下载提高文件下载速度

---

[orzmc-pypi]: <https://pypi.org/project/OrzMC/>
