import ChatInterface from '../components/ChatInterface';
import apiService from '../services/api';

function ChatPage({ sessionId, setSessionId }) {
  const ensureSession = () => {
    if (!sessionId) {
      const newId = crypto.randomUUID();
      setSessionId(newId);
      if (window.chatHistory) {
        window.chatHistory.saveChat(newId, 'Новый чат');
      }
      return newId;
    }
    return sessionId;
  };

  const handleSendMessage = async (question) => {
    const sid = ensureSession();
    return await apiService.sendQuery(question, sid);
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
