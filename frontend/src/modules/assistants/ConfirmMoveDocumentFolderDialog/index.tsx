import { Stack, Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useMoveDocumentFolder } from "@/orval/backend-api";
import {
  Bot,
  DocumentFolder,
  DocumentFolderDetail,
  MoveDocumentFolderParam,
} from "@/orval/models/backend-api";

import { DocumentFolderPaths } from "../DocumentManagement/DocumentFolderPaths";

type Props = {
  bot: Bot;
  open: boolean;
  targetDocumentFolder: DocumentFolder;
  currentParentDocumentFolderDetail: DocumentFolderDetail;
  newParentDocumentFolderDetail: DocumentFolderDetail;
  isLoading: boolean;
  onCloseConfirmDialog: () => void;
  onCloseTableDialog: () => void;
  refetch: () => void;
};

export const ConfirmMoveDocumentFolderDialog = ({
  bot,
  open,
  targetDocumentFolder,
  currentParentDocumentFolderDetail,
  newParentDocumentFolderDetail,
  isLoading,
  onCloseConfirmDialog,
  onCloseTableDialog,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useMoveDocumentFolder(bot.id, targetDocumentFolder.id);

  const handleMoveDocumentFolder = async (param: MoveDocumentFolderParam) => {
    try {
      await trigger(param);
      refetch();
      onCloseConfirmDialog();
      onCloseTableDialog();
      enqueueSuccessSnackbar({ message: "フォルダを移動しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "フォルダの移動に失敗しました。" });
    }
  };

  const dialogContent = isLoading ? (
    <CircularLoading />
  ) : (
    <Stack direction="column" gap={2} alignItems="center">
      <Typography>
        <Typography component="span" fontWeight="bold">
          {targetDocumentFolder.name}
        </Typography>
        を移動してもよろしいですか？
      </Typography>
      <Stack direction="column" alignItems="flex-start" gap={0.5}>
        <Stack direction="row" alignItems="center" gap={1}>
          <Typography variant="h5">現在のフォルダ：</Typography>
          <DocumentFolderPaths documentFolderDetail={currentParentDocumentFolderDetail} />
        </Stack>
        <Stack direction="row" alignItems="center" gap={1}>
          <Typography variant="h5">移動先フォルダ：</Typography>
          <DocumentFolderPaths documentFolderDetail={newParentDocumentFolderDetail} />
        </Stack>
      </Stack>
      <Typography variant="caption">
        ※ フォルダを移動すると、フォルダ内のサブフォルダとファイルも同時に移動されます。
        <br />※ ファイルの移動処理には時間がかかる場合があります。
      </Typography>
    </Stack>
  );

  return (
    <ConfirmDialog
      title="移動先の確認"
      color="info"
      open={open}
      onClose={onCloseConfirmDialog}
      content={dialogContent}
      buttonText="移動"
      onSubmit={() =>
        handleMoveDocumentFolder({
          new_parent_document_folder_id: newParentDocumentFolderDetail.id,
        })
      }
      isLoading={isMutating}
    />
  );
};
