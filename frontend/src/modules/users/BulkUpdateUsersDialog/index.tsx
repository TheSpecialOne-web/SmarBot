import { Box, Stack, Typography } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { FileInput } from "@/components/inputs/FileInput";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useBulkUpdateUsers } from "@/orval/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

type FileUploadForm = {
  file: File | null;
};

export const BulkUpdateUsersDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: bulkUpdateUsers } = useBulkUpdateUsers();
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
      await bulkUpdateUsers({ file });
      reset();
      setValue("file", null);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ユーザーを一括更新しました。" });
    } catch (error) {
      const errMsg = getErrorMessage(error);
      enqueueErrorSnackbar({ message: errMsg || "ユーザーの一括更新に失敗しました。" });
    }
  };

  return (
    <CustomDialog open={open} onClose={onClose} title="ユーザー一括編集" maxWidth="md">
      <form noValidate onSubmit={handleSubmit(onSubmit)}>
        <CustomDialogContent>
          <Stack gap={2}>
            <Box>
              <Typography variant="body2">
                ・CSVファイルの列名には「名前, メールアドレス, 役割, グループ1, グループ2,
                グループ3, ...」を指定します。
                <br />
                ・入力された「メールアドレス」のユーザーに対して、名前、役割、所属グループが変更されます。
                <br />
                ・「メールアドレス」は変更することができず、一意である必要があります。
                <br />
                ・「役割」は「組織管理者」または「一般ユーザー」を指定します。
                <br />
                ・指定できるグループ数の上限は100個です。
                <br />
                ・CSVファイルには最大300行のデータを含めることができます。
                <Typography component="span" variant="h4" display="block" mt={1}>
                  注意点
                </Typography>
                ・存在しないグループ名が含まれている場合、エラーが返されます。
                <br />
                ・存在しないメールアドレスが含まれている場合、エラーは返されませんが、新しいユーザーの作成は行われません。
              </Typography>
            </Box>
            <FileInput file={selectedFile} onChange={handleChangeFile} />
          </Stack>
        </CustomDialogContent>
        <CustomDialogAction onClose={onClose} buttonText="送信" loading={isSubmitting} />
      </form>
    </CustomDialog>
  );
};
