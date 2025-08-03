import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined";
import { Stack } from "@mui/material";

import { DocumentFolderDetail } from "@/orval/models/backend-api";

type Props = {
  documentFolderDetail: DocumentFolderDetail;
};

export const DocumentFolderPaths = ({ documentFolderDetail }: Props) => {
  return (
    <Stack direction="row" alignItems="center" gap={0.5}>
      <Stack justifyContent="center">
        <HomeOutlinedIcon fontSize="small" />
      </Stack>
      {documentFolderDetail.ancestor_document_folders.map(({ id, name }) => (
        <Stack key={id} direction="row" alignItems="center" gap={0.5}>
          <span>/</span>
          {name}
        </Stack>
      ))}

      {documentFolderDetail.name && (
        <Stack direction="row" alignItems="center" gap={0.5}>
          <span>/</span>
          <span>{documentFolderDetail.name}</span>
        </Stack>
      )}
    </Stack>
  );
};
