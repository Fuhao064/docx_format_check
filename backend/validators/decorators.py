"""
验证装饰器

提供请求验证的装饰器
"""

from functools import wraps
from flask import jsonify, request
from typing import Type, Any, Callable, Optional


def validate_request(schema_class: Type[Any]):
    """
    请求验证装饰器

    Args:
        schema_class: Pydantic 模型类

    Returns:
        装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                if request.is_json:
                    data = request.get_json()
                    # 验证请求数据
                    validated_data = schema_class(**data)
                    # 将验证后的数据添加到 kwargs 中
                    kwargs['validated_data'] = validated_data
                    return f(*args, **kwargs)
                else:
                    # 对于非 JSON 请求（如文件上传），不进行验证
                    return f(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'请求验证失败: {str(e)}'
                }), 400
        return wrapper
    return decorator


def catch_errors(f: Optional[Callable] = None, *, return_json: bool = True, log_errors: bool = True):
    """
    错误捕获装饰器

    Args:
        f: 被装饰的函数
        return_json: 是否返回 JSON 响应
        log_errors: 是否记录错误日志

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    import traceback
                    print(f"错误在 {func.__name__}: {str(e)}")
                    traceback.print_exc()

                if return_json:
                    return jsonify({
                        'success': False,
                        'message': f'服务器错误: {str(e)}'
                    }), 500
                raise
        return wrapper

    if f is not None:
        return decorator(f)
    return decorator
