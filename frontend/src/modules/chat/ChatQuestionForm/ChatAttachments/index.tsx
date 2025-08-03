import CloseIcon from "@mui/icons-material/Close";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { Box, IconButton, Skeleton, Stack, Typography } from "@mui/material";

import { ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE } from "@/const";
import { ImageFile } from "@/hooks/useAttachment";
import { Attachment } from "@/orval/models/backend-api";

const borderStyle = {
  borderWidth: "1px",
  borderStyle: "solid",
  borderColor: "rgba(0, 0, 0, 0.2)",
  borderRadius: 2,
} as const;

type RemoveButtonProps = {
  onRemove: (attachmentId: string) => void;
  attachment: Attachment;
};

const RemoveButton = ({ onRemove, attachment }: RemoveButtonProps) => {
  return (
    <IconButton
      className="removeButton"
      onClick={() => onRemove(attachment.id)}
      sx={{
        position: "absolute",
        right: -4,
        top: -4,
        bgcolor: "background.paper",
        "&:hover": {
          bgcolor: "background.paper",
        },
        p: 0.25,
        ...borderStyle,
        borderRadius: "50%",
      }}
      size="small"
    >
      <CloseIcon sx={{ fontSize: "14px", color: "black" }} />
    </IconButton>
  );
};

type Props = {
  uploadedAttachments: Attachment[];
  selectedFiles: File[] | null;
  imageFiles: ImageFile[];
  isUploading: boolean;
  onRemove: (attachmentId: string) => void;
};

export const ChatAttachments = ({
  uploadedAttachments,
  selectedFiles,
  imageFiles,
  isUploading,
  onRemove,
}: Props) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 1,
        overflow: "visible",
      }}
    >
      <>
        {uploadedAttachments.length > 0 &&
          uploadedAttachments.map(attachment => {
            const isImage = Object.values(ALLOWED_ATTACHMENT_FILE_EXTENSIONS_IMAGE).includes(
              attachment.file_extension,
            );
            if (isImage) {
              const imageFile = imageFiles?.find(
                file => file.name === `${attachment.name}.${attachment.file_extension}`,
              );
              if (!imageFile) {
                return null;
              }
              return (
                <Stack key={attachment.id} direction="row" alignItems="center" position="relative">
                  <Box
                    component="span"
                    width={56}
                    height={56}
                    sx={{
                      backgroundImage: `url(${imageFile.base64Url})`,
                      backgroundPosition: "50%",
                      backgroundSize: "cover",
                      ...borderStyle,
                    }}
                  />
                  <RemoveButton onRemove={onRemove} attachment={attachment} />
                </Stack>
              );
            }
            return (
              <Stack
                key={attachment.id}
                direction="row"
                alignItems="center"
                gap={1}
                p={2}
                width="fit-content"
                maxWidth="300px"
                position="relative"
                overflow="visible"
                sx={borderStyle}
              >
                <TextSnippetIcon />
                <Typography
                  variant="h6"
                  overflow="hidden"
                  textOverflow="ellipsis"
                  whiteSpace="nowrap"
                >
                  {attachment.name}.{attachment.file_extension}
                </Typography>
                <RemoveButton onRemove={onRemove} attachment={attachment} />
              </Stack>
            );
          })}
        {isUploading &&
          selectedFiles &&
          selectedFiles.map((_, index) => (
            <Box
              key={index}
              sx={{
                display: "flex",
                alignItems: "center",
                columnGap: 1,
                p: 2,
                width: "fit-content",
                ...borderStyle,
              }}
            >
              <Skeleton animation="pulse" variant="rounded" width="24px" height="24px" />
              <Skeleton animation="pulse" variant="text" width="200px" height="24px" />
            </Box>
          ))}
      </>
    </Box>
  );
};
