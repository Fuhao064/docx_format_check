import sys
import os

# 添加父级目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的函数
from backend.utils.utils import is_value_equal, extract_number

# 测试 is_value_equal 函数
def test_is_value_equal():
    # 测试字符串比较
    assert is_value_equal("center", "CENTER", "alignment") == True, "应该能够比较不同大小写"
    assert is_value_equal("2.5cm", "2.5", "margin") == True, "应该能够比较带单位的数值"
    
    # 测试数值比较
    assert is_value_equal(2.5, 2.51, "margin") == True, "应该允许小误差"
    assert is_value_equal("2.5", 2.5, "margin") == True, "应该能够比较字符串和数字"
    
    # 测试负面案例
    assert is_value_equal("center", "left", "alignment") == False, "不同值应该返回False"
    assert is_value_equal("3.0cm", 2.5, "margin") == False, "差异较大的值应该返回False"
    
    # 测试特殊情况 - 字号
    assert is_value_equal("16pt", 16, "size") == True, "字号应该能够比较带单位的值"
    assert is_value_equal(16, 16.4, "size") == True, "字号应该允许0.5pt的误差"
    assert is_value_equal(16, 16.6, "size") == False, "字号超过0.5pt的误差应该返回False"
    
    # 测试布尔值
    assert is_value_equal(True, "true", None) == True, "应该能够比较布尔值和字符串"
    assert is_value_equal(False, "false", None) == True, "应该能够比较布尔值和字符串"
    assert is_value_equal(True, False, None) == False, "不同的布尔值应该返回False"

# 测试 extract_number 函数
def test_extract_number():
    assert extract_number("2.5cm") == 2.5, "应该能够提取带单位的数值"
    assert extract_number("2.5") == 2.5, "应该能够提取不带单位的数值"
    assert extract_number(2.5) == 2.5, "应该能够处理数值类型"
    assert extract_number("-2.5") == -2.5, "应该能够处理负数"
    assert extract_number("no-number") is None, "无法提取数值时应该返回None"

if __name__ == "__main__":
    print("测试 is_value_equal 函数...")
    test_is_value_equal()
    print("is_value_equal 测试通过！")
    
    print("测试 extract_number 函数...")
    test_extract_number()
    print("extract_number 测试通过！")
    
    print("所有测试通过！")
