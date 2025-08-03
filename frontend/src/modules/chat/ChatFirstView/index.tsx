import { Approach, Bot } from "@/orval/models/backend-api";

import { AssistantChatFirstView } from "./AssistantChatFirstView";
import { BotIntroduction } from "./BotIntroduction";
import { FoundationModelFirstView } from "./FoundationModelFirstView";
import { SearchChatFirstView } from "./SearchChatFirstView";

type Props = {
  onInput: (question: string) => void;
  bot: Bot;
  showPromptTemplates?: boolean;
  isEmbedded?: boolean;
};

export const ChatFirstView = ({
  onInput,
  bot,
  showPromptTemplates = true,
  isEmbedded = false,
}: Props) => {
  switch (bot.approach) {
    case Approach.text_2_image:
      return <BotIntroduction bot={bot} />;
    case Approach.chat_gpt_default:
      return (
        <FoundationModelFirstView onInput={onInput} showPromptTemplates={showPromptTemplates} />
      );
    case Approach.ursa:
      return (
        <SearchChatFirstView
          bot={bot}
          onInput={onInput}
          showPromptTemplates={showPromptTemplates}
        />
      );
    default:
      return (
        <AssistantChatFirstView
          onInput={onInput}
          bot={bot}
          showPromptTemplates={showPromptTemplates}
          isEmbedded={isEmbedded}
        />
      );
  }
};
