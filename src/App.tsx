import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { FiSend, FiUpload, FiX } from 'react-icons/fi';
import axios from 'axios';
import { renderAsync } from 'docx-preview';
import ErrorBoundary from './ErrorBoundary';

// 定义消息类型
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [filePath, setFilePath] = useState<string>(''); // 新增状态用于存储文件路径
  const [progress, setProgress] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 获取标题
  const fetchTitle = async () => {
    try {
      const response = await axios.get('/api/title');
      setTitle(response.data.title);
    } catch (error) {
      console.error('获取标题失败:', error);
      setTitle('文档分析系统');
    }
  };

  useEffect(() => {
    fetchTitle();
  }, []);

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 模拟发送消息和接收回复
  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // 模拟AI回复
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '我正在分析您的文档，请稍候...',
        sender: 'bot',
      };
      setMessages((prev) => [...prev, botMessage]);

      // 模拟进度更新
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        currentProgress += 10;
        setProgress(currentProgress);
        if (currentProgress >= 100) {
          clearInterval(progressInterval);
          setTimeout(() => setProgress(0), 1000);
        }
      }, 500);
    }, 1000);
  };

  // 处理文件上传
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setShowPreview(true);

      // 创建FormData对象用于文件上传
      const formData = new FormData();
      formData.append('file', selectedFile);

      // 设置上传进度初始值
      setProgress(0);

      // 使用axios上传文件到后端API
      axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          // 计算并更新上传进度
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || progressEvent.loaded)
          );
          setProgress(percentCompleted);
        },
      })
        .then((response) => {
          // 上传成功后显示消息
          const botMessage: Message = {
            id: Date.now().toString(),
            content: `文件 "${selectedFile.name}" 已上传成功，文件路径: ${response.data.path}`,
            sender: 'bot',
          };
          setMessages((prev) => [...prev, botMessage]);

          // 保存文件路径用于预览
          setFilePath(response.data.path); // 使用新状态存储文件路径
        })
        .catch((error) => {
          // 处理上传错误
          console.error('文件上传失败:', error);
          const errorMessage: Message = {
            id: Date.now().toString(),
            content: `文件上传失败: ${error.response?.data?.error || '服务器错误'}`,
            sender: 'bot',
          };
          setMessages((prev) => [...prev, errorMessage]);
          setProgress(0);
        });
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const closePreview = () => {
    setShowPreview(false);
    setFile(null);
  };

  // 文件预览逻辑
  useEffect(() => {
    if (showPreview && file && filePath) {
      const previewContainer = document.getElementById('docx-preview');
      if (previewContainer) {
        fetch(`http://localhost:5000${filePath}`)
          .then((response) => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.blob();
          })
          .then((blob) => {
            renderAsync(blob, previewContainer, previewContainer, {
              className: 'docx-preview',
              inWrapper: true,
              useBase64URL: true,
            }).catch((error) => {
              console.error('渲染失败:', error);
              setMessages((prev) => [
                ...prev,
                {
                  id: Date.now().toString(),
                  content: '文档预览失败：' + error.message,
                  sender: 'bot',
                },
              ]);
              setShowPreview(false);
            });
          })
          .catch((error) => {
            console.error('文件加载失败:', error);
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                content: `文件加载失败：${error.message}`,
                sender: 'bot',
              },
            ]);
            setShowPreview(false);
          });
      }
    }
  }, [showPreview, file, filePath]); // 依赖文件和文件路径

  return (
    <AppContainer>
      <LeftPanel>
        <Header>
          <LogoContainer>
            <Logo onClick={() => window.location.href = '/'}>
              <LogoIcon>📄</LogoIcon>
            </Logo>
            <LogoText>FkdF</LogoText>
          </LogoContainer>
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: '100%', opacity: 1 }}
            transition={{ duration: 1.5, ease: 'easeInOut' }}
          >
            <Title>{title}</Title>
          </motion.div>
        </Header>
        
        <ChatContainer>
          <MessagesContainer>
            {messages.map((message) => (
              <MessageWrapper key={message.id} sender={message.sender}>
                <AnimatePresence>
                  <Message sender={message.sender}>
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.5 }}
                    >
                      {message.sender === 'bot' ? (
                        <TypewriterText text={message.content} />
                      ) : (
                        message.content
                      )}
                    </motion.div>
                  </Message>
                </AnimatePresence>
              </MessageWrapper>
            ))}
            <div ref={messagesEndRef} />
          </MessagesContainer>
          
          <InputContainer>
            <UploadButton onClick={triggerFileInput}>
              <FiUpload />
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                accept=".docx"
              />
            </UploadButton>
            <InputField
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入您的问题..."
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <SendButton onClick={handleSendMessage}>
              <FiSend />
            </SendButton>
          </InputContainer>
        </ChatContainer>
      </LeftPanel>
      
      <RightPanel>
        {showPreview ? (
          <PreviewContainer>
            <PreviewHeader>
              <PreviewTitle>{file?.name || '文档预览'}</PreviewTitle>
              <CloseButton onClick={closePreview}>
                <FiX />
              </CloseButton>
            </PreviewHeader>
            <PreviewContent>
              {file ? (
                file.name.endsWith('.docx') ? (
                  <ErrorBoundary
                    fallback={<div style={{ padding: '20px', color: 'red' }}>文件预览出错，请重试</div>}
                  >
                    <div id="docx-preview" style={{ width: '100%', height: '100%', overflow: 'auto' }} />
                  </ErrorBoundary>
                ) : (
                  <div>不支持的文件类型</div>
                )
              ) : (
                <PreviewPlaceholder>
                  文档预览区域
                  {file && (file as File).name && <div>文件名: {(file as File).name}</div>}
                </PreviewPlaceholder>
              )}
            </PreviewContent>
            <ProgressContainer>
              <ProgressBar progress={progress} />
              <ProgressText>{progress}% 完成</ProgressText>
            </ProgressContainer>
          </PreviewContainer>
        ) : (
          <EmptyPreview>
            <p>请上传DOCX文件以查看预览</p>
          </EmptyPreview>
        )}
      </RightPanel>
    </AppContainer>
  );
};

