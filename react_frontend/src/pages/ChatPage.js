import ChatInterface from '../components/ChatInterface';
import apiService from '../services/api';

function ChatPage({ sessionId, setSessionId }) {
  const ensureSession = (historyTitle = 'Новый чат') => {
    if (!sessionId) {
      const newId = crypto.randomUUID();
      setSessionId(newId);
      if (window.chatHistory) {
        window.chatHistory.saveChat(newId, historyTitle);
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
    const sid = ensureSession(file.name);
    const result = await apiService.uploadTempFile(file, sid);

    if (result.session_id !== sid) {
      setSessionId(result.session_id);
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
