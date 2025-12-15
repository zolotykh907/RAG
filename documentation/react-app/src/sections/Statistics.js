import { useEffect, useState } from 'react';
import { getAllKPI } from '../utils/api';

const Statistics = () => {
  const [kpiData, setKpiData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchKPI = async () => {
      try {
        setLoading(true);
        const data = await getAllKPI();
        setKpiData(data);
        setError(null);
      } catch (err) {
        setError('Ошибка загрузки данных статистики');
        console.error('Error fetching KPI:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchKPI();

    const interval = setInterval(fetchKPI, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}ч ${minutes}м ${secs}с`;
    } else if (minutes > 0) {
      return `${minutes}м ${secs}с`;
    } else {
      return `${secs}с`;
    }
  };

  if (loading) {
    return (
      <section className="fade-in">
        <h2>Статистика посещений</h2>
        <p>Загрузка данных...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="fade-in">
        <h2>Статистика посещений</h2>
        <p style={{ color: 'red' }}>{error}</p>
      </section>
    );
  }

  return (
    <section className="fade-in">
      <h2>Статистика посещений</h2>
      <p>Данные о посещениях и времени, проведенном на каждой странице документации.</p>

      {kpiData.length === 0 ? (
        <p>Нет данных для отображения. Создайте страницы через API.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название страницы</th>
              <th>URL</th>
              <th>Количество посещений</th>
              <th>Общее время на странице</th>
            </tr>
          </thead>
          <tbody>
            {kpiData.map((page) => (
              <tr key={page.id}>
                <td>{page.id}</td>
                <td>{page.name}</td>
                <td><span className="inline-code">{page.url}</span></td>
                <td style={{ textAlign: 'center', fontWeight: 'bold' }}>{page.kpi.visits}</td>
                <td style={{ textAlign: 'center' }}>{formatTime(page.kpi.total_time_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="highlight" style={{ marginTop: '20px' }}>
        <h4>ℹ️ Информация</h4>
        <ul>
          <li className="highlight-li">Данные обновляются автоматически каждые 5 секунд</li>
          <li className="highlight-li">Счетчик посещений увеличивается при каждом заходе на страницу</li>
          <li className="highlight-li">Время учитывается с момента открытия страницы до перехода на другую или закрытия вкладки</li>
        </ul>
      </div>
    </section>
  );
};

export default Statistics;
