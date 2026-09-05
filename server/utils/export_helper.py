"""导出工具：文章导出Word、标题导出Excel"""
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def export_article_to_word(article_id: int) -> str:
    """
    导出文章为Word文档
    实际应使用 python-docx 生成完整文档
    """
    os.makedirs("data/exports", exist_ok=True)
    filename = f"article_{article_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join("data/exports", filename)

    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        # 标题
        title = doc.add_heading(f"文章 #{article_id}", level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # 正文占位
        doc.add_paragraph("（文章正文内容）")
        doc.save(filepath)
        logger.info(f"文章已导出: {filepath}")
    except ImportError:
        # python-docx 未安装时创建空文件
        with open(filepath, "w") as f:
            f.write(f"Article #{article_id}\n\n(请安装 python-docx 以生成完整Word文档)")
        logger.warning("python-docx 未安装，已生成占位文件")

    return filepath
