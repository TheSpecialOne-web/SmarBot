import { Box, Stack, Typography } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { FileInput } from "@/components/inputs/FileInput";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useBulkCreateOrUpdateQuestionAnswers } from "@/orval/backend-api";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  botId: Bot["id"];
};

type FileUploadForm = {
  file: File | null;
};

export const BulkCreateOrUpdateQuestionAnswersDialog = ({
  open,
  onClose,
  refetch,
  botId,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: bulkCreateOrUpdateQuestionAnswers } =
    useBulkCreateOrUpdateQuestionAnswers(botId);

  const {
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { isSubmitting },
  } = useForm<FileUploadForm>({
    defaultValues: {
      file: null,
    },
  });

  const selectedFile = watch("file");

  const handleChangeFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValue("file", null);

    if (!event.target.files || event.target.files.length === 0) return;
    const file = Array.from(event.target.files).at(0);
    if (!file) return;
    setValue("file", file);
  };

  const onSubmit = async ({ file }: FileUploadForm) => {
    if (!file) return;

    try {
      await bulkCreateOrUpdateQuestionAnswers({ file });
      reset();
      setValue("file", null);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "FAQを一括追加しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "FAQの一括追加に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="FAQの一括追加" maxWidth="md">
      <form noValidate onSubmit={handleSubmit(onSubmit)}>
        <CustomDialogContent>
          <Stack gap={2}>
            <Box>
              <Typography variant="body2">
                ・CSVファイルの列名には「質問, 回答」を指定します。
                <br />
                ・指定された情報でFAQが作成されます。
                <br />
                ・「質問」は一意でなければなりません。
                <br />
                ・CSVファイルには最大300行のデータを含めることができます。
                <Spacer px={4} />
                <Typography variant="h6">注意点</Typography>
                ・CSVファイル内に同一の質問が複数回含まれる場合、エラーが返されます。
                <br />
                ・既に同じ質問を持つFAQが存在する場合、そのFAQの内容は上書きされます。
                <br />
                ・処理中のFAQを上書きすることはできません。
                <br />
                ・FAQが反映されるまでに数分かかる場合があります。
              </Typography>
            </Box>

            <FileInput file={selectedFile} onChange={handleChangeFile} />
          </Stack>
        </CustomDialogContent>
        <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="追加" />
      </form>
    </CustomDialog>
  );
};
