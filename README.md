# OrzPythonMC

OrzMC Writed by Python Language

## 命令行工具

使用 Python3 编写，可以运行在`Ubuntu/MacOS`系统上（系统需要配置有`JAVA`和`Python3`运行环境），功能包括:

1. 部署`Minecraft`私人服务器(Vanilla/Paper/spigot/forge)
2. 启动`Minecraft`客户端功能（Vanilla)
3. 支持的`1.13`以上正式版

工具已上传到`Python`包管理网站 [PyPi][orzmc-pypi]，可以使用`pip`进行安装

```python
$ pip install orzmc
$ orzmc -h # 查看使用帮助
```

如果你有兴趣和我一起开发这个Python项目，拉项目到本地, 并配置开发环境，运行下面命令即可配置好开发环境：🤒

```bash
$ git clone --recurse-submodules \
      https://github.com/OrzGeeker/OrzMC.git && \
      cd OrzMC && ./config_orzmc_dev && pipenv shell
```

## 项目待办

- [ ] 自动安装JRE运行环境
- [ ] 并发下载提高文件下载速度

---

[orzmc-pypi]: <https://pypi.org/project/OrzMC/>