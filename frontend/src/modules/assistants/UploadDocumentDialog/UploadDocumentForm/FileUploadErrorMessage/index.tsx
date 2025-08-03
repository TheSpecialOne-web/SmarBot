import { Alert, Box, Stack, Tooltip, Typography } from "@mui/material";
import { FieldErrors } from "react-hook-form";

import { CreateDocumentsParam } from "@/orval/models/backend-api";

type Props = {
  invalidTypeFiles: File[];
  duplicateFiles: File[];
  isFileFull: boolean;
  isFileNameEmpty: boolean;
  errors: FieldErrors<CreateDocumentsParam>;
};

export const FileUploadErrorMassage = ({
  invalidTypeFiles,
  duplicateFiles,
  isFileFull,
  isFileNameEmpty,
  errors,
}: Props) => {
  return (
    <Box>
      {invalidTypeFiles.length > 0 && (
        <Tooltip
          title={
            <>
              {invalidTypeFiles.map(file => (
                <Typography key={file.name} variant="caption">
                  {file.name}
                </Typography>
              ))}
            </>
          }
        >
          <Stack sx={{ alignItems: "center" }} gap={1} borderRadius={1}>
            <Alert severity="warning">
              {invalidTypeFiles.length}個のファイルが対応していない形式のため追加できませんでした
            </Alert>
          </Stack>
        </Tooltip>
      )}
      {duplicateFiles.length > 0 && (
        <Tooltip
          title={
            <>
              {duplicateFiles.map(file => (
                <Typography key={file.name} variant="caption">
                  {file.name}
                </Typography>
              ))}
            </>
          }
        >
          <Stack alignItems="center" gap={1} borderRadius={1}>
            <Alert severity="warning">
              {duplicateFiles.length}個のファイルが重複しているため追加できませんでした
            </Alert>
          </Stack>
        </Tooltip>
      )}
      {isFileFull && (
        <Stack alignItems="center" gap={1} borderRadius={1}>
          <Alert severity="warning">10個を超えるファイルを追加できませんでした</Alert>
        </Stack>
      )}
      {isFileNameEmpty && (
        <Stack alignItems="center" gap={1} borderRadius={1}>
          <Alert severity="warning">空のファイルは追加できません</Alert>
        </Stack>
      )}
      {errors?.files && (
        <Stack alignItems="center" gap={1} borderRadius={1}>
          <Alert severity="error">
            {errors.files?.message || "なんらかのエラーが発生しました"}
          </Alert>
        </Stack>
      )}
    </Box>
  );
};
