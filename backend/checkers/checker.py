from backend.preparation.para_type import ParagraphManager, ParsedParaType, ParaInfo
from backend.preparation.docx_parser import extract_section_info

def check_abstract(paragraph_manager:ParagraphManager):
    """检查摘要格式"""
    errors = []

    # 查找摘要段落
    abstract_paras = []
    abstract_content_paras = []

    for para in paragraph_manager.paragraphs:
        if para.type == ParsedParaType.ABSTRACT_ZH or para.content.strip().startswith('摘要'):
            abstract_paras.append(para)
        elif para.type == ParsedParaType.ABSTRACT_CONTENT_ZH:
            abstract_content_paras.append(para)

    # 检查是否存在摘要
    if not abstract_paras:
        errors.append({
            'message': '文档中缺少摘要',
            'location': '文档开头部分'
        })
        return errors

    # 检查是否有摘要内容
    if not abstract_content_paras:
        errors.append({
            'message': '文档中缺少摘要内容',
            'location': '摘要标题后'
        })
        return errors

    # 检查摘要内容长度
    for content_para in abstract_content_paras:
        abstract_text = content_para.content.strip()
        if len(abstract_text) < 10:  # 假设摘要至少应该有10个字符
            errors.append({
                'message': '摘要内容过短',
                'location': '摘要部分'
            })

    return errors

def check_keywords(paragraph_manager:ParagraphManager):
    """检查关键词格式"""
    errors = []

    # 查找关键词段落
    keyword_paras = []
    for para in paragraph_manager.paragraphs:
        para_text = para.content.strip()
        if para_text.startswith('关键词') or para_text.startswith('Keywords'):
            keyword_paras.append(para)

    # 检查是否存在关键词
    if not keyword_paras:
        errors.append({
            'message': '文档中缺少关键词',
            'location': '摘要之后'
        })
        return errors

    # 检查关键词内容
    keyword_para = keyword_paras[0]
    keyword_text = keyword_para.content.strip()

    # 检查是否有足够的关键词（假设至少3个）
    if '：' in keyword_text:
        keywords = keyword_text.split('：')[1].split('；')
    elif ':' in keyword_text:
        keywords = keyword_text.split(':')[1].split(';')
    else:
        keywords = []

    if len(keywords) < 3:
        errors.append({
            'message': '关键词数量不足，建议至少提供3个关键词',
            'location': '关键词部分'
        })

    return errors

def check_required_paragraphs(paragraph_manager:ParagraphManager, required_format:Dict) -> List[Dict]:
    """
    检查一定要求出现的段落是否出现

    参数:
    paragraph_manager: 段落管理器
    required_format: 格式要求

    返回:
    List[Dict]: 错误列表
    """
    errors = []

    required_types = required_format.get('required_paragraphs')

    # 检查每种必需的段落类型
    for type_key, type_name in required_types:
        if type_key in required_format:
            # 检查该类型是否存在于段落管理器中
            try:
                para_type = ParsedParaType(type_key)
                paras = paragraph_manager.get_by_type(para_type)
                if not paras:
                    errors.append({
                        "message": f"缺少{type_name}部分",
                        "location": "文档结构"
                    })
            except ValueError:
                # 如果段落类型无效，则跳过
                continue

    return errors

def _recursive_check(actual, expected):
    """
    递归检查嵌套字典的字段。
    返回格式为[(key, error_message), ...]的列表
    """
    errors = []

    for key, expected_value in expected.items():
        actual_value = actual.get(key)

        # 如果字段不存在
        if actual_value is None:
            errors.append((key, f"缺少必需字段: '{key}'"))
            continue

        # 如果字段是列表类型，优先检查长度
        if isinstance(actual_value, list):
            if len(actual_value) > 1:
                errors.append((key, f"字段 '{key}' 存在多个值: {actual_value}"))
                continue
            if len(actual_value) == 0:
                continue
            actual_value = actual_value[0]  # 取第一个值进行比较

        # 递归处理嵌套字典
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                errors.append((key, f"字段类型不匹配: '{key}' 应为字典类型，实际为 {type(actual_value).__name__}"))
                continue

            # 递归检查嵌套字段
            deeper_errors = _recursive_check(actual_value, expected_value)
            for err_key, err_msg in deeper_errors:
                errors.append((f"{key}.{err_key}", err_msg))

        # 检查值是否匹配
        else:
            if not is_value_equal(expected_value, actual_value, key=key):
                errors.append((key, f"'{key}' 不匹配: 要求 {expected_value}, 实际 {actual_value}"))

    return errors

def remark_para_type(doc_path: str, format_agent: FormatAgent) -> ParagraphManager:
    # 初始化段落管理器
    paragraph_manager = ParagraphManager()

    # 读取doc的段落信息
    paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)

    # 文档整个内容
    doc_content = docx_parser.extract_doc_content(doc_path)

    # 定义任务函数
    def process_paragraph(para_index: int, para: Dict, doc_content_sent: bool, manager: ParagraphManager):
        try:
            if para["type"] != ParsedParaType.BODY:
                pass
            # 提取当前段落信息
            para_string = para["content"]

            # 调用大模型预测类型
            response = format_agent.predict_location(doc_content, para_string, doc_content_sent)

            # 直接使用response字典，无需再次解析
            response_dict = response

            # 将返回的location转换为ParsedParaType枚举类型
            try:
                new_type = ParsedParaType(response_dict["location"])
                # 直接访问paragraphs列表中的对应索引
                manager.paragraphs[para_index].type = new_type
            except ValueError:
                print(f"Invalid paragraph type received: {response_dict['location']}")
                manager.paragraphs[para_index].type = ParsedParaType.BODY

        except Exception as e:
            # 如果解析失败，将段落类型设置为 BODY
            print(f"Error processing paragraph: {para_string[:50]}... Error: {e}")
            manager.paragraphs[para_index].type = ParsedParaType.BODY

    # 将段落json转为中文
    paras_info_json_zh = paragraph_manager.to_chinese_dict()

    # 使用线程池并发处理，限制最大线程数为10
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        doc_content_sent = False

        # 创建任务列表
        tasks = []
        for i, para in enumerate(paras_info_json_zh):
            tasks.append((i, para, doc_content_sent, paragraph_manager))
            doc_content_sent = True  # 更新全文标志

        # 分批提交任务，每批最多5个任务
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i+batch_size]
            batch_futures = [executor.submit(process_paragraph, *task) for task in batch_tasks]
            futures.extend(batch_futures)

            # 等待当前批次完成
            for future in concurrent.futures.as_completed(batch_futures):
                try:
                    future.result()  # 确保任务完成
                except Exception as e:
                    print(f"Error in thread pool task: {e}")

    return paragraph_manager

