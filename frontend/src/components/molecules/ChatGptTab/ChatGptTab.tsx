import { RefObject, useRef, useState } from "react";
import OpenAI from "openai";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane, faUpRightAndDownLeftFromCenter } from "@fortawesome/free-solid-svg-icons";
import { Button, Progress } from "@nextui-org/react";
import useAutosizeTextArea from "../../../hooks/useAutosizeTextArea";
import { ChatGptSpeechBubble } from "../../atoms/ChatMessage/ChatGptSpeechBubble";
import { ChatGptMessage } from "../../../types";
import { ChatGptModal } from "./ChatGptModal";
import { initialSnackbar } from "../../../utils/constants";
import CustomSnackbar from "../../atoms/CustomSnackbar/CustomSnackbar";

const initialMessage: ChatGptMessage = {
  content: "Hello, I'm ChatGPT! Ask me anything!",
  role: "assistant"
};

export const ChatGptTab = () => {
  const openai = new OpenAI({
    apiKey: import.meta.env.VITE_CHAT_GPT_API_KEY,
    dangerouslyAllowBrowser: true
  });
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const [isTyping, setIsTyping] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [messageHistory, setMessageHistory] = useState<Array<ChatGptMessage>>([initialMessage]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  useAutosizeTextArea(textAreaRef.current, message);

  const scrollToBottom = (ref: RefObject<any>) => {
    ref.current.scrollIntoView({ behavior: "smooth" });
  };

  const sendMsgToChatGpt = async (message: string, refElement?: RefObject<any>) => {
    setMessageHistory((prevHistory) => [...prevHistory, { role: "user", content: message }]);
    setMessage("");

    const params: OpenAI.Chat.ChatCompletionCreateParams = {
      messages: [...messageHistory, { role: "user", content: message }],
      model: "gpt-3.5-turbo"
    };
    setIsTyping(true);
    try {
      const response = await openai.chat.completions.create(params);
      setIsTyping(false);
      setMessageHistory((prevHistory) => [...prevHistory, response.choices[0].message]);
      setTimeout(() => {
        scrollToBottom(refElement ? refElement : messagesEndRef);
      }, 100);
    } catch (error) {
      //TODO: more detailed error-handling
      console.log(error);
      setSnackbar({
        open: true,
        text: `Given ChatGPT API key is invalid. Please check for the validity of your API key.`,
        severity: "error"
      });
    }
  };

  const onEnterPressed = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMsgToChatGpt(message);
    }
  };

  const handleModal = () => {
    setIsModalOpen(!isModalOpen);
  };

  return (
    <div className="flex flex-col border-l-gray-200 border-l-2 h-full w-full items-center">
      {(!openai.apiKey || openai.apiKey === "ADD_YOUR_API_KEY_HERE") && (
        <>
          <div className="flex flex-row items-center justify-between border-b-2 border-b-gray-200 w-full py-4 px-6 gap-y-2">
            <h3 className="text-3xl">No ChatGPT API Key detected.</h3>
          </div>
          <div className="py-4 px-6">
            Service disabled. For more information on how to add your ChatGPT key and the ChatGPT
            features, please read{" "}
            <a
              className="text-blue-600"
              href="https://github.com/TUMFARSynchrony/experimental-hub/wiki/ChatGPT"
              target="blank"
            >
              this entry on our Wiki
            </a>
            .
          </div>
        </>
      )}
      {openai.apiKey && openai.apiKey != "ADD_YOUR_API_KEY_HERE" && isModalOpen && (
        <ChatGptModal
          sendMsgToChatGpt={sendMsgToChatGpt}
          messageHistory={messageHistory}
          onEnterPressed={onEnterPressed}
          isTyping={isTyping}
          isModalOpen={isModalOpen}
          onOpenChange={handleModal}
        />
      )}
      {openai.apiKey && openai.apiKey != "ADD_YOUR_API_KEY_HERE" && (
        <>
          <div className="flex flex-row items-center justify-between border-b-2 border-b-gray-200 w-full py-4 px-6 gap-y-2">
            <h3 className="text-3xl">ChatGPT</h3>
            <Button className="rounded-md" onClick={() => handleModal()} size="sm">
              <FontAwesomeIcon icon={faUpRightAndDownLeftFromCenter} />
            </Button>
          </div>
          <div className="w-full flex flex-col justify-between overflow-y-auto h-full">
            <div className="p-4 overflow-y-auto">
              {messageHistory.map((message, index) => (
                <div className="py-2" key={index}>
                  <ChatGptSpeechBubble role={message.role} content={message.content} />
                </div>
              ))}
              {isTyping && (
                <Progress
                  size="sm"
                  isIndeterminate
                  aria-label="Loading..."
                  className="max-w-md py-4"
                />
              )}
              <div ref={messagesEndRef}></div>
            </div>
            <div className="flex flex-col p-4 py-8">
              <div className="flex flex-row justify-between gap-x-2 items-center">
                <textarea
                  className="resize-none border-2 border-stone-300 p-2 py-2 h-full w-full rounded outline-none text-sm"
                  placeholder="Enter your message here"
                  value={message}
                  ref={textAreaRef}
                  rows={1}
                  onChange={(event) => setMessage(event.target.value)}
                  onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                    onEnterPressed(event);
                  }}
                />
                <Button
                  className="h-8 rounded-sm"
                  color="primary"
                  size="md"
                  isIconOnly={true}
                  onClick={() => sendMsgToChatGpt(message)}
                >
                  <FontAwesomeIcon icon={faPaperPlane} style={{ color: "#ffffff" }} />{" "}
                </Button>
              </div>
            </div>
          </div>
          <CustomSnackbar
            open={snackbar.open}
            text={snackbar.text}
            severity={snackbar.severity}
            handleClose={() => setSnackbar(initialSnackbar)}
            autoHideDuration={snackbar.autoHideDuration}
            anchorOrigin={snackbar.anchorOrigin}
          />
        </>
      )}
    </div>
  );
};
