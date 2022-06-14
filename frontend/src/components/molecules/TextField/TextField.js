import "./TextField.css";
import Label from "../../atoms/Label/Label";

function TextField({ title, value, onChange, placeholder, required }) {
  return (
    <div className="textAreaContainer">
      <Label title={title} />
      <textarea
        className="textAreaField"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
      ></textarea>
    </div>
  );
}

export default TextField;
