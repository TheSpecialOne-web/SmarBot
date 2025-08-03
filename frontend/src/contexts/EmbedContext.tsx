import { AxiosHeaders, InternalAxiosRequestConfig } from "axios";
import { createContext, ReactNode, useEffect } from "react";
import { useLocation } from "react-router-dom";

import { CircularLoading } from "@/components/loadings/CircularLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { apiInstance } from "@/libs/api/mutator";
import { useGetEndpointInfo } from "@/orval/api";
import { Approach, Bot } from "@/orval/models/backend-api";
import { DEFAULT_ASSISTANT_ICON_COLOR } from "@/theme";

type EmbedContextType = {
  clientId: string;
  endpointId: string;
  bot: Bot;
};

export const EmbedContext = createContext<EmbedContextType>({} as EmbedContextType);

export const EmbedContextProvider = ({ children }: { children: ReactNode }) => {
  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const clientId = queryParams.get("client_id");
  const endpointId = queryParams.get("endpoint_id");
  if (!clientId || !endpointId) {
    enqueueErrorSnackbar({ message: "クエリパラメータが不正です。" });
    throw new Error("Invalid query parameters");
  }

  useEffect(() => {
    const headers = {
      "X-neoAI-Chat-Client-Id": clientId,
    };
    const interceptorId = apiInstance.interceptors.request.use(
      (config): InternalAxiosRequestConfig => ({
        ...config,
        headers: new AxiosHeaders({
          ...config.headers,
          ...headers,
        }),
      }),
    );

    return () => {
      apiInstance.interceptors.request.eject(interceptorId);
    };
  }, [clientId]);

  const { data: endpointInfo } = useGetEndpointInfo(endpointId, { swr: { enabled: Boolean(clientId && endpointId) } });

  if (!endpointInfo?.assistant) {
    return <CircularLoading />;
  }

  const bot: Bot = {
    id: endpointInfo.assistant.id,
    name: endpointInfo.assistant.name,
    description: endpointInfo.assistant.description,
    created_at: "",
    model_family: "gpt-4o",
    pdf_parser: "pypdf",
    status: "active",
    system_prompt: "システムプロンプト",
    icon_url: endpointInfo.assistant.icon_url || "",
    icon_color: endpointInfo.assistant.icon_color || DEFAULT_ASSISTANT_ICON_COLOR,
    approach: Approach.neollm,
    document_limit: 5,
    enable_web_browsing: false,
    enable_follow_up_questions: false,
    example_questions: [],
  };

  const contextValue: EmbedContextType = {
    clientId,
    endpointId,
    bot,
  };

  return <EmbedContext.Provider value={contextValue}>{children}</EmbedContext.Provider>;
};
