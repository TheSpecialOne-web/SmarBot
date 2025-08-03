import FolderIcon from "@mui/icons-material/Folder";
import { Box, Stack, Typography } from "@mui/material";
import { styled } from "@mui/system";

import { Spacer } from "@/components/spacers/Spacer";
import { Attachment, DocumentFolder } from "@/orval/models/backend-api";

import { UserAttachment } from "./UserAttachment";
import { UserChatBase } from "./UserChatBase";

const StyledBox = styled(Box)(() => ({
  padding: "8px 16px",
  borderWidth: "1px",
  borderStyle: "solid",
  borderColor: "rgba(0, 0, 0, 0.2)",
  borderRadius: 8,
  width: "fit-content",
  maxWidth: "300px",
  position: "relative",
  overflow: "visible",
  ":hover": {
    "& .removeButton": {
      visibility: "visible",
    },
  },
}));

type Props = {
  botId?: number;
  message: string;
  attachments?: Attachment[];
  documentFolder?: DocumentFolder;
};

export const UserChatMessage = ({ botId, message, attachments, documentFolder }: Props) => {
  const showChatAttachments = botId && attachments && attachments.length > 0;
  return (
    <UserChatBase>
      {(documentFolder || showChatAttachments) && (
        <>
          <Spacer px={8} />
          <Stack direction="row" gap={1}>
            {documentFolder && (
              <StyledBox>
                <Stack direction="row" alignItems="center" gap={1}>
                  <FolderIcon />
                  <Typography
                    variant="h6"
                    overflow="hidden"
                    textOverflow="ellipsis"
                    whiteSpace="nowrap"
                  >
                    {documentFolder.name}
                  </Typography>
                </Stack>
              </StyledBox>
            )}
            {showChatAttachments && (
              <Stack direction="row" gap={1}>
                {attachments.map(attachment => (
                  <UserAttachment key={attachment.id} botId={botId} attachment={attachment} />
                ))}
              </Stack>
            )}
          </Stack>
          <Spacer px={8} />
        </>
      )}
      <Typography>{message}</Typography>
    </UserChatBase>
  );
};
