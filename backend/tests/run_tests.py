import unittest
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入测试模块
from test_agents import TestAgents
from test_api_endpoints import TestAPIEndpoints
from test_para_manager_exchange import TestParaManagerExchange
from test_format_fixer import TestFormatFixer

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestAgents))
    test_suite.addTest(unittest.makeSuite(TestFormatFixer))
    
    # 添加需要服务器运行的测试用例
    # 注意：这些测试需要服务器运行，如果服务器未运行，这些测试将失败
    if os.environ.get('RUN_SERVER_TESTS', 'False').lower() == 'true':
        test_suite.addTest(unittest.makeSuite(TestAPIEndpoints))
        test_suite.addTest(unittest.makeSuite(TestParaManagerExchange))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    # 检查是否运行服务器测试
    if len(sys.argv) > 1 and sys.argv[1] == '--with-server':
        os.environ['RUN_SERVER_TESTS'] = 'True'
    
    # 运行测试
    success = run_tests()
    
    # 设置退出码
    sys.exit(0 if success else 1)
