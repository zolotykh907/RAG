function Slider({ value, onChange, min = 0, max = 100 }) {
  return (
  <div className="slider-container">
    <button onClick={() => value > min && onChange(value - 1)}>−</button>
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="slider"
    />
    <button onClick={() => value < max && onChange(value + 1)}>+</button>
  </div>
);

}

export default Slider;
