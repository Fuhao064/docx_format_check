import docx
import zipfile
import os
import tempfile
import base64
import io
from PIL import Image
from backend.preparation.para_type import ParagraphManager, ParsedParaType

def extract_images_from_docx(doc_path):
    """从docx文件中提取图片信息"""
    images = []
    try:
        # 打开docx文件（实际上是一个zip文件）
        with zipfile.ZipFile(doc_path, 'r') as docx_zip:
            # 提取所有图片文件
            for item in docx_zip.namelist():
                if item.startswith('word/media/'):
                    # 提取图片数据
                    image_data = docx_zip.read(item)
                    image_name = os.path.basename(item)

                    # 创建临时目录来存储提取的图片
                    temp_dir = tempfile.mkdtemp()
                    image_path = os.path.join(temp_dir, image_name)

                    # 保存图片到临时目录
                    with open(image_path, 'wb') as f:
                        f.write(image_data)

                    # 获取图片尺寸
                    try:
                        with Image.open(io.BytesIO(image_data)) as img:
                            width, height = img.size
                            # 转换为英寸
                            width_inches = width / 96  # 假设96dpi
                    except Exception as e:
                        print(f"无法获取图片尺寸: {str(e)}")
                        width_inches = 6  # 默认宽度
                        height = 0

                    # 将图片数据转换为base64编码
                    binary_data = base64.b64encode(image_data).decode('utf-8')

                    # 将图片信息添加到列表中
                    images.append({
                        'name': image_name,
                        'path': image_path,
                        'width': width_inches,
                        'height': height,
                        'binary_data': binary_data
                    })

            print(f"从文档中提取了 {len(images)} 个图片")
    except Exception as e:
        print(f"提取图片时出错: {str(e)}")

    return images

def extract_tables_from_docx(doc_path):
    """从docx文件中提取表格信息"""
    tables = []
    try:
        doc = docx.Document(doc_path)

        # 遍历所有表格
        for i, table in enumerate(doc.tables):
            # 提取表格数据
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text)
                table_data.append(row_data)

            # 获取表格样式
            table_style = 'Table Grid'  # 默认样式
            if hasattr(table, 'style') and table.style:
                table_style = table.style.name

            # 提取合并单元格信息
            merged_cells = []
            # 注意：python-docx不直接支持提取合并单元格信息
            # 这里只是一个占位符，实际实现可能需要更复杂的逻辑

            # 将表格信息添加到列表中
            tables.append({
                'position': i,
                'data': table_data,
                'style': table_style,
                'merged_cells': merged_cells,
                'caption': f"表格 {i+1}",  # 默认题注
                'table_number': i+1
            })

        print(f"从文档中提取了 {len(tables)} 个表格")
    except Exception as e:
        print(f"提取表格时出错: {str(e)}")

    return tables

def add_media_to_manager(manager: ParagraphManager, doc_path: str):
    """将图片和表格添加到段落管理器中"""
    # 提取图片信息
    images = extract_images_from_docx(doc_path)

    # 提取表格信息
    tables = extract_tables_from_docx(doc_path)

    # 将图片添加到段落管理器中
    for i, image in enumerate(images):
        # 创建图片段落的元数据
        meta_data = {
            'image_path': image['path'],
            'width': image['width'],
            'binary_data': image['binary_data'],
            'figure_number': i + 1
        }

        # 添加图片段落到段落管理器
        try:
            # 确保使用正确的枚举类型
            figures_type = ParsedParaType.FIGURES
            if not isinstance(figures_type, ParsedParaType):
                print(f"警告：FIGURES类型不是ParsedParaType枚举，将尝试重新获取")
                # 尝试重新获取枚举值
                for enum_type in ParsedParaType:
                    if enum_type.value == 'figures':
                        figures_type = enum_type
                        break

            manager.add_para(
                para_type=figures_type,
                content=f"图片 {i+1}",  # 默认题注
                meta=meta_data
            )
        except Exception as e:
            print(f"添加图片段落到管理器时出错: {str(e)}")
            # 尝试使用OTHERS类型作为备选
            try:
                manager.add_para(
                    para_type=ParsedParaType.OTHERS,
                    content=f"图片 {i+1}",  # 默认题注
                    meta=meta_data
                )
                print(f"使用OTHERS类型添加图片段落成功")
            except Exception as e2:
                print(f"使用OTHERS类型添加图片段落也失败: {str(e2)}")

    # 将表格添加到段落管理器中
    for i, table in enumerate(tables):
        # 创建表格段落的元数据
        meta_data = {
            'table_data': table['data'],
            'table_number': i + 1,
            'style': table['style'],
            'merged_cells': table['merged_cells']
        }

        # 添加表格段落到段落管理器
        try:
            # 确保使用正确的枚举类型
            tables_type = ParsedParaType.TABLES
            if not isinstance(tables_type, ParsedParaType):
                print(f"警告：TABLES类型不是ParsedParaType枚举，将尝试重新获取")
                # 尝试重新获取枚举值
                for enum_type in ParsedParaType:
                    if enum_type.value == 'tables':
                        tables_type = enum_type
                        break

            manager.add_para(
                para_type=tables_type,
                content=f"表格 {i+1}",  # 默认题注
                meta=meta_data
            )
        except Exception as e:
            print(f"添加表格段落到管理器时出错: {str(e)}")
            # 尝试使用OTHERS类型作为备选
            try:
                manager.add_para(
                    para_type=ParsedParaType.OTHERS,
                    content=f"表格 {i+1}",  # 默认题注
                    meta=meta_data
                )
                print(f"使用OTHERS类型添加表格段落成功")
            except Exception as e2:
                print(f"使用OTHERS类型添加表格段落也失败: {str(e2)}")

    return manager
