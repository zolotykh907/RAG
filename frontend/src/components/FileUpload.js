import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const FileUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setUploadResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    multiple: false
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('/upload-files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult({
        success: true,
        message: response.data.message || 'Файл успешно загружен и проиндексирован!'
      });
      setSelectedFile(null);
    } catch (error) {
      setUploadResult({
        success: false,
        message: error.response?.data?.error || 'Ошибка при загрузке файла'
      });
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setUploadResult(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Upload className="h-5 w-5 mr-2" />
          Загрузка и индексация файлов
        </h2>
        
        <p className="text-gray-600 mb-6">
          Загрузите документ для индексации в векторную базу данных. 
          Поддерживаются форматы: PDF, DOC, DOCX, TXT, JPG, PNG
        </p>

        {/* Область для перетаскивания файлов */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          {isDragActive ? (
            <p className="text-primary-600 font-medium">Отпустите файл здесь...</p>
          ) : (
            <div>
              <p className="text-gray-600 font-medium mb-2">
                Перетащите файл сюда или нажмите для выбора
              </p>
              <p className="text-sm text-gray-500">
                Поддерживаются PDF, DOC, DOCX, TXT, JPG, PNG
              </p>
            </div>
          )}
        </div>

        {/* Выбранный файл */}
        {selectedFile && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-gray-500" />
                <div>
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Неизвестный тип'}
                  </p>
                </div>
              </div>
              <button
                onClick={removeFile}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}

        {/* Кнопка загрузки */}
        {selectedFile && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary w-full mt-4 flex items-center justify-center space-x-2"
          >
            {uploading ? (
              <>
                <div className="loading-spinner"></div>
                <span>Индексация файла...</span>
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                <span>Загрузить и проиндексировать</span>
              </>
            )}
          </button>
        )}

        {/* Результат загрузки */}
        {uploadResult && (
          <div className={`mt-4 p-4 rounded-lg border ${
            uploadResult.success
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center space-x-2">
              {uploadResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" />
              )}
              <span className={`font-medium ${
                uploadResult.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {uploadResult.message}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload; 