import { Box, Stack, Typography } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { FileInput } from "@/components/inputs/FileInput";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useBulkCreateUsers } from "@/orval/backend-api";
import { downloadFile } from "@/utils/downloadFile";

import { bulkCreateUsersSampleCSV } from "./bulkCreateUsersSampleCSV";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

type FileUploadForm = {
  file: File | null;
};

export const BulkCreateUsersDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: bulkCreateUsers } = useBulkCreateUsers();
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
      await bulkCreateUsers({ file });
      reset();
      setValue("file", null);
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "ユーザーを一括作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ユーザーの一括作成に失敗しました。" });
    }
  };

  const downloadSampleCsv = () => {
    // CSVのStringをBlobオブジェクトに変換
    const sampleBulkCreateUsersBlob = new Blob([bulkCreateUsersSampleCSV], { type: "text/csv" });
    downloadFile("ユーザー一括作成サンプル.csv", sampleBulkCreateUsersBlob);
    enqueueSuccessSnackbar({
      message: "ユーザー一括作成サンプルの、CSV形式でのエクスポートが完了しました。",
    });
  };

  return (
    <CustomDialog open={open} maxWidth="md" onClose={onClose} title="ユーザー一括追加">
      <form noValidate onSubmit={handleSubmit(onSubmit)}>
        <CustomDialogContent>
          <Stack gap={2}>
            <Box>
              <Typography variant="body2">
                ・CSVファイルの列名には「名前, メールアドレス, 役割, グループ1, グループ2,
                グループ3, ...」を指定します。
                <br />
                ・指定された情報でユーザーが作成され、指定されたグループに追加されます。
                <br />
                ・「メールアドレス」は一意でなければなりません。
                <br />
                ・「役割」は「組織管理者」または「一般ユーザー」を指定します。
                <br />
                ・指定できるグループ数の上限は100個です。
                <br />
                ・CSVファイルには最大300行のデータを含めることができます。
                <Typography component="span" variant="h4" display="block" mt={1}>
                  注意点
                </Typography>
                <Typography variant="body2" fontWeight={700} display="block">
                  ・一括追加したユーザーの反映にはしばらく時間がかかります。30分間は同じユーザーを重複して追加しないでください。
                </Typography>
                ・同じユーザーを短時間に複数回追加すると、正しく追加できない場合があります。
                <br />
                ・存在しないグループ名が含まれている場合、エラーが返されます。
                <br />
                ・既に同じメールアドレスを持つユーザーが存在する場合、エラーが返されます。
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2">
                ユーザー一括追加のサンプルCSVを
                <Typography
                  component="span"
                  variant="body2"
                  color="primary"
                  onClick={downloadSampleCsv}
                  sx={{
                    "&:hover": {
                      cursor: "pointer",
                    },
                  }}
                >
                  ダウンロード
                </Typography>
                する
              </Typography>
            </Box>
            <FileInput file={selectedFile} onChange={handleChangeFile} />
          </Stack>
        </CustomDialogContent>
        <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="送信" />
      </form>
    </CustomDialog>
  );
};