// 打字机效果组件
const TypewriterText: React.FC<{ text: string }> = ({ text }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, 30); // 调整速度

      return () => clearTimeout(timeout);
    }
  }, [currentIndex, text]);

  useEffect(() => {
    setDisplayedText('');
    setCurrentIndex(0);
  }, [text]);

  return <>{displayedText}</>;
};

// 样式组件
const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
  font-family: 'Arial', sans-serif;
`;

const LeftPanel = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background-color: white;
`;

const RightPanel = styled.div`
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #ffffff;
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  margin-right: 20px;
`;

const Logo = styled.div`
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background-color: #4a6cf7;
  color: white;
  cursor: pointer;
  margin-right: 10px;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #3a5ce5;
  }
`;

const LogoIcon = styled.span`
  font-size: 20px;
`;

const LogoText = styled.h1`
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  font-family: 'Times New Roman', serif;
  color: #333;
`;

const Title = styled.h2`
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const MessageWrapper = styled.div<{ sender: 'user' | 'bot' }>`
  display: flex;
  justify-content: ${props => props.sender === 'user' ? 'flex-end' : 'flex-start'};
  margin-bottom: 10px;
`;

const Message = styled.div<{ sender: 'user' | 'bot' }>`
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  background-color: ${props => props.sender === 'user' ? '#4a6cf7' : '#f0f2f5'};
  color: ${props => props.sender === 'user' ? 'white' : '#333'};
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

const InputContainer = styled.div`
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  background-color: white;
`;

const InputField = styled.input`
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: #4a6cf7;
  }
`;

const SendButton = styled.button`
  width: 40px;
  height: 40px;
  margin-left: 10px;
  border: none;
  border-radius: 50%;
  background-color: #4a6cf7;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #3a5ce5;
  }
`;

const UploadButton = styled.button`
  width: 40px;
  height: 40px;
  margin-right: 10px;
  border: none;
  border-radius: 50%;
  background-color: #f0f2f5;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #e0e0e0;
  }
`;

const PreviewContainer = styled.div`
  flex: 1;
  background-color: #f0f2f5;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

const PreviewHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
`;

const PreviewTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  border-radius: 50%;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #f0f2f5;
  }
`;

const PreviewContent = styled.div`
  flex: 1;
  padding: 20px;
  overflow: auto;
  background-color: white;
`;

const PreviewPlaceholder = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
`;

const ProgressContainer = styled.div`
  padding: 10px 20px;
  background-color: #ffffff;
  border-top: 1px solid #e0e0e0;
`;

const ProgressBar = styled.div<{ progress: number }>`
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
  position: relative;
  
  &:after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: ${props => props.progress}%;
    background-color: #4a6cf7;
    border-radius: 4px;
    transition: width 0.3s ease;
  }
`;

const ProgressText = styled.div`
  font-size: 12px;
  color: #666;
  text-align: right;
`;

const EmptyPreview = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  border-radius: 12px;
  color: #666;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

export default App;