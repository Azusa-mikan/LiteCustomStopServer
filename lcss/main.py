from typing import Literal
import json
import threading

from mcdreforged import (
    PluginCommandSource,
    PluginServerInterface,
    CommandSource
)
from mcdreforged.api.command import Literal as CommandLiteral
from mcdreforged.minecraft.rtext.style import RColor
from schedule import Scheduler, CancelJob

from lcss.conmsg import (
    Config,
    Messages,
    help_message,
    interface_config,
    interface_messages, 
    remove_config_task
)
from .util import ResourceBundleError, ColorText

CountdownStatus = Literal["Shutdown", "Restart"]

class PluginMain:
    def __init__(
            self,
            ServerInterface: PluginServerInterface
        ) -> None:
        self.server: PluginServerInterface = ServerInterface
        self._scheduled = Scheduler()
        self.config = interface_config(ServerInterface)
        self.messages = interface_messages(ServerInterface)
        self._sleep_event = threading.Event()
        self._task_event = threading.Event()
        self._lock = threading.Lock()
        self._server_status: CountdownStatus | None = None
        self._seconds: int = self.config.seconds
        self._src: PluginCommandSource = ServerInterface.get_plugin_command_source()
        self._task_threading = threading.Thread(
            target=self.scheduled_task_threading,
            name="LCSSTimer",
            daemon=True
        )

    def _color_replace(self, msg: str) -> ColorText:
        return ColorText(msg.replace("&", "§"))

    def _prefix_color_replace(self, msg: str) -> ColorText:
        return ColorText(
            (f"{self.messages.plugin_prefix} " + msg)
                .replace("&", "§")
        )

    def _title_broadcast(self, prefix: ColorText, msg: ColorText) -> None:
        title_json = json.dumps(
            {"text": prefix},
            ensure_ascii=False
        )
        subtitle_json = json.dumps(
            {"text": msg},
            ensure_ascii=False
        )
        self.server.execute(
            'execute if entity @a run title @a times 10 70 20'
        )
        self.server.execute(
            f'execute if entity @a run title @a title {title_json}'
        )
        self.server.execute(
            f'execute if entity @a run title @a subtitle {subtitle_json}'
        )
        return

    def _server_broadcast(self, msg: str) -> None:
        prefix_msg = self._prefix_color_replace(
            msg
        ).replace("<seconds>", str(self._seconds))
        msg = self._color_replace(
            msg
        ).replace("<seconds>", str(self._seconds))
        self.server.broadcast(prefix_msg)
        if not self.config.title_true_or_false:
            return
        prefix = self._color_replace(self.messages.announcement_prefix)
        self._title_broadcast(prefix, msg)
        return

    def _callback_server_status(
            self,
            src: CommandSource
        ) -> None:
        if self._server_status == "Shutdown":
            src.reply(
                self._prefix_color_replace(self.messages.shutdown_countdown_already)
            )
        elif self._server_status == "Restart":
            src.reply(
                self._prefix_color_replace(self.messages.restart_countdown_already)
            )
        return

    def verify_permission(self, src: CommandSource) -> bool:
        """
        检查用户是否有权限
        """
        verify: bool = src.has_permission(3)
        if not verify:
            src.reply(
                self.server.rtr("lcss.no_permission")
                    .set_color(RColor.red)
            )
            return verify
        return verify

    def _stop_thread(self):
        self._seconds: int = self.config.seconds
        countdown_set: set[int] = set(self.config.countdown)
        try:
            while self._seconds > 0 and not self._sleep_event.is_set():
                if self._seconds in countdown_set:
                    self._server_broadcast(self.messages.shutdown_message)
                self._sleep_event.wait(1)
                self._seconds -= 1
            if not self._sleep_event.is_set(): # 若还未被设置为 set（取消）
                self.server.stop_exit()
                return
        finally:
            self._server_status = None
            self._lock.release()

    def _restart_thread(self):
        self._seconds: int = self.config.seconds
        countdown_set: set[int] = set(self.config.countdown)
        try:
            while self._seconds > 0 and not self._sleep_event.is_set():
                if self._seconds in countdown_set:
                    self._server_broadcast(self.messages.restart_message)
                self._sleep_event.wait(1)
                self._seconds -= 1
            if not self._sleep_event.is_set(): # 若还未被设置为 set（取消）
                self.server.restart()
                return
        finally:
            self._server_status = None
            self._lock.release()

    def server_stop(self, src: CommandSource) -> None:
        """
        停止服务器
        """
        if not self.verify_permission(src):
            return
        if not self._lock.acquire(blocking=False):
            self._callback_server_status(src)
            return
        self._sleep_event.clear()
        self._server_status = "Shutdown"
        self.countdown_t = threading.Thread(
            target=self._stop_thread,
            name="Shutdown"
        )
        self.countdown_t.start()
        return

    def server_restart(self, src: CommandSource) -> None:
        """
        重启服务器
        """
        if not self.verify_permission(src):
            return
        if not self._lock.acquire(blocking=False):
            self._callback_server_status(src)
            return
        self._sleep_event.clear()
        self._server_status = "Restart"
        self.countdown_t = threading.Thread(
            target=self._restart_thread,
            name="Restart"
        )
        self.countdown_t.start()
        return

    def cancel(self, src: CommandSource) -> None:
        """
        取消操作
        """
        if not self.verify_permission(src):
            return
        if self._server_status is None:
            src.reply(
                self._prefix_color_replace(
                    self.messages.shutdown_already_cancelled
                )
            )
            return
        status = self._server_status # 缓存
        self._sleep_event.set()
        if status == "Restart":
            self._server_broadcast(self.messages.restart_cancel_announce)
        elif status == "Shutdown":
            self._server_broadcast(self.messages.shutdown_cancel_announce)
        return

    def plugin_stop(self) -> None:
        """
        停止插件
        """
        self._scheduled.clear()
        self._task_event.set()
        self._sleep_event.set()
        self._server_status = None
        return

    def reload(self, src: CommandSource) -> None:
        self.server.reload_permission_file()
        try:
            self.config: Config = interface_config(self.server)
            self.messages: Messages = interface_messages(self.server)
        except ResourceBundleError as e:
            src.reply(
                self.server.rtr(
                    "lcss.bundle_error"
                ).set_color(RColor.red)
            )
            self.server.logger.exception(
                f"{e.file} Configuration parsing failed"
            )
        else:
            if self.config.timing:
                self._scheduled.clear()
                self._scheduled = Scheduler()
                self.scheduled_task_in_stop()
                self.scheduled_task_in_restart()
                if not self._task_threading.is_alive():
                    self._task_event.clear()
                    self._task_threading = threading.Thread(
                        target=self.scheduled_task_threading,
                        name="LCSSTimer",
                        daemon=True
                    )
                    self._task_threading.start()
            else:
                self._task_event.set()

            src.reply(
                self._prefix_color_replace(
                    self.messages.reload_success
                )
            )
        return

    def help_message(self, src: CommandSource) -> None:
        raw_lines = self.messages.help_message
        if not raw_lines:
            raw_lines = help_message
        first = self._color_replace(raw_lines[0])
        rest = [
            "\n" + self._color_replace(line)
            for line in raw_lines[1:]
        ]
        src.reply(first + "".join(rest))

    def _scheduled_task_stop(
            self,
            is_once: bool,
            raw_time: str
        ):
        self._server_broadcast(self.messages.time_for_shutdown)
        self.server_stop(self._src)
        if is_once:
            remove_config_task(
                self.server,
                raw_time,
                "auto_stop_time"
            )
            return CancelJob
    
    def _scheduled_task_restart(
            self,
            is_once: bool,
            raw_time: str
        ):
        self._server_broadcast(self.messages.time_for_restart)
        self.server_restart(self._src)
        if is_once:
            remove_config_task(
                self.server,
                raw_time,
                "auto_restart_time"
            )
            return CancelJob
    
    def scheduled_task_in_stop(self) -> None:
        for raw_time in self.config.auto_stop_time:
            try:
                if raw_time == 'none':
                    break

                time_part, is_delete_str = raw_time.split(',')
                schedule_time = time_part.replace('-', ':')
                is_once = (is_delete_str.strip() == '1')
                self._scheduled.every().day.at(schedule_time).do(
                self._scheduled_task_stop, 
                is_once=is_once,
                raw_time=raw_time
                )
            except Exception:
                self.server.logger.exception(
                    self.server.tr("lcss.schedule_error")
                )
        return

    def scheduled_task_in_restart(self) -> None:
        for raw_time in self.config.auto_restart_time:
            try:
                if raw_time == 'none':
                    break

                time_part, is_delete_str = raw_time.split(',')
                schedule_time = time_part.replace('-', ':')
                is_once = (is_delete_str.strip() == '1')
                self._scheduled.every().day.at(schedule_time).do(
                self._scheduled_task_restart, 
                is_once=is_once,
                raw_time=raw_time
                )
            except Exception:
                self.server.logger.exception(
                    self.server.tr("lcss.schedule_error")
                )
        return

    def scheduled_task_threading(self) -> None:
        self.server.logger.warning(
            self.server.tr("lcss.schedule_start")
        )

        while not self._task_event.is_set():
            self._scheduled.run_pending()
            self._task_event.wait(30)

        self.server.logger.info(
            self.server.tr("lcss.schedule_stop")
        )

    def register_command(self) -> None:
        # 遍历需要注册的前缀
        for prefix in [
            '!!litecustomstopserver',
            '!!litecstopserver',
            '!!lcss'
        ]:
            # 创建带前缀的主节点，每次都要新建
            cmd = CommandLiteral(prefix).runs(self.server_stop)
            
            # 依次将平行的子节点挂载到主节点上
            cmd.then(CommandLiteral('stop').runs(self.server_stop))
            cmd.then(CommandLiteral('restart').runs(self.server_restart))
            cmd.then(CommandLiteral('cancel').runs(self.cancel))
            cmd.then(CommandLiteral('reload').runs(self.reload))
            cmd.then(CommandLiteral('help').runs(self.help_message))
            
            # 最后注册构建好的完整指令树
            self.server.register_command(cmd)
        return

    def init(self):
        self.register_command()

        if self.config.timing:
            self.scheduled_task_in_stop()
            self.scheduled_task_in_restart()
            self._task_threading.start()

        return
