import InputField from "../../atoms/InputField/InputField";
import Label from "../../atoms/Label/Label";
import "./InputTextField.css";

function InputTextField({
  title,
  value,
  placeholder,
  readonly,
  onChange,
  inputType,
  required,
  min
}: any) {
  return (
    <div className="inputFieldContainer">
      <Label title={title} />
      <InputField
        inputType={inputType}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        readonly={readonly}
        required={required}
        min={min}
      />
    </div>
  );
}

export default InputTextField;
