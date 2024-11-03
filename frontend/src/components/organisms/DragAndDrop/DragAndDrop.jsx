import { useState } from "react";
import { Layer, Stage, Text } from "react-konva";
import { useAppDispatch } from "../../../redux/hooks";
import { changeParticipantDimensions } from "../../../redux/slices/openSessionSlice";
import Rectangle from "../../atoms/Rectangle/Rectangle";
import { CANVAS_SIZE } from "../../../utils/constants";

function DragAndDrop({ participantDimensions, setParticipantDimensions, asymmetricView }) {
  const [selectedShape, setSelectShape] = useState(null);

  const dispatch = useAppDispatch();

  const checkDeselect = (e) => {
    const clickedOnEmpty = e.target === e.target.getStage();
    if (clickedOnEmpty) {
      setSelectShape(null);
    }
  };
  return (
    <div className="w-full h-full">
      <Stage
        className="flex items-center justify-center bg-slate-200 rounded-md shadow-lg"
        width={CANVAS_SIZE.width}
        height={CANVAS_SIZE.height}
        onMouseDown={checkDeselect}
      >
        <Layer>
          {participantDimensions.length > 0 ? (
            participantDimensions.map((rect, index) => {
              return (
                <Rectangle
                  key={index}
                  shapeProps={rect.shapes}
                  groupProps={rect.groups}
                  isSelected={index === selectedShape}
                  onSelect={() => {
                    setSelectShape(index);
                  }}
                  onChange={(newAttrs) => {
                    const dimensions = participantDimensions.slice();
                    dimensions[index].groups = newAttrs;
                    setParticipantDimensions(dimensions);

                    if (!asymmetricView) {
                      dispatch(
                        changeParticipantDimensions({
                          index: index,
                          position: {
                            x: newAttrs.x,
                            y: newAttrs.y,
                            z: 0
                          },
                          size: {
                            width: newAttrs.width,
                            height: newAttrs.height
                          }
                        })
                      );
                    }
                  }}
                />
              );
            })
          ) : (
            <div className="w-full h-full">
              <Text
                text="There are no participants in this session yet."
                fontSize={20}
                align={"center"}
                verticalAlign={"middle"}
                width={CANVAS_SIZE.width}
                height={CANVAS_SIZE.height}
              />
            </div>
          )}
        </Layer>
      </Stage>
    </div>
  );
}

export default DragAndDrop;
