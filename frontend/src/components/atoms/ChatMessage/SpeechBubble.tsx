import moment from "moment";

type Props = {
  author: string;
  target: string;
  message: string;
  date: number;
  currentUser: string;
  color?: string;
};
export const SpeechBubble = (props: Props) => {
  const { author, target, message, date, currentUser, color } = props;
  const shouldApplySelfEnd = (): boolean => {
    if (author === "experimenter" && currentUser === "experimenter") {
      return false;
    } else if (author === "experimenter" && currentUser !== "experimenter") {
      return true;
    } else return author !== "experimenter" && currentUser === "experimenter";
  };
  return (
    <div className="flex flex-col">
      <div
        className={`${
          shouldApplySelfEnd() ? "self-end" : "self-start"
        } text-[0.65rem] max-w-full`}
      >
        {moment(date).format("lll")}
      </div>
      <div
        className={`${
          shouldApplySelfEnd()
            ? "self-end bg-stone-200"
            : `self-start ${color ? color : "bg-blue-600"} text-white`
        } px-2 py-1 rounded break-words max-w-full text-start`}
      >
        {message}
      </div>
    </div>
  );
};
