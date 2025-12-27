import FileUpload from '../components/FileUpload';
import InfoPopup from '../components/InfoPopup';
import apiService from '../services/api';
import './UploadPage.css';

function UploadPage() {
  const handlePermanentUpload = async (file) => {
    return await apiService.uploadFile(file);
  };

  const handleClearIndex = async () => {
    if (window.confirm('Вы уверены, что хотите удалить все индексированные документы? Это действие нельзя отменить.')) {
      try {
        await apiService.clearIndex();
        alert('Все документы успешно удалены');
      } catch (error) {
        alert(`Ошибка при удалении документов: ${error.message}`);
      }
    }
  };

  return (
    <div className="upload-section">
      <div className="upload-section-content">
        <div className="section-header">
          <div className="header-with-help">
            <h2>Загрузка документов</h2>
            <InfoPopup title="Режимы работы с документами">
              <div className="upload-modes">
                <div className="mode-item">
                  <strong>Временная загрузка:</strong>
                  <ul>
                    <li>Документ доступен только в текущей сессии чата</li>
                    <li>Идеально для разовых вопросов по одному документу</li>
                    <li>Загружается прямо в чате с помощью кнопки прикрепления файла</li>
                    <li>Автоматически удаляется при создании нового чата</li>
                    <li>Не занимает место в общей базе данных</li>
                  </ul>
                </div>
                <div className="mode-item">
                  <strong>Постоянная индексация:</strong>
                  <ul>
                    <li>Документы доступны всем пользователям системы</li>
                    <li>Хранятся в базе данных постоянно</li>
                    <li>Можно задавать вопросы по нескольким документам одновременно</li>
                    <li>Поддерживается поиск по содержимому всех документов</li>
                    <li>Загружаются на этой странице</li>
                  </ul>
                </div>
              </div>
            </InfoPopup>
          </div>
          <p>Добавьте документы в постоянное хранилище для совместного использования</p>
        </div>

        <FileUpload
          onPermanentUpload={handlePermanentUpload}
        />

        <button
          onClick={handleClearIndex}
          className="clear-index-btn"
        >
          Очистить базу
        </button>
      </div>
    </div>
  );
}

export default UploadPage;
