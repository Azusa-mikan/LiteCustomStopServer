from typing import Literal
from pathlib import Path
import contextlib
import pkgutil

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from pydantic import BaseModel, ValidationError
from mcdreforged import PluginServerInterface

from .util import ResourceBundleError

yaml = YAML(typ="rt")
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True

help_message: list[str] = [
    '---------&8&l[&b&lLiteCustomStopServer&8&l]&7&l插件帮助---------',
    '&7指令前缀 !!litecustomstopserver 可简写为 !!litecstopserver 或 !!lcss',
    '&7&l!!lcss 或 !!lcss stop &r&7进入关服倒计时',
    '&7&l!!lcss restart &r&7进入重启倒计时',
    '&7&l!!lcss cancel &r&7取消关服/重启倒计时',
    '&7&l!!lcss reload &r&7重载插件配置',
    '&7&l!!lcss help &r&7查看插件帮助',
    '---------&8&l[&b&lLiteCustomStopServer&8&l]&7&l插件帮助---------'
]

class Config(BaseModel):
    seconds: int
    countdown: list[int]
    timing: bool
    auto_stop_time: list[str]
    auto_restart_time: list[str]
    title_true_or_false: bool

class Messages(BaseModel):
    announcement_prefix: str
    plugin_prefix: str
    shutdown_message: str
    restart_message: str
    shutdown_inseconds: str
    restart_inseconds: str
    shutdown_cancel_announce: str
    restart_cancel_announce: str
    shutdown_already_cancelled: str
    restart_already_cancelled: str
    time_for_shutdown: str
    time_for_restart: str
    shutdown_countdown_already: str
    restart_countdown_already: str
    reload_success: str
    help_message: list[str]

def interface_config(
        server: PluginServerInterface
    ) -> Config:
    config_path = Path(server.get_data_folder(), "config.yml")
    try:
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = pkgutil.get_data("lcss", "resources/config.yml")
            if data is not None:
                config_path.write_bytes(data)
        raw_config = yaml.load(
            config_path.read_text(encoding="utf-8")
        )
        return Config.model_validate(raw_config)
    except (ParserError, ValidationError) as e:
        raise ResourceBundleError(config_path) from e

def interface_messages(
        server: PluginServerInterface
    ) -> Messages:
    messages_path = Path(server.get_data_folder(), "messages.yml")
    try:
        if not messages_path.exists():
            messages_path.parent.mkdir(parents=True, exist_ok=True)
            data = pkgutil.get_data("lcss", "resources/messages.yml")
            if data is not None:
                messages_path.write_bytes(data)
        raw_messages = yaml.load(
            messages_path.read_text(encoding="utf-8")
        )
        return Messages.model_validate(raw_messages)
    except (ParserError, ValidationError) as e:
        raise ResourceBundleError(messages_path) from e

def remove_config_task(
        server: PluginServerInterface,
        raw_time: str,
        type: Literal[
            "auto_stop_time",
            "auto_restart_time"
        ] = "auto_stop_time"
    ) -> None:
    with contextlib.suppress(ParserError):
        config_path = Path(server.get_data_folder(), "config.yml")
        data = yaml.load(
            config_path.read_text(encoding="utf-8")
        )

        task_list: list[str] = data.get(type, [])

        if raw_time in task_list:
            task_list.remove(raw_time)
            if not task_list:
                task_list.append('none')
            
            yaml.dump(data, config_path)
        
        server.logger.info(server.tr("lcss.schedule_delete"))
        return
