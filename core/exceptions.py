class BaseError(Exception):
    """插件基础异常"""
    def __init__(self, message="插件发生错误"):
        super().__init__(message)
        self.message = message

class DataLoadError(BaseError):
    """数据加载失败异常"""
    def __init__(self, path, detail=""):
        message = f"数据加载失败 | 路径: {path} | 详情: {detail}"
        super().__init__(message)
        self.path = path  # 可以记录出错的文件路径

class DataSaveError(BaseError):
    """数据保存失败异常"""
    def __init__(self, path, detail=""):
        message = f"数据保存失败 | 路径: {path} | 详情: {detail}"
        super().__init__(message)
        self.path = path