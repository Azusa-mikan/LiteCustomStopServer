# LiteCustomStopServer

[![](https://img.shields.io/badge/license-CC--BY--NC--SA--4.0-green)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

这是一个为 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 设计的优雅关服/重启插件，支持倒计时广播与定时任务功能。

本插件是基于 [Katorly](https://github.com/katorly) 的同名 Bukkit 插件 [LiteCustomStopServer](https://github.com/katorly/LiteCustomStopServer) 移植并重构的 MCDR 版本。

## 特色功能

- **倒计时关服/重启**：执行指令后不会立刻关闭服务器，而是进入倒计时，并在公屏和标题（Title）进行全服动态广播，给玩家充足的准备时间。
- **随时取消**：倒计时期间，管理员可以随时使用指令取消关服/重启进程。
- **定时任务系统**：支持在配置文件中设定每天固定时间自动触发关服或重启。
- **一次性定时任务**：支持设置“执行一次后自动删除”的定时任务，任务执行完毕后插件会自动从配置文件中抹除该记录，彻底释放双手。
- **高度自定义**：支持完全自定义的提示信息、倒计时总秒数、需要广播的特定秒数节点以及标题显示开关。
- **无缝热重载**：修改配置后直接使用 `!!lcss reload` 即可瞬间生效，包括重新调度定时任务，无需重启 MCDR。

## 安装与依赖

本插件依赖一些第三方 Python 库以实现高级功能。请在你的 MCDR 环境下运行以下命令安装依赖：

```bash
pip install schedule pydantic
```

安装好依赖后，将本插件放置于 MCDR 的 `plugins` 目录下，启动 MCDR 即可自动加载。

## 指令与权限

触发指令前缀支持：`!!litecustomstopserver`、`!!litecstopserver` 或简写 **`!!lcss`**。
执行以下指令默认需要 **权限等级 3**（管理员）。

- `!!lcss` 或 `!!lcss stop`：进入关服倒计时
- `!!lcss restart`：进入重启倒计时
- `!!lcss cancel`：取消当前正在运行的关服/重启倒计时
- `!!lcss reload`：热重载插件配置与语言文件
- `!!lcss help`：查看插件帮助信息

## 配置文件

插件首次加载后，会在 `config/LiteCustomStopServer` 目录下自动生成两个配置文件：

### `config.yml`
核心逻辑配置。你可以调整倒计时的总时长、指定需要触发广播的秒数集合，以及设定**定时任务**。
定时任务格式为列表，单项格式示例：`HH-mm,是否删除`。
- `0` 表示每天循环执行。
- `1` 表示仅执行一次，执行后自动从本文件中删除。

### `messages.yml`
全文本配置文件。支持使用传统的 `&` 符号配置颜色和样式（如 `&a`、`&l` 等），你可以随心所欲地修改所有提示信息、前缀和广播文本。

## 鸣谢与授权

非常感谢原作者 **[Katorly](https://github.com/katorly)** 的开源精神与最初的灵感启发。

本项目已由我移植至 MCDR 平台，并使用现代化的 Python 代码进行了彻底重构，新增了高级定时任务系统、并发控制与热重载支持。
本项目已获得原作者授权，允许基于 [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) 协议对原作品进行演绎与发布。
