import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUndo,
  faRedo,
  faCommentAlt,
  faClipboardCheck,
  faUsers
} from "@fortawesome/free-solid-svg-icons";

const buttonConfigs = {
  // not only icons but general buttons with different looks etc.
  undoRedoButtonList: [faUndo, faRedo],
  experimenterButtonList: [faCommentAlt, faClipboardCheck, faUsers],
  participantButtonList: [faCommentAlt, faClipboardCheck]
};

const ButtonList = ({ type }) => {
  const buttons = buttonConfigs[type] || [];

  return (
    <div className="button-list flex gap-2">
      {buttons.map((icon, index) => (
        <button
          key={index}
          className="w-12 h-9 px-4 py-2 bg-neutral-200 rounded-2xl border border-neutral-200 flex justify-center items-center"
        >
          <FontAwesomeIcon icon={icon} className="w-4 h-4" />
        </button>
      ))}
    </div>
  );
};

export default ButtonList;
