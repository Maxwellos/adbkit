from typing import Dict, Any, Optional

class ServiceMap:
    """
    ServiceMap 类用于管理远程服务连接。
    
    它维护了一个远程 ID 到 socket 的映射，并提供了添加、获取、移除和结束所有服务的方法。
    """

    def __init__(self):
        """
        初始化 ServiceMap 实例。
        """
        self.remotes: Dict[int, Any] = {}
        self.count: int = 0

    def end(self):
        """
        结束所有远程服务连接并重置 ServiceMap。
        """
        for remote in self.remotes.values():
            remote.end()
        self.remotes.clear()
        self.count = 0

    def insert(self, remote_id: int, socket: Any) -> Any:
        """
        插入新的远程服务连接。

        Args:
            remote_id (int): 远程服务的 ID。
            socket (Any): 与远程服务关联的 socket 对象。

        Returns:
            Any: 插入的 socket 对象。

        Raises:
            ValueError: 如果 remote_id 已经存在。
        """
        if remote_id in self.remotes:
            raise ValueError(f"Remote ID {remote_id} is already being used")
        self.count += 1
        self.remotes[remote_id] = socket
        return socket

    def get(self, remote_id: int) -> Optional[Any]:
        """
        获取指定 remote_id 的 socket 对象。

        Args:
            remote_id (int): 远程服务的 ID。

        Returns:
            Optional[Any]: 如果找到则返回 socket 对象，否则返回 None。
        """
        return self.remotes.get(remote_id)

    def remove(self, remote_id: int) -> Optional[Any]:
        """
        移除并返回指定 remote_id 的 socket 对象。

        Args:
            remote_id (int): 远程服务的 ID。

        Returns:
            Optional[Any]: 如果找到并移除则返回 socket 对象，否则返回 None。
        """
        if remote_id in self.remotes:
            remote = self.remotes.pop(remote_id)
            self.count -= 1
            return remote
        return None
