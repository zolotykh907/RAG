import React, { useState } from 'react';

function Slider() {
    const [value, setValue] = useState(50); // Начальное значение 50

    const handleChange = (event) => {
    setValue(event.target.value);
    };

    return (
    <div>
        <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={handleChange}
        />
        <p>Текущее значение: {value}</p>
    </div>
    );
}
export default Slider;
