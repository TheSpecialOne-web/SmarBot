import { enqueueSnackbar } from "notistack";
import { useContext } from "react";
import { useNavigate } from "react-router-dom";

import { ConversationContext } from "@/contexts/ConversationContext";
import { getErrorMessage } from "@/libs/error";
import { createConversationTitle, getConversation, updateConversation } from "@/orval/backend-api";
import { UpdateConversationParam } from "@/orval/models/backend-api";

import { useUserInfo } from "./useUserInfo";

export const useConversation = () => {
  const navigate = useNavigate();

  const {
    conversations,
    isLoadingFetchConversations,
    isValidatingFetchConversations,
    refreshConversations,
  } = useContext(ConversationContext);

  const { userInfo } = useUserInfo();

  const handleGetConversation = async (conversationId: string) => {
    try {
      const data = await getConversation(userInfo.id, conversationId);
      return data;
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueSnackbar(errMsg || "会話の取得に失敗しました。", {
        variant: "error",
        preventDuplicate: true,
      });
      navigate("/main/chat");
      throw e;
    }
  };

  const updateTitle = async (conversationId: string, title: string) => {
    const updateParam: UpdateConversationParam = {
      title,
    };
    await updateConversation(userInfo.id, conversationId, updateParam);
    refreshConversations();
  };

  return {
    conversations,
    isLoadingFetchConversations,
    isValidatingFetchConversations,
    getConversation: handleGetConversation,
    createConversationTitle,
    refreshConversations,
    updateTitle,
  };
};
