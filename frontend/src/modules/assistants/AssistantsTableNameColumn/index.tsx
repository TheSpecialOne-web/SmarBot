import LinkIcon from "@mui/icons-material/Link";
import { Link, Stack } from "@mui/material";

import { CopyButton } from "@/components/buttons/CopyButton";
import { Spacer } from "@/components/spacers/Spacer";
import { useCopy } from "@/hooks/useCopy";
import { Bot, BotWithGroup } from "@/orval/models/backend-api";

type Props = {
  bot: Bot | BotWithGroup;
  groupId?: number;
};

export const AssistantsTableNameColumn = ({ bot, groupId }: Props) => {
  const { isCopied, copy } = useCopy();

  return (
    <Stack direction="row" alignItems="center">
      <Link
        href={
          groupId ? `#/main/groups/${groupId}/assistants/${bot.id}` : `#/main/assistants/${bot.id}`
        }
      >
        {bot.name}
      </Link>
      <Spacer px={8} horizontal />
      <CopyButton
        isCopied={isCopied}
        copy={copy}
        text={`${window.location.origin}/#/main/chat?botId=${bot.id}`}
        tooltipTitle="チャット画面へのURLをコピー"
        copyIcon={<LinkIcon fontSize="small" />}
      />
    </Stack>
  );
};
