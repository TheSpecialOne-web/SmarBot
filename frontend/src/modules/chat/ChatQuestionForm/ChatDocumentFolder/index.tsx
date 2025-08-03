import CloseIcon from "@mui/icons-material/Close";
import FolderIcon from "@mui/icons-material/Folder";
import { IconButton, Stack, Typography } from "@mui/material";

import { DocumentFolder } from "@/orval/models/backend-api";

const borderStyle = {
  borderWidth: "1px",
  borderStyle: "solid",
  borderColor: "rgba(0, 0, 0, 0.2)",
  borderRadius: 2,
} as const;

type Props = {
  selectedDocumentFolder: DocumentFolder;
  onRemove: () => void;
};

export const ChatDocumentFolder = ({ selectedDocumentFolder, onRemove }: Props) => {
  return (
    <Stack
      direction="row"
      gap={1}
      alignItems="center"
      sx={{
        p: 2,
        ...borderStyle,
        maxWidth: "300px",
        position: "relative",
        ":hover": {
          "& .removeButton": {
            visibility: "visible",
          },
        },
      }}
    >
      <FolderIcon />
      <Typography variant="h6" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap">
        {selectedDocumentFolder.name}
      </Typography>
      <IconButton
        className="removeButton"
        onClick={onRemove}
        sx={{
          position: "absolute",
          right: -6,
          top: -6,
          visibility: "hidden",
          ...borderStyle,
          borderRadius: "50%",
          bgcolor: "background.paper",
          "&:hover": {
            bgcolor: "background.paper",
          },
        }}
        size="small"
      >
        <CloseIcon sx={{ fontSize: "13px", color: "black" }} />
      </IconButton>
    </Stack>
  );
};
