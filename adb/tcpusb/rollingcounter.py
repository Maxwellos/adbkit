class RollingCounter:
    """
    RollingCounter 类实现了一个在指定范围内循环的计数器。

    当计数器达到最大值时，它会重置为最小值并继续计数。

    属性:
        max (int): 计数器的最大值。
        min (int): 计数器的最小值，默认为 1。
        now (int): 当前计数器的值。
    """

    def __init__(self, max_value: int, min_value: int = 1):
        """
        初始化 RollingCounter 实例。

        参数:
            max_value (int): 计数器的最大值。
            min_value (int, 可选): 计数器的最小值，默认为 1。
        """
        self.max = max_value
        self.min = min_value
        self.now = self.min

    def next(self) -> int:
        """
        返回计数器的下一个值。

        如果当前值小于最大值，则递增当前值。
        如果当前值等于最大值，则重置为最小值。

        返回:
            int: 计数器的下一个值。
        """
        if self.now >= self.max:
            self.now = self.min
        else:
            self.now += 1
        return self.now
