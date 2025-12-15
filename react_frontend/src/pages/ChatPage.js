import ChatInterface from '../components/ChatInterface';
import apiService from '../services/api';

function ChatPage({ sessionId, setSessionId }) {
  const handleSendMessage = async (question) => {
    return await apiService.sendQuery(question, sessionId);
  };

  const handleTempUpload = async (file) => {
    const result = await apiService.uploadTempFile(file);
    setSessionId(result.session_id);

    if (window.chatHistory) {
      window.chatHistory.saveChat(result.session_id, file.name);
    }

    return result;
  };

  return (
    <ChatInterface
      onSendMessage={handleSendMessage}
      sessionId={sessionId}
      onFileUpload={handleTempUpload}
    />
  );
}

export default ChatPage;
