import { createContext, ReactNode } from "react";

import { useUserInfo } from "@/hooks/useUserInfo";
import { useGetConversations } from "@/orval/backend-api";
import { Conversation, TenantStatus } from "@/orval/models/backend-api";

type ConversationContextType = {
  conversations: Conversation[];
  isLoadingFetchConversations: boolean;
  isValidatingFetchConversations: boolean;
  refreshConversations: () => void;
};

export const ConversationContext = createContext<ConversationContextType>({
  conversations: [],
  isLoadingFetchConversations: false,
  isValidatingFetchConversations: true,
  refreshConversations: () => {},
});

export const ConversationContextProvider = ({ children }: { children: ReactNode }) => {
  const { userInfo } = useUserInfo();

  const limit = 20;
  const enableGetConversations = Boolean(
    !userInfo.tenant.ip_blocked && userInfo.tenant.status !== TenantStatus.suspended,
  );

  const {
    data,
    isLoading: isLoadingFetchConversations,
    isValidating: isValidatingFetchConversations,
    mutate: refreshConversations,
  } = useGetConversations(
    userInfo.id,
    { limit: limit, offset: 0 },
    { swr: { enabled: enableGetConversations } },
  );

  const conversations = data?.conversations || [];

  return (
    <ConversationContext.Provider
      value={{
        conversations,
        isLoadingFetchConversations,
        isValidatingFetchConversations,
        refreshConversations,
      }}
    >
      {children}
    </ConversationContext.Provider>
  );
};
