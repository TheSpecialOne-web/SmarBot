import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import { Link, Stack } from "@mui/material";

import { DocumentFolderDetail } from "@/orval/models/backend-api";

type Props = {
  documentFolderDetail: DocumentFolderDetail;
  rootDocumentFolderId: string;
  onMoveToFolder: (folderId: string) => void;
};

export const DocumentFolderBreadcrumbs = ({
  documentFolderDetail,
  rootDocumentFolderId,
  onMoveToFolder,
}: Props) => {
  const isRootFolder = documentFolderDetail.id === rootDocumentFolderId;
  return (
    <Stack direction="row" alignItems="center" gap={0.5}>
      <Link
        onClick={() => onMoveToFolder(rootDocumentFolderId)}
        sx={{
          cursor: isRootFolder ? "default" : "pointer",
          pointerEvents: isRootFolder ? "none" : "auto",
          textDecoration: "none",
        }}
      >
        <Stack justifyContent="center">
          <HomeOutlinedIcon fontSize="small" color={isRootFolder ? "secondary" : "primary"} />
        </Stack>
      </Link>

      {documentFolderDetail.ancestor_document_folders.map(({ id, name }) => (
        <Stack key={id} direction="row" alignItems="center" gap={0.5}>
          <span>/</span>
          <Link
            onClick={() => onMoveToFolder(id)}
            sx={{ cursor: "pointer", textDecoration: "none" }}
          >
            {name}
          </Link>
        </Stack>
      ))}

      {documentFolderDetail.name && (
        <Stack direction="row" alignItems="center" gap={0.5}>
          <span>/</span>
          {documentFolderDetail.name}
        </Stack>
      )}
    </Stack>
  );
};
