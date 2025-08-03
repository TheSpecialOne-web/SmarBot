import { DeleteOutlineOutlined } from "@mui/icons-material";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import { Box, IconButton, List, ListItem, ListItemText, Stack, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { MultipleFileInput } from "@/components/inputs/MultipleFileInput";
import { Spacer } from "@/components/spacers/Spacer";
import { ALLOWED_FILE_EXTENSIONS, ALLOWED_FILE_EXTENSIONS_V2 } from "@/const";
import { FileValidationType, validateFile, validateFileV2 } from "@/libs/files";
import { CreateDocumentsParam, Document } from "@/orval/models/backend-api";

import { FileUploadErrorMassage } from "./FileUploadErrorMessage";

type Props = {
  onSubmit: (params: CreateDocumentsParam) => Promise<void>;
  onClose: () => void;
  documents: Document[];
};

export const UploadDocumentForm = ({ onSubmit, onClose, documents }: Props) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [invalidTypeFiles, setInvalidTypeFiles] = useState<File[]>([]);
  const [duplicateFiles, setDuplicateFiles] = useState<File[]>([]);
  const [isFileFull, setIsFileFull] = useState<boolean>(false);
  const [isFileNameEmpty, setIsFileNameEmpty] = useState<boolean>(false);
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    clearErrors,
  } = useForm<CreateDocumentsParam>({
    defaultValues: {
      memo: "",
      files: [],
    },
  });

  const { legacyMicrosoftOfficeExtension } = useFlags();

  const handleFormErrorClear = useCallback(() => {
    setDuplicateFiles([]);
    setInvalidTypeFiles([]);
    setIsFileNameEmpty(false);
    setIsFileFull(false);
    clearErrors();
  }, [clearErrors]);

  const handleAddFiles = useCallback(
    (newFiles: File[]) => {
      handleFormErrorClear();

      const invalidTypeFiles = [];
      const duplicateFiles = [];
      const validFiles = [...selectedFiles];

      for (const file of newFiles) {
        if (validFiles.length >= 10) {
          setIsFileFull(true);
          break;
        }

        let validateError;

        legacyMicrosoftOfficeExtension
          ? (validateError = validateFileV2(file, validFiles, documents))
          : (validateError = validateFile(file, validFiles, documents));

        if (!validateError) {
          validFiles.push(file);
          continue;
        }

        if (validateError.type === FileValidationType.Invalid) {
          invalidTypeFiles.push(file);
        } else if (validateError.type === FileValidationType.Duplicated) {
          duplicateFiles.push(file);
        } else if (validateError.type === FileValidationType.Empty) {
          setIsFileNameEmpty(true);
        }
      }

      setSelectedFiles(validFiles);
      setValue("files", validFiles);

      if (invalidTypeFiles.length > 0) {
        setInvalidTypeFiles(invalidTypeFiles);
      }
      if (duplicateFiles.length > 0) {
        setDuplicateFiles(duplicateFiles);
      }
    },
    [documents, handleFormErrorClear, legacyMicrosoftOfficeExtension, selectedFiles, setValue],
  );

  const onFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    clearErrors("files");
    if (event.target.files !== null) {
      const files = Array.from(event.target.files);
      handleAddFiles(files);
    }
  };

  const onDrop = useCallback(
    (files: File[]) => {
      handleAddFiles(files);
    },
    [handleAddFiles],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, noClick: true });

  const handleDeleteFile = (file: File) => {
    const newFiles = selectedFiles.filter(f => f.name !== file.name);
    setSelectedFiles(newFiles);
    setValue("files", newFiles);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <CustomDialogContent>
        <CustomTextField
          label="メモ"
          autoFocus
          fullWidth
          control={control}
          placeholder="資料に関するメモを入力してください"
          name="memo"
          type="text"
        />

        <Spacer px={14} />

        <Box
          sx={{
            border: "1px dashed",
            borderColor: "divider",
            py: 4,
            borderRadius: 2,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 1,
            bgcolor: "primaryBackground.main",
            ...(isDragActive && {
              borderStyle: "solid",
              borderColor: "primary.main",
              opacity: 0.5,
            }),
          }}
          component="div"
          {...getRootProps({
            onClick: event => event.stopPropagation(),
          })}
        >
          <Stack direction="row" alignItems="center">
            <FileUploadIcon />
            <Typography>ファイルをここにドラッグ＆ドロップ</Typography>
          </Stack>
          <Typography variant="body2">または</Typography>
          <input {...getInputProps()} />
          <MultipleFileInput
            allowed_extension={
              legacyMicrosoftOfficeExtension
                ? `${Object.values(ALLOWED_FILE_EXTENSIONS_V2)
                    .map(extension => `.${extension}`)
                    .join(", ")}`
                : `${Object.values(ALLOWED_FILE_EXTENSIONS)
                    .map(extension => `.${extension}`)
                    .join(", ")}`
            }
            onChange={onFileChange}
          />

          <FileUploadErrorMassage
            invalidTypeFiles={invalidTypeFiles}
            duplicateFiles={duplicateFiles}
            isFileFull={isFileFull}
            isFileNameEmpty={isFileNameEmpty}
            errors={errors}
          />

          <Spacer px={14} />

          {selectedFiles.length > 0 && (
            <List
              sx={{
                display: "flex",
                flexDirection: "column",
                width: "100%",
                maxWidth: 360,
                bgcolor: "background.paper",
                overflow: "auto",
                maxHeight: 300,
              }}
            >
              {selectedFiles.map(file => (
                <ListItem
                  key={file.name}
                  secondaryAction={
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => handleDeleteFile(file)}
                    >
                      <DeleteOutlineOutlined color="error" />
                    </IconButton>
                  }
                >
                  <ListItemText>{file.name}</ListItemText>
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Spacer px={7} />

        <Typography variant="caption">
          ※ファイル形式はPDF(.pdf)、Word(.docx)、Excel(.xlsx)、PowerPoint(.pptx)、テキスト(.txt)のみ対応しています。
          <br />
          ※最大10ファイルまで一度にアップロードできます。
        </Typography>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="追加" />
    </form>
  );
};
