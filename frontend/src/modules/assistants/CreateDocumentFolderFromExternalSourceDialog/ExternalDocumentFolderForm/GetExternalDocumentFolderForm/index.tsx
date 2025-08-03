import { LoadingButton } from "@mui/lab";
import { Stack } from "@mui/material";
import { useForm } from "react-hook-form";
import { useAsyncFn } from "react-use";

import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { getExternalDocumentFoldersSync } from "@/orval/backend-api";
import {
  DocumentFolder,
  ExternalDataConnectionType,
  GetExternalDocumentFoldersSyncParams,
} from "@/orval/models/backend-api";

const sharedUrlTooltip = {
  [ExternalDataConnectionType.sharepoint]:
    "同期したいSharePointフォルダのページ上の「URLのコピー」ボタンをクリックしてコピーした共有URLを入力してください。",
  [ExternalDataConnectionType.box]:
    "同期したいBoxフォルダのページで「共有」ボタンをクリックして共有URLをコピーして入力してください。",
  [ExternalDataConnectionType.google_drive]: undefined,
};

type Props = {
  externalDataConnectionType: ExternalDataConnectionType;
  botId: number;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  setFolderName: (name: string) => void;
  setExternalId: (externalId: string) => void;
};

export const GetExternalDocumentFolderForm = ({
  externalDataConnectionType,
  botId,
  parentDocumentFolderId,
  setFolderName,
  setExternalId,
}: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const { control, handleSubmit } = useForm<GetExternalDocumentFoldersSyncParams>({
    defaultValues: {
      external_data_connection_type: externalDataConnectionType,
      parent_document_folder_id: parentDocumentFolderId ?? undefined,
    },
  });

  const [onSubmitGetExternalDocumentFolderToSyncState, onSubmitGetExternalDocumentFolderToSync] =
    useAsyncFn(async (params: GetExternalDocumentFoldersSyncParams) => {
      try {
        const { external_id, is_valid, name } = await getExternalDocumentFoldersSync(botId, params);
        if (!is_valid) {
          enqueueErrorSnackbar({ message: `フォルダ名が重複しています: ${name}` });
          return;
        }
        setFolderName(name);
        setExternalId(external_id);
      } catch (e) {
        const errMsg = getErrorMessage(e);
        enqueueErrorSnackbar({ message: errMsg || "フォルダの取得に失敗しました。" });
      }
    });

  return (
    <form onSubmit={handleSubmit(onSubmitGetExternalDocumentFolderToSync)}>
      <CustomTextField
        name="external_data_shared_url"
        label="共有URL"
        tooltip={sharedUrlTooltip[externalDataConnectionType]}
        fullWidth
        variant="outlined"
        control={control}
        defaultValue=""
      />
      <Spacer px={8} />
      <Stack direction="row" justifyContent="flex-end">
        <LoadingButton
          type="submit"
          variant="contained"
          color="primary"
          onClick={handleSubmit(onSubmitGetExternalDocumentFolderToSync)}
          loading={onSubmitGetExternalDocumentFolderToSyncState.loading}
        >
          同期するフォルダを取得
        </LoadingButton>
      </Stack>
    </form>
  );
};
