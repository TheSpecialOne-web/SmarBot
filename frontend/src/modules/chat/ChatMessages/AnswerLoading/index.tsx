import { CircularProgress, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { Bot, ConversationEvent, ModelFamily } from "@/orval/models/backend-api";

import { BotChatBase } from "../../BotChatBase";

type Props = {
  bot: Bot;
  status: ConversationEvent | undefined;
  queries: string[];
  isEmbedded?: boolean;
};

export const AnswerLoading = ({ bot, status, queries, isEmbedded }: Props) => {
  const [statusList, setStatusList] = useState<ConversationEvent[]>([]);

  useEffect(() => {
    if (!status) {
      setStatusList([]);
      return;
    }
    if (
      (
        [
          ConversationEvent.query_generation_started,
          ConversationEvent.web_documents_retrieval_started,
          ConversationEvent.internal_documents_retrieval_started,
          ConversationEvent.response_generation_started,
          ConversationEvent.prompt_generation_started,
          ConversationEvent.image_generation_started,
        ] as string[]
      ).includes(status)
    ) {
      setStatusList(prev => [...prev, status]);
    }
  }, [status]);

  const renderStatus = (status: ConversationEvent | undefined, modelFamily: ModelFamily) => {
    switch (status) {
      case ConversationEvent.query_generation_started:
        return "検索クエリを生成しています";
      case ConversationEvent.web_documents_retrieval_started:
        return "Webページを検索しています";
      case ConversationEvent.internal_documents_retrieval_started:
        return "ドキュメントを検索しています";
      case ConversationEvent.response_generation_started:
        return ([ModelFamily["o1-preview"], ModelFamily["o1-mini"]] as ModelFamily[]).includes(
          modelFamily,
        )
          ? "思考中です"
          : "回答を生成しています";
      case ConversationEvent.prompt_generation_started:
        return "画像生成プロンプトを生成しています";
      case ConversationEvent.image_generation_started:
        return "画像を生成しています";
      default:
        return "";
    }
  };

  return (
    <BotChatBase bot={bot} isEmbedded={isEmbedded}>
      <Stack direction="row" gap={1}>
        <Stack>
          <Spacer px={4} />
          <CircularProgress size={16} />
        </Stack>
        <Stack gap={1}>
          {statusList.map((status, index) => (
            <Stack key={index} direction="row" alignItems="center" gap={1}>
              <Typography>{renderStatus(status, bot.model_family)}</Typography>
              {(status === ConversationEvent.internal_documents_retrieval_started ||
                status === ConversationEvent.web_documents_retrieval_started ||
                status === ConversationEvent.prompt_generation_started) &&
                queries.length > 0 && (
                  <Typography>
                    {status === ConversationEvent.prompt_generation_started
                      ? "プロンプト"
                      : "検索クエリ"}
                    :{" "}
                    <Typography component="span" variant="body2">
                      {queries.join(", ")}
                    </Typography>
                  </Typography>
                )}
            </Stack>
          ))}
        </Stack>
      </Stack>
    </BotChatBase>
  );
};
