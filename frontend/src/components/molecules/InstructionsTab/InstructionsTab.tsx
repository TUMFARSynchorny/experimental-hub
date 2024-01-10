import { instructionsList } from "../../../utils/constants";

export const InstructionsTab = () => {
  return (
    <div className="flex flex-col p-4 border-l-gray-100 border-l-2 h-[calc(100vh-4rem)] w-full items-center gap-y-5">
      <div className="text-3xl">Instructions</div>
      <div className="w-full flex flex-col h-full items-start space-y-6">
        {/* // getting a common set of instructions for the participant from constants.js */}
        <p>
          <b>TASK:</b> please take your time to discuss and rank the following items with your
          partner. Once complete, have one of you send the final ranking in the chat.
        </p>
        {instructionsList.map((instruction, index) => {
          return <div key={index}>{`- ${instruction}`}</div>;
        })}
      </div>
    </div>
  );
};
