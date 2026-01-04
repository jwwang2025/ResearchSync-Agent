"""
知识库管理器

该模块负责知识库的文档管理，包括：
- 从各种来源加载文档
- 批量文档处理
- 知识库统计和维护
"""

from typing import List, Dict, Any, Optional
import os
import logging
from pathlib import Path
from urllib.parse import urlparse
import tempfile

# LangChain文档加载器
try:
    from langchain.document_loaders import (
        WebBaseLoader,
        PyPDFLoader,
        DirectoryLoader,
        TextLoader,
        UnstructuredFileLoader
    )
    from langchain.docstore.document import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Document = dict  # 备用定义

from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    知识库管理器

    负责文档的加载、处理和管理，为RAG系统提供知识来源。
    """

    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.pdf': 'pdf',
        '.md': 'markdown',
        '.html': 'html',
        '.htm': 'html'
    }

    def __init__(self, vector_store: VectorStoreManager):
        """
        初始化知识库管理器

        参数:
            vector_store: 向量存储管理器实例
        """
        self.vector_store = vector_store

        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain未安装，将使用基础文档加载功能")

    def load_from_url(
        self,
        url: str,
        collection_name: str = "research_kb",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从URL加载文档

        参数:
            url: 文档URL
            collection_name: 目标集合名称
            metadata: 额外的元数据

        返回:
            包含加载结果的字典
        """
        if not LANGCHAIN_AVAILABLE:
            return {
                'success': False,
                'error': 'LangChain未安装，无法加载URL文档',
                'chunks_loaded': 0
            }

        try:
            logger.info(f"Loading document from URL: {url}")

            # 验证URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("无效的URL格式")

            # 加载文档
            loader = WebBaseLoader(url)
            documents = loader.load()

            if not documents:
                return {
                    'success': False,
                    'error': '未能从URL加载到文档内容',
                    'chunks_loaded': 0
                }

            # 添加来源元数据
            for doc in documents:
                doc.metadata.update({
                    'source': 'url',
                    'url': url,
                    'domain': parsed_url.netloc
                })
                if metadata:
                    doc.metadata.update(metadata)

            # 添加到向量数据库
            chunks_loaded = self.vector_store.add_documents(documents, collection_name)

            logger.info(f"Successfully loaded {chunks_loaded} chunks from URL: {url}")

            return {
                'success': True,
                'chunks_loaded': chunks_loaded,
                'documents_count': len(documents),
                'source': 'url',
                'url': url
            }

        except Exception as e:
            logger.error(f"Failed to load from URL {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chunks_loaded': 0
            }

    def load_from_file(
        self,
        file_path: str,
        collection_name: str = "research_kb",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从文件加载文档

        参数:
            file_path: 文件路径
            collection_name: 目标集合名称
            metadata: 额外的元数据

        返回:
            包含加载结果的字典
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'文件不存在: {file_path}',
                'chunks_loaded': 0
            }

        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.pdf':
                return self._load_pdf_file(file_path, collection_name, metadata)
            elif file_ext in ['.txt', '.md']:
                return self._load_text_file(file_path, collection_name, metadata)
            elif file_ext in ['.html', '.htm']:
                return self._load_html_file(file_path, collection_name, metadata)
            else:
                return self._load_generic_file(file_path, collection_name, metadata)

        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chunks_loaded': 0
            }

    def load_from_directory(
        self,
        directory_path: str,
        collection_name: str = "research_kb",
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        从目录批量加载文档

        参数:
            directory_path: 目录路径
            collection_name: 目标集合名称
            recursive: 是否递归处理子目录
            file_extensions: 要处理的文件的扩展名列表

        返回:
            包含批量加载结果的字典
        """
        if not os.path.exists(directory_path):
            return {
                'success': False,
                'error': f'目录不存在: {directory_path}',
                'total_files': 0,
                'loaded_files': 0,
                'total_chunks': 0
            }

        if file_extensions is None:
            file_extensions = list(self.SUPPORTED_EXTENSIONS.keys())

        # 查找文件
        all_files = []
        path_obj = Path(directory_path)

        pattern = "**/*" if recursive else "*"
        for file_path in path_obj.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                all_files.append(str(file_path))

        if not all_files:
            return {
                'success': False,
                'error': '目录中没有找到支持的文件',
                'total_files': 0,
                'loaded_files': 0,
                'total_chunks': 0
            }

        # 批量加载文件
        loaded_files = 0
        total_chunks = 0
        errors = []

        for file_path in all_files:
            try:
                result = self.load_from_file(
                    file_path,
                    collection_name,
                    metadata={'source': 'directory', 'directory': directory_path}
                )

                if result['success']:
                    loaded_files += 1
                    total_chunks += result['chunks_loaded']
                else:
                    errors.append(f"{file_path}: {result['error']}")

            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        return {
            'success': loaded_files > 0,
            'total_files': len(all_files),
            'loaded_files': loaded_files,
            'total_chunks': total_chunks,
            'errors': errors
        }

    def get_collection_stats(self, collection_name: str = "research_kb") -> Dict[str, Any]:
        """
        获取集合统计信息

        参数:
            collection_name: 集合名称

        返回:
            包含统计信息的字典
        """
        return self.vector_store.get_collection_stats(collection_name)

    def list_collections(self) -> List[str]:
        """
        列出所有集合

        返回:
            集合名称列表
        """
        return self.vector_store.list_collections()

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合

        参数:
            collection_name: 要删除的集合名称

        返回:
            删除是否成功
        """
        return self.vector_store.delete_collection(collection_name)

    def clear_collection(self, collection_name: str) -> bool:
        """
        清空集合内容

        参数:
            collection_name: 要清空的集合名称

        返回:
            清空是否成功
        """
        return self.vector_store.clear_collection(collection_name)

    def _load_pdf_file(
        self,
        file_path: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """加载PDF文件"""
        if not LANGCHAIN_AVAILABLE:
            return self._load_text_fallback(file_path, collection_name, metadata, 'pdf')

        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            # 添加元数据
            for doc in documents:
                doc.metadata.update({
                    'source': 'file',
                    'file_path': file_path,
                    'file_type': 'pdf',
                    'file_name': os.path.basename(file_path)
                })
                if metadata:
                    doc.metadata.update(metadata)

            chunks_loaded = self.vector_store.add_documents(documents, collection_name)

            return {
                'success': True,
                'chunks_loaded': chunks_loaded,
                'file_type': 'pdf',
                'pages': len(documents)
            }

        except Exception as e:
            return self._load_text_fallback(file_path, collection_name, metadata, 'pdf')

    def _load_text_file(
        self,
        file_path: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """加载文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 创建Document对象
            doc = Document(
                page_content=content,
                metadata={
                    'source': 'file',
                    'file_path': file_path,
                    'file_type': Path(file_path).suffix.lower(),
                    'file_name': os.path.basename(file_path),
                    **(metadata or {})
                }
            )

            chunks_loaded = self.vector_store.add_documents([doc], collection_name)

            return {
                'success': True,
                'chunks_loaded': chunks_loaded,
                'file_type': 'text',
                'file_size': len(content)
            }

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': 'file',
                        'file_path': file_path,
                        'file_type': Path(file_path).suffix.lower(),
                        'file_name': os.path.basename(file_path),
                        'encoding': 'gbk',
                        **(metadata or {})
                    }
                )
                chunks_loaded = self.vector_store.add_documents([doc], collection_name)
                return {
                    'success': True,
                    'chunks_loaded': chunks_loaded,
                    'file_type': 'text',
                    'encoding': 'gbk'
                }
            except Exception as e2:
                return {
                    'success': False,
                    'error': f'文件编码错误: {str(e2)}',
                    'chunks_loaded': 0
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'chunks_loaded': 0
            }

    def _load_html_file(
        self,
        file_path: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """加载HTML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单的HTML清理（移除标签）
            import re
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()

            doc = Document(
                page_content=clean_content,
                metadata={
                    'source': 'file',
                    'file_path': file_path,
                    'file_type': 'html',
                    'file_name': os.path.basename(file_path),
                    **(metadata or {})
                }
            )

            chunks_loaded = self.vector_store.add_documents([doc], collection_name)

            return {
                'success': True,
                'chunks_loaded': chunks_loaded,
                'file_type': 'html'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'chunks_loaded': 0
            }

    def _load_generic_file(
        self,
        file_path: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用通用加载器加载文件"""
        if LANGCHAIN_AVAILABLE:
            try:
                loader = UnstructuredFileLoader(file_path)
                documents = loader.load()

                # 添加元数据
                for doc in documents:
                    doc.metadata.update({
                        'source': 'file',
                        'file_path': file_path,
                        'file_name': os.path.basename(file_path),
                        **(metadata or {})
                    })

                chunks_loaded = self.vector_store.add_documents(documents, collection_name)

                return {
                    'success': True,
                    'chunks_loaded': chunks_loaded,
                    'file_type': 'generic'
                }

            except Exception:
                pass

        # 回退到文本加载
        return self._load_text_fallback(file_path, collection_name, metadata, 'generic')

    def _load_text_fallback(
        self,
        file_path: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]],
        file_type: str
    ) -> Dict[str, Any]:
        """文本加载回退方案"""
        try:
            # 尝试读取为二进制文件
            with open(file_path, 'rb') as f:
                content = str(f.read()[:10000])  # 只读取前10KB

            doc = Document(
                page_content=f"File content (binary): {content}",
                metadata={
                    'source': 'file',
                    'file_path': file_path,
                    'file_type': file_type,
                    'file_name': os.path.basename(file_path),
                    'load_method': 'fallback',
                    **(metadata or {})
                }
            )

            chunks_loaded = self.vector_store.add_documents([doc], collection_name)

            return {
                'success': True,
                'chunks_loaded': chunks_loaded,
                'file_type': file_type,
                'load_method': 'fallback'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'无法加载文件: {str(e)}',
                'chunks_loaded': 0
            }
