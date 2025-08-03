import { useAuth0 } from "@auth0/auth0-react";
import readNDJSONStream from "ndjson-readablestream";
import { useContext, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { SENSITIVE_CONTENTS } from "@/const";
import { EmbedContext } from "@/contexts/EmbedContext";
import { getErrorMessage } from "@/libs/error";
import {
  updateChatCompletionFeedbackComment,
  updateChatCompletionFeedbackEvaluation,
} from "@/orval/api";
import {
  createConversationFeedbackComment,
  updateConversationEvaluation,
  validateConversation,
} from "@/orval/backend-api";
import {
  CreateChatCompletionRequest,
  CreateChatCompletionResponse,
  Message,
  MessageRole,
} from "@/orval/models/api";
import {
  Attachment,
  Bot,
  ConversationEvent,
  ConversationRequest,
  ConversationResponse,
  ConversationTurn,
  ConversationValidationResult,
  DataPoint,
  DocumentFolder,
  Feedback,
} from "@/orval/models/backend-api";
import { ChatSession } from "@/types/chat";

import { useConversation } from "./useConversation";
import { useCustomSnackbar } from "./useCustomSnackbar";
import { useUserInfo } from "./useUserInfo";

export const useChat = () => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const { userInfo } = useUserInfo();
  const navigate = useNavigate();
  const location = useLocation();
  const { conversationId } = useParams();
  const { endpointId, clientId } = useContext(EmbedContext);

  const [responseConversationId, setResponseConversationId] =
    useState<ConversationResponse["conversation_id"]>();

  // チャット開始からストリーム開始まで
  const [isLoading, setIsLoading] = useState(false);
  const [answers, setAnswers] = useState<ChatSession[]>([]);
  const [status, setStatus] = useState<ConversationEvent>();
  const [queries, setQueries] = useState<string[]>([]);
  // ストリーム開始からストリーム終了まで
  const [isStreaming, setIsStreaming] = useState(false);
  const isManuallyStopped = useRef<boolean>(false);
  const [streamedAnswers, setStreamedAnswers] = useState<ChatSession[]>([]);
  // チャット開始からストリーム終了まで
  const isChatActive = useRef<boolean>(false);
  const { createConversationTitle, refreshConversations } = useConversation();
  const currentPath = location.pathname;
  const pathHasConversationId = Boolean(conversationId);
  const [isChatReady, setIsChatReady] = useState(true);
  // feedback送信から完了まで
  const [isFeedbackSending, setIsFeedbackSending] = useState(false);

  const formatValidationErrorMessage = (validation: ConversationValidationResult): string => {
    const sensitiveContents = validation.sensitive_contents
      .map(
        data =>
          `- ${SENSITIVE_CONTENTS[data.type as keyof typeof SENSITIVE_CONTENTS]}: ${data.content}`,
      )
      .join("\n");
    return `個人情報が含まれていたため、チャットができませんでした\n\n${sensitiveContents}`;
  };

  const updateAnswerWithError = (
    question: string,
    errorMessage: string,
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
  ) => {
    const errorAnswer = {
      user: question,
      bot: {
        conversation_id: "",
        conversation_turn_id: "",
        answer: errorMessage,
        data_points: [],
        follow_up_questions: [],
      },
      attachments: attachments || [],
      documentFolder: documentFolder,
    };
    setStreamedAnswers([...answers, errorAnswer]);
    setAnswers([...answers, errorAnswer]);
  };

  // チャットを強制的に終了する
  const onStopChat = () => {
    isChatActive.current = false;
    isManuallyStopped.current = true;
    setIsLoading(false);
    setIsStreaming(false);
  };

  const resetChat = () => {
    isChatActive.current = false;
    isManuallyStopped.current = false;
    setIsLoading(false);
    setIsStreaming(false);
    clearChatHistory();
    setResponseConversationId("");
  };

  const clearChatHistory = () => {
    setStreamedAnswers([]);
    setAnswers([]);
  };

  const { getAccessTokenSilently } = useAuth0();

  const createConversationRequest = async (
    botId: Bot["id"],
    options: ConversationRequest,
  ): Promise<Response> => {
    const basePath = import.meta.env.VITE_API_BASE_URL;
    const accessToken = await getAccessTokenSilently();
    return await fetch(`${basePath}/bots/${botId}/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant-Id": userInfo.tenant.id.toString() || "",
      },
      body: JSON.stringify(options),
    });
  };

  async function* streamGenerator<T>(responseBody: ReadableStream): AsyncGenerator<T> {
    const reader = responseBody.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      if (!isChatActive.current) {
        reader.cancel();
        return;
      }

      try {
        const { done, value } = await reader.read();
        if (done) {
          reader.releaseLock();
          return;
        }

        const decoded = decoder.decode(value, { stream: !done });
        const decodedParts = decoded.split("\n");

        for (const part of decodedParts) {
          try {
            const parsed = JSON.parse(part);
            yield parsed;
          } catch (e) {
            // JSON parse error
          }
        }
      } catch (e) {
        // ReadableStream error
        reader.releaseLock();
        throw e;
      }
    }
  }

  const onChatStream = async (
    question: string,
    answers: ChatSession[],
    responseBody: ReadableStream,
    botId?: Bot["id"],
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
  ): Promise<ConversationResponse> => {
    let answer: string = "";
    const askResponse: ConversationResponse = {
      answer: "",
      conversation_id: "",
      conversation_turn_id: "",
      data_points: [],
    };

    const updateState = (newContent: string) => {
      return new Promise(resolve => {
        setTimeout(() => {
          const plainAnswer = answer;
          // 表示のために⚫️を追加
          answer += newContent + "⚫️";
          const latestResponse: ConversationResponse = {
            ...askResponse,
            answer,
          };
          setStreamedAnswers([
            ...answers,
            {
              user: question,
              bot: latestResponse,
              attachments: attachments || [],
              documentFolder: documentFolder,
            },
          ]);
          answer = plainAnswer + newContent;
          resolve(null);
        }, 11);
      });
    };

    try {
      setIsStreaming(true);
      for await (const event of readNDJSONStream(responseBody)) {
        if (!isChatActive.current) {
          break;
        }
        if (event["conversation_id"]) {
          askResponse.conversation_id = event["conversation_id"];
          if (pathHasConversationId) {
            continue;
          }
          if (isChatActive.current && botId) {
            navigate(`${currentPath}/${event["conversation_id"]}?botId=${botId}`, {
              replace: true,
            });
            setResponseConversationId(event["conversation_id"]);
          }
        } else if (event["event"]) {
          setStatus(event["event"]);
        } else if (event["query"]) {
          setQueries(event["query"]);
        } else if (event["conversation_turn_id"]) {
          askResponse.conversation_turn_id = event["conversation_turn_id"];
        } else if (event["data_points"]) {
          askResponse.data_points = event["data_points"];
        } else if (event["follow_up_questions"]) {
          askResponse.follow_up_questions = event["follow_up_questions"];
        } else if (event["answer"]) {
          setIsLoading(false);
          await updateState(event["answer"]);
        } else if (event["error"]) {
          setIsLoading(false);
          setIsStreaming(false);
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

  const onChatRequest = async (
    botId: Bot["id"],
    question: string,
    useWebBrowsing: boolean,
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
    propsConversationId?: string,
  ): Promise<void> => {
    setIsLoading(true);
    const startTime = Date.now();
    // チャットが30秒以内に準備にならなかった場合はチャットを開始する
    while (!isChatReady && Date.now() - startTime < 30000) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    setIsChatReady(false);
    isChatActive.current = true;
    const newAnswer = {
      user: question,
      bot: {
        conversation_id: "",
        conversation_turn_id: "",
        answer: "",
        data_points: [],
        follow_up_questions: [],
      },
      attachments: attachments || [],
      documentFolder: documentFolder,
    };
    setAnswers([...answers, newAnswer]);
    setStreamedAnswers([...answers, newAnswer]);

    // チャット開始時に個人情報のバリデーションを行う
    if (userInfo.tenant.is_sensitive_masked) {
      const validation = await validateConversation(botId, { question });
      if (!validation.is_valid) {
        const errorMessage = formatValidationErrorMessage(validation);
        updateAnswerWithError(question, errorMessage, attachments, documentFolder);
        isChatActive.current = false;
        setIsLoading(false);
        return;
      }
    }

    try {
      const response = await createConversationRequest(botId, {
        question,
        stream: true,
        ...(propsConversationId && { conversation_id: propsConversationId }),
        attachments: attachments?.map(attachment => ({ id: attachment.id, from: "user" })),
        use_web_browsing: useWebBrowsing,
        document_folder_id: documentFolder?.id,
      });

      if (!response.ok) {
        throw new Error("チャット中にエラーが発生しました。");
      }
      if (!response.body) {
        throw new Error("No response body");
      }

      const chatResponse = await onChatStream(
        question,
        answers,
        response.body,
        botId,
        attachments,
        documentFolder,
      );

      if (isManuallyStopped.current || isChatActive.current) {
        setAnswers([
          ...answers,
          {
            user: question,
            bot: chatResponse,
            attachments: attachments || [],
            documentFolder: documentFolder,
          },
        ]);
        if (answers.length === 0) {
          await createConversationTitle(botId, chatResponse.conversation_id);
        }
      }
    } finally {
      refreshConversations();
      isChatActive.current = false;
      setIsLoading(false);
      setIsChatReady(true);
    }
  };

  const onEmbedChatStream = async (
    question: string,
    answers: ChatSession[],
    responseBody: ReadableStream,
  ): Promise<ConversationResponse> => {
    let answer: string = "";
    const askResponse: ConversationResponse = {
      answer: "",
      conversation_id: "",
      conversation_turn_id: "",
      data_points: [],
    };

    const updateState = (content: string) => {
      return new Promise(resolve => {
        answer = content + "⚫️";
        setTimeout(() => {
          const latestResponse: ConversationResponse = {
            ...askResponse,
            answer,
          };
          setStreamedAnswers([
            ...(answers.slice(0, answers.length - 1) || []),
            {
              user: question,
              bot: latestResponse,
              attachments: [],
            },
          ]);
          answer = content;
          resolve(null);
        }, 11);
      });
    };

    setIsStreaming(true);
    const generator = streamGenerator<CreateChatCompletionResponse>(responseBody);
    for await (const chunk of generator) {
      askResponse.conversation_turn_id = chunk.id;
      askResponse.data_points = chunk.data_points as DataPoint[];
      if (chunk.content.length > 0) {
        setIsLoading(false);
        await updateState(chunk.content);
      }

      if (chunk.error) {
        setIsLoading(false);
        setIsStreaming(false);
        isChatActive.current = false;
        return {
          ...askResponse,
          answer: chunk.error,
        };
      }
    }
    setIsStreaming(false);

    return {
      ...askResponse,
      answer,
    };
  };

  const getEmbedChatCompletionRequest = (answers: ChatSession[]): CreateChatCompletionRequest => {
    return {
      messages: answers.flatMap(answer => {
        const messages: Message[] = [
          {
            role: MessageRole.user,
            content: answer.user,
          },
        ];
        if (answer.bot.answer) {
          messages.push({
            role: MessageRole.assistant,
            content: answer.bot.answer,
          });
        }
        return messages;
      }),
      stream: true,
    };
  };

  const createChatCompletionRequest = async (
    options: CreateChatCompletionRequest,
  ): Promise<Response> => {
    const basePath = import.meta.env.VITE_EXTERNAL_API_URL;
    return fetch(`${basePath}/endpoints/${endpointId}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-neoAI-Chat-Client-Id": clientId,
      },
      body: JSON.stringify(options),
    });
  };

  // 埋め込みチャット
  const onEmbedChatRequest = async (question: string): Promise<ConversationResponse> => {
    setIsLoading(true);
    isChatActive.current = true;

    const newAnswers = [
      ...answers,
      {
        user: question,
        bot: {
          conversation_id: "",
          conversation_turn_id: "",
          answer: "",
          data_points: [],
        },
      },
    ];
    setAnswers(newAnswers);
    setStreamedAnswers(newAnswers);

    try {
      const request = getEmbedChatCompletionRequest(newAnswers);
      const response = await createChatCompletionRequest(request);

      if (!response.ok) {
        throw new Error("チャット中にエラーが発生しました。");
      }
      if (!response.body) {
        throw new Error("No response body");
      }

      const chatResponse = await onEmbedChatStream(question, newAnswers, response.body);
      if (isManuallyStopped.current || isChatActive.current) {
        setAnswers([
          ...answers,
          {
            user: question,
            bot: chatResponse,
          },
        ]);
      }
      return chatResponse;
    } finally {
      isChatActive.current = false;
      setIsLoading(false);
    }
  };

  // feedbackを送信する
  const onSendFeedback = async (conversationTurnId: ConversationTurn["id"], feedback: Feedback) => {
    setIsFeedbackSending(true);
    try {
      if (!conversationId) {
        throw new Error("conversationId is not defined.");
      }
      if (!feedback.evaluation && !feedback.comment) {
        throw new Error("Feedback is undefined.");
      }
      await Promise.all([
        feedback.evaluation
          ? updateConversationEvaluation(conversationId, conversationTurnId, {
              evaluation: feedback.evaluation,
            })
          : undefined,
        feedback.comment
          ? createConversationFeedbackComment(conversationId, conversationTurnId, {
              comment: feedback.comment,
            })
          : undefined,
      ]);
      const newAnswers = answers.map(answer => {
        if (answer.bot.conversation_turn_id === conversationTurnId) {
          return {
            ...answer,
            feedback,
          };
        }
        return answer;
      });
      setAnswers(newAnswers);
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フィードバックの送信に失敗しました。" });
    } finally {
      setIsFeedbackSending(false);
    }
  };

  const onSendEmbeddedFeedback = async (chatCompletionId: string, feedback: Feedback) => {
    setIsFeedbackSending(true);
    try {
      if (!chatCompletionId) {
        throw new Error("chatCompletionId is not defined.");
      }
      if (!feedback.evaluation && !feedback.comment) {
        throw new Error("Feedback is undefined.");
      }
      await Promise.all([
        feedback.evaluation
          ? updateChatCompletionFeedbackEvaluation(endpointId, chatCompletionId, {
              evaluation: feedback.evaluation,
            })
          : undefined,
        feedback.comment
          ? updateChatCompletionFeedbackComment(endpointId, chatCompletionId, {
              comment: feedback.comment,
            })
          : undefined,
      ]);

      const newAnswers = answers.map(answer =>
        answer.bot.conversation_turn_id === chatCompletionId ? { ...answer, feedback } : answer,
      );
      setAnswers(newAnswers);
    } catch (error) {
      const errMsg = getErrorMessage(error);
      enqueueErrorSnackbar({ message: errMsg || "フィードバックの送信に失敗しました。" });
    } finally {
      setIsFeedbackSending(false);
    }
  };

  return {
    isLoading,
    status,
    queries,
    isStreaming,
    answers,
    setAnswers,
    streamedAnswers,
    onChatRequest,
    onEmbedChatRequest,
    clearChatHistory,
    resetChat,
    onStopChat,
    responseConversationId,
    isFeedbackSending,
    onSendFeedback,
    onSendEmbeddedFeedback,
  };
};
