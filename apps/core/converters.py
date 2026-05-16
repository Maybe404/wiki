"""自定义 URL 路径转换器。"""


class UnicodeSlugConverter:
    """支持中文等 Unicode 字符的 slug 转换器。

    Django 内置 `slug` 转换器的正则为 ``[-a-zA-Z0-9_]+``，无法匹配
    `SlugField(allow_unicode=True)` 生成的中文 slug，会导致中文 slug
    文档在路由阶段直接 404。此转换器用 ``\\w``（Unicode 词字符）放宽。
    """

    regex = r"[-\w]+"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value
