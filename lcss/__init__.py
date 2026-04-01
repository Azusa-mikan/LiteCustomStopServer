from mcdreforged import PluginServerInterface

from .main import PluginMain

pm: PluginMain | None = None

def on_load(server: PluginServerInterface, prev_module) -> None:
    global pm
    pm = PluginMain(server)
    pm.init()
    server.logger.info(server.tr("lcss.loaded"))
    return

def on_unload(server: PluginServerInterface):
    global pm
    if pm is not None:
        pm.plugin_stop()
    server.logger.info(server.tr("lcss.unloaded"))
    return