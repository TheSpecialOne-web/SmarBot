import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { Box, Skeleton, Stack, Typography } from "@mui/material";
import { styled } from "@mui/system";

import { ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE } from "@/const";
import { useGetAttachmentSignedUrl } from "@/orval/backend-api";
import { Attachment } from "@/orval/models/backend-api";

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
  botId: number;
  attachment: Attachment;
};

export const UserAttachment = ({ botId, attachment }: Props) => {
  const { data, isLoading } = useGetAttachmentSignedUrl(botId, attachment.id, {
    swr: {
      enabled:
        !isNaN(botId) &&
        Object.values(ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE).includes(attachment.file_extension),
    },
  });
  const signedUrl = data?.signed_url;

  if (isLoading) {
    return <Skeleton variant="rectangular" width={300} height={40} />;
  }
  return (
    <>
      {signedUrl ? (
        <Box
          component="img"
          src={signedUrl}
          alt={attachment.name}
          sx={{
            maxWidth: "360px",
            maxHeight: "300px",
            width: "100%",
            height: "auto",
          }}
        />
      ) : (
        <StyledBox key={attachment.id}>
          <Stack direction="row" alignItems="center" gap={1}>
            <TextSnippetIcon />
            <Typography variant="h6" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap">
              {attachment.name}.{attachment.file_extension}
            </Typography>
          </Stack>
          {attachment.is_blob_deleted && (
            <Typography variant="caption">※保存期間が終了したため、参照できません。</Typography>
          )}
        </StyledBox>
      )}
    </>
  );
};
