import React, { useState } from 'react';
import axios from 'axios';

const Flip = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;

    if (!selected.type.startsWith('image/')) {
      setError('Выберите изображение');
      return;
    }

    setFile(selected);
    setError('');

    const reader = new FileReader();
    reader.onload = (event) => setPreview(event.target.result);
    reader.readAsDataURL(selected);
  };

  const handleFlip = async () => {
    if (!file) {
      setError('Сначала выберите изображение');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('http://localhost:8000/flip', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const imageUrl = URL.createObjectURL(blob);
      setResult(imageUrl);
    } catch (err) {
      setError('Ошибка: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id='flip' className='fade-in'>
      <h2>Переворот изображения</h2>

      <div className="flip-controls">
        <input type="file" accept="image/*" id="fileInput" onChange={handleFileChange} hidden />
        <label htmlFor="fileInput" className="method-btn">
          {file ? 'Выбрать другое изображение' : 'Выбрать изображение'}
        </label>

        {file && (
          <button onClick={handleFlip} disabled={loading} className="method-btn">
            {loading ? 'Обработка...' : 'Перевернуть'}
          </button>
        )}
      </div>

      {error && <p className="flip-error">{error}</p>}

      <div className="flip-images">
        {preview && (
          <div className="flip-image-block">
            <h3>До</h3>
            <img src={preview} alt="original" className="flip-image" />
          </div>
        )}
        {result && (
          <div className="flip-image-block">
            <h3>После</h3>
            <img src={result} alt="flipped" className="flip-image" />
          </div>
        )}
      </div>
    </section>
  );
};

export default Flip;