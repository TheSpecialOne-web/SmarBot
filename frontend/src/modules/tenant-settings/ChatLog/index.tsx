import { Stack } from "@mui/material";

import { DownloadChatCompletion } from "../DownloadChatCompletion";
import { DownloadConversation } from "../DownloadConversation";

type Props = {
  enable_api_integrations: boolean;
};

export const ChatLog = ({ enable_api_integrations }: Props) => {
  return (
    <Stack gap={2}>
      <DownloadConversation />
      {enable_api_integrations && <DownloadChatCompletion />}
    </Stack>
  );
};
