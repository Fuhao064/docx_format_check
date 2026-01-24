"""
数据验证模型

使用 Pydantic 定义 API 请求和响应的数据模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class FileUploadRequest(BaseModel):
    """文件上传请求验证"""
    # 实际上通过 FormData 上传，这里用于文档
    file: Optional[str] = None
    filename: Optional[str] = None


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    file: Dict[str, str] = Field(default_factory=dict)


class FileMetadata(BaseModel):
    """文件元数据"""
    id: str
    original_name: str
    timestamped_name: str
    size: int
    upload_time: str
    task_id: Optional[str] = None
    status: str = Field(..., regex="^(pending|uploading|completed|error)$")
    path: Optional[str] = None


class DocumentCheckRequest(BaseModel):
    """文档检查请求验证"""
    doc_path: str = Field(..., min_length=1, description="文档路径")
    config_path: str = Field(..., min_length=1, description="配置文件路径")
    use_llm: bool = Field(default=True, description="是否使用LLM")


class DocumentCheckResponse(BaseModel):
    """文档检查响应验证"""
    success: bool
    message: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    para_manager: Optional[Dict[str, Any]] = None


class TaskStatusUpdate(BaseModel):
    """任务状态更新"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., regex="^(pending|in_progress|completed|error)$", description="任务状态")
    progress: float = Field(..., ge=0, le=100, description="进度百分比")
    message: Optional[str] = Field(None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")


class AnalysisProgress(BaseModel):
    """分析进度更新"""
    task_id: str
    stage: str
    message: str
    progress: float = Field(..., ge=0, le=100)
    timestamp: str


class NotificationMessage(BaseModel):
    """通知消息"""
    level: str = Field(..., regex="^(success|warning|error|info)$")
    title: str
    message: str
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: str


class ApplyFormatRequest(BaseModel):
    """应用格式请求"""
    doc_path: str = Field(..., description="文档路径")
    config_path: str = Field(..., description="配置文件路径")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    original_filename: str = Field(..., description="原始文件名")
    para_manager: Optional[List[Dict[str, Any]]] = Field(None, description="段落管理器数据")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., min_length=1, description="消息内容")
    doc_path: str = Field(..., description="文档路径")
    config_path: Optional[str] = Field(None, description="配置文件路径")
    para_manager: Optional[List[Dict[str, Any]]] = Field(None, description="段落管理器数据")


class AnalyzeParagraphRequest(BaseModel):
    """分析段落请求"""
    doc_path: str = Field(..., description="文档路径")
    para_index: int = Field(..., ge=0, description="段落索引")
    context_range: int = Field(default=2, ge=0, description="上下文范围")
    para_manager: Optional[List[Dict[str, Any]]] = Field(None, description="段落管理器数据")


class EnhanceParagraphsRequest(BaseModel):
    """增强段落请求"""
    doc_path: str = Field(..., description="文档路径")
    para_indices: Optional[List[int]] = Field(None, description="段落索引列表")
    para_manager: Optional[List[Dict[str, Any]]] = Field(None, description="段落管理器数据")


class ModelConfigRequest(BaseModel):
    """模型配置请求"""
    provider: str = Field(..., description="提供商名称")
    model_key: str = Field(..., description="模型标识")
    model_name: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")


class SetAgentModelRequest(BaseModel):
    """设置代理模型请求"""
    agent_type: str = Field(..., regex="^(format|editor|advice|communicate)$", description="代理类型")
    model_name: str = Field(..., description="模型名称")


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    doc_path: str = Field(..., description="文档路径")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="错误列表")
    config_path: Optional[str] = Field(None, description="配置文件路径")
    original_filename: Optional[str] = Field(None, description="原始文件名")


class CreateConfigRequest(BaseModel):
    """创建配置请求"""
    config_path: str = Field(..., description="配置文件路径")
    config_data: Dict[str, Any] = Field(..., description="配置数据")
