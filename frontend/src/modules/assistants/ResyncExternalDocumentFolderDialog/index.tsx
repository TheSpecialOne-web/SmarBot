import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useResyncExternalDocumentFolder } from "@/orval/backend-api";
import { Bot, DocumentFolder } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  documentFolder: DocumentFolder;
  bot: Bot;
  onClose: () => void;
  refetch: () => void;
};

export const ResyncExternalDocumentFolderDialog = ({
  open,
  documentFolder,
  bot,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: resyncDocumentFolder, isMutating } = useResyncExternalDocumentFolder(
    bot.id,
    documentFolder.id,
  );

  const onResyncExternalDocumentFolder = async () => {
    try {
      await resyncDocumentFolder();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "フォルダの再同期を開始しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの再同期に失敗しました。" });
    }
  };

  const resyncDialogContents = (
    <Typography>
      外部データ連携フォルダ
      <Typography component="span" fontWeight="bold" px={0.5}>
        {documentFolder.name}
      </Typography>
      を再同期してもよろしいですか？
      <Spacer px={8} />
      <Typography variant="caption" component="span">
        ※OCR機能が有効な場合には、更新・追加されたファイルに対するデータ学習による消費トークンが発生します。
      </Typography>
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="外部データ連携フォルダの再同期"
      color="info"
      content={resyncDialogContents}
      buttonText="再同期"
      onSubmit={onResyncExternalDocumentFolder}
      isLoading={isMutating}
    />
  );
};
