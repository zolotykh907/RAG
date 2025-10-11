function Slider({ value, onChange, min = 0, max = 100 }) {
  const handleChange = (e) => {
    onChange(Number(e.target.value));
  };

  const increment = () => {
    if (value < max) onChange(value + 1);
  };

  const decrement = () => {
    if (value > min) onChange(value - 1);
  };

  return (
    <div className="slider-container">
      <button onClick={decrement}>−</button>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={handleChange}
        className="slider"
      />
      <button onClick={increment}>+</button>
    </div>
  );
}

export default Slider;
