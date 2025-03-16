"""
项目配置模块，用于导出配置设置
这是为了兼容代码中使用from app.config import settings的导入方式
"""

from app.core.config import settings

# 导出settings以允许 from app.config import settings
__all__ = ["settings"] 