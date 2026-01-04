"""
RAG API路由

提供RAG功能的REST API接口，包括：
- 知识库管理
- 文档上传和检索
- RAG增强查询
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
import tempfile
import logging
from pathlib import Path

# RAG组件导入
from ...rag.vector_store import VectorStoreManager
from ...rag.retriever import RAGRetriever
from ...rag.knowledge_manager import KnowledgeManager

# LLM工厂导入（用于RAG检索器）
from ...llm.factory import LLMFactory

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局组件实例（在实际应用中应该通过依赖注入管理）
_vector_store = None
_rag_retriever = None
_knowledge_manager = None

def get_rag_components():
    """获取或初始化RAG组件"""
    global _vector_store, _rag_retriever, _knowledge_manager

    if _vector_store is None:
        # 从配置获取向量存储路径（简化版，实际应该从配置管理器获取）
        persist_dir = os.getenv("RAG_VECTOR_STORE_PATH", "./data/chroma_db")
        _vector_store = VectorStoreManager(persist_directory=persist_dir)

    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager(_vector_store)

    if _rag_retriever is None:
        # 初始化LLM（这里使用默认配置，实际应该从配置管理器获取）
        try:
            llm_factory = LLMFactory()
            llm = llm_factory.create_llm("deepseek")  # 默认使用DeepSeek
            _rag_retriever = RAGRetriever(_vector_store, llm)
        except Exception as e:
            logger.warning(f"Failed to initialize LLM for RAG: {e}")
            _rag_retriever = None

    return _vector_store, _rag_retriever, _knowledge_manager


@router.post("/knowledge/upload-url")
async def upload_from_url(
    url: str,
    collection: str = "research_kb",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    从URL上传文档到知识库

    参数:
        url: 文档URL
        collection: 目标集合名称
        metadata: 额外的元数据
    """
    try:
        _, _, knowledge_manager = get_rag_components()

        result = knowledge_manager.load_from_url(url, collection, metadata)

        if result['success']:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Successfully loaded {result['chunks_loaded']} document chunks from URL",
                    "data": result
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"URL upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/upload-file")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str = "research_kb",
    metadata: Optional[str] = None  # JSON字符串
):
    """
    上传文件到知识库

    参数:
        file: 上传的文件
        collection: 目标集合名称
        metadata: JSON格式的额外元数据
    """
    try:
        # 解析元数据
        file_metadata = {}
        if metadata:
            try:
                import json
                file_metadata = json.loads(metadata)
            except:
                pass  # 忽略无效的元数据

        # 保存上传的文件到临时目录
        upload_dir = Path("./data/uploads")
        upload_dir.mkdir(exist_ok=True, parents=True)

        file_path = upload_dir / f"{file.filename}"
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # 异步处理文件（避免阻塞）
        background_tasks.add_task(process_uploaded_file, str(file_path), collection, file_metadata)

        return JSONResponse(
            status_code=202,  # Accepted
            content={
                "status": "processing",
                "message": f"File {file.filename} uploaded and queued for processing",
                "file_path": str(file_path)
            }
        )

    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/upload-directory")
async def upload_directory(
    background_tasks: BackgroundTasks,
    directory_path: str,
    collection: str = "research_kb",
    recursive: bool = True,
    file_extensions: Optional[List[str]] = None
):
    """
    从目录批量上传文档

    参数:
        directory_path: 目录路径
        collection: 目标集合名称
        recursive: 是否递归处理子目录
        file_extensions: 文件扩展名列表
    """
    try:
        _, _, knowledge_manager = get_rag_components()

        # 异步处理目录上传
        background_tasks.add_task(
            process_directory_upload,
            directory_path,
            collection,
            recursive,
            file_extensions
        )

        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": f"Directory {directory_path} queued for processing",
                "collection": collection
            }
        )

    except Exception as e:
        logger.error(f"Directory upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_stats(collection: str = "research_kb"):
    """获取知识库统计信息"""
    try:
        _, _, knowledge_manager = get_rag_components()
        stats = knowledge_manager.get_collection_stats(collection)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stats": stats
            }
        )

    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/collections")
async def list_collections():
    """列出所有知识库集合"""
    try:
        _, _, knowledge_manager = get_rag_components()
        collections = knowledge_manager.list_collections()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "collections": collections
            }
        )

    except Exception as e:
        logger.error(f"Failed to list collections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """删除知识库集合"""
    try:
        _, _, knowledge_manager = get_rag_components()

        success = knowledge_manager.delete_collection(collection_name)

        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"Collection '{collection_name}' deleted successfully"
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"Failed to delete collection '{collection_name}'")

    except Exception as e:
        logger.error(f"Failed to delete collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(
    query: str,
    collection: str = "research_kb",
    top_k: int = 5,
    temperature: float = 0.3,
    include_sources: bool = True
):
    """
    执行RAG增强查询

    参数:
        query: 查询内容
        collection: 知识库集合名称
        top_k: 检索文档数量
        temperature: 生成温度
        include_sources: 是否包含来源信息
    """
    try:
        _, rag_retriever, _ = get_rag_components()

        if rag_retriever is None:
            raise HTTPException(status_code=503, detail="RAG retriever not available")

        result = rag_retriever.retrieve_and_generate(
            query=query,
            collection_name=collection,
            top_k=top_k,
            temperature=temperature
        )

        # 格式化响应
        response_data = {
            "status": "success",
            "query": result["query"],
            "response": result["generated_response"],
            "context_used": result["context_used"],
            "retrieved_count": result.get("filtered_count", 0)
        }

        if include_sources and result.get("retrieved_documents"):
            response_data["sources"] = [
                {
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "score": doc.get("score"),
                    "metadata": doc.get("metadata", {})
                }
                for doc in result["retrieved_documents"][:3]  # 只返回前3个来源
            ]

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        logger.error(f"RAG query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/retrieve-only")
async def retrieve_only(
    query: str,
    collection: str = "research_kb",
    top_k: int = 5
):
    """
    仅执行文档检索，不进行生成

    参数:
        query: 查询内容
        collection: 知识库集合名称
        top_k: 检索文档数量
    """
    try:
        _, rag_retriever, _ = get_rag_components()

        if rag_retriever is None:
            raise HTTPException(status_code=503, detail="RAG retriever not available")

        results = rag_retriever.retrieve_only(
            query=query,
            collection_name=collection,
            top_k=top_k
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "query": query,
                "results": results,
                "count": len(results)
            }
        )

    except Exception as e:
        logger.error(f"Retrieval only failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 后台任务函数

async def process_uploaded_file(file_path: str, collection: str, metadata: Dict[str, Any]):
    """处理上传的文件（后台任务）"""
    try:
        _, _, knowledge_manager = get_rag_components()
        result = knowledge_manager.load_from_file(file_path, collection, metadata)

        if result['success']:
            logger.info(f"Successfully processed uploaded file: {file_path}, chunks: {result['chunks_loaded']}")
        else:
            logger.error(f"Failed to process uploaded file: {file_path}, error: {result.get('error', 'Unknown error')}")

        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Background file processing failed for {file_path}: {str(e)}")


async def process_directory_upload(
    directory_path: str,
    collection: str,
    recursive: bool,
    file_extensions: Optional[List[str]]
):
    """处理目录上传（后台任务）"""
    try:
        _, _, knowledge_manager = get_rag_components()
        result = knowledge_manager.load_from_directory(
            directory_path,
            collection,
            recursive,
            file_extensions
        )

        logger.info(f"Directory processing completed: {directory_path}, loaded: {result.get('loaded_files', 0)} files")

    except Exception as e:
        logger.error(f"Background directory processing failed for {directory_path}: {str(e)}")


# 健康检查端点
@router.get("/health")
async def rag_health_check():
    """RAG模块健康检查"""
    try:
        vector_store, rag_retriever, knowledge_manager = get_rag_components()

        health_status = {
            "status": "healthy",
            "components": {
                "vector_store": "available",
                "rag_retriever": "available" if rag_retriever else "unavailable",
                "knowledge_manager": "available"
            },
            "collections": knowledge_manager.list_collections()
        }

        return JSONResponse(status_code=200, content=health_status)

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )
