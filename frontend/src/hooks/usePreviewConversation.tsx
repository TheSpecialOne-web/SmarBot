import { useAuth0 } from "@auth0/auth0-react";
import readNDJSONStream from "ndjson-readablestream";
import { useRef, useState } from "react";

import {
  Approach,
  ConversationPreview,
  ModelFamily,
  PreviewConversationParam,
} from "@/orval/models/backend-api";
import { PreviewChatSession } from "@/types/chat";

import { useUserInfo } from "./useUserInfo";

export const usePreviewConversation = () => {
  // チャット開始からストリーム開始まで
  const [isLoading, setIsLoading] = useState(false);
  const [answers, setAnswers] = useState<PreviewChatSession[]>([]);
  // ストリーム開始からストリーム終了まで
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedAnswers, setStreamedAnswers] = useState<PreviewChatSession[]>([]);
  // チャット開始からストリーム終了まで
  const isChatActive = useRef<boolean>(false);
  const { userInfo } = useUserInfo();

  const { getAccessTokenSilently } = useAuth0();

  const createConversationRequest = async (
    options: PreviewConversationParam,
  ): Promise<Response> => {
    const basePath = import.meta.env.VITE_API_BASE_URL;
    const accessToken = await getAccessTokenSilently();
    return await fetch(`${basePath}/conversations/preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-Id": userInfo.tenant.id.toString() || "",
      },
      body: JSON.stringify(options),
    });
  };

  const handleChatStream = async (
    question: string,
    answers: PreviewChatSession[],
    responseBody: ReadableStream,
  ): Promise<ConversationPreview> => {
    let answer: string = "";
    const askResponse: ConversationPreview = {
      answer: "",
      data_points: [],
      follow_up_questions: [],
    };
    const updateState = (newContent: string) => {
      return new Promise(resolve => {
        setTimeout(() => {
          answer += newContent;
          const latestResponse: ConversationPreview = {
            ...askResponse,
            answer,
          };
          setStreamedAnswers([
            ...answers,
            {
              user: question,
              bot: latestResponse,
            },
          ]);
          resolve(null);
        }, 33);
      });
    };
    try {
      setIsStreaming(true);
      for await (const event of readNDJSONStream(responseBody)) {
        if (!isChatActive.current) {
          break;
        }
        if (event["answer"]) {
          setIsLoading(false);
          await updateState(event["answer"]);
        } else if (event["data_points"]) {
          askResponse.data_points = event["data_points"];
        } else if (event["follow_up_questions"]) {
          askResponse.follow_up_questions = event["follow_up_questions"];
        } else if (event["error"]) {
          setIsLoading(false);
          setIsStreaming(false);
          isChatActive.current = false;
          return {
            ...askResponse,
            answer: event["error"],
          };
        }
      }
    } finally {
      setIsStreaming(false);
    }
    return {
      ...askResponse,
      answer,
    };
  };

  const handleChatRequest = async (
    question: string,
    responseGeneratorModelFamily: ModelFamily,
    responseSystemPrompt: string,
    approach: Approach,
  ): Promise<void> => {
    setIsLoading(true);
    isChatActive.current = true;
    const newAnswer = {
      user: question,
      bot: {
        answer: "",
        data_points: [],
        follow_up_questions: [],
      },
    };
    setAnswers([...answers, newAnswer]);
    setStreamedAnswers([...answers, newAnswer]);
    const history: PreviewConversationParam["history"] = answers.map(answer => {
      return {
        bot: answer.bot.answer,
        user: answer.user,
      };
    });
    try {
      const response = await createConversationRequest({
        history: [...history, { user: question }],
        model_family: responseGeneratorModelFamily,
        system_prompt: responseSystemPrompt,
        approach: approach,
      });
      const responseBody = response.body as ReadableStream;
      const chatResponse = await handleChatStream(question, answers, responseBody);

      setAnswers([...answers, { user: question, bot: chatResponse }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopChat = () => {
    isChatActive.current = false;
    setIsLoading(false);
    setIsStreaming(false);
  };

  const clearChat = () => {
    isChatActive.current = false;
    setIsLoading(false);
    setIsStreaming(false);
    setAnswers([]);
    setStreamedAnswers([]);
  };
  return {
    isLoading,
    answers,
    isStreaming,
    streamedAnswers,
    handleChatRequest,
    clearChat,
    handleStopChat,
  };
};
