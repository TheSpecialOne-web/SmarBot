import FolderIcon from "@mui/icons-material/Folder";
import { LoadingButton } from "@mui/lab";
import { MenuItem, Stack, Typography } from "@mui/material";
import { TimePicker } from "@mui/x-date-pickers";
import dayjs, { Dayjs } from "dayjs";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { DayOfWeek, dayOfWeekLabels, scheduleToCron, SyncSchedule } from "@/libs/externalSync";
import { useStartExternalDataConnection } from "@/orval/backend-api";
import { DocumentFolder, ExternalDataConnectionType } from "@/orval/models/backend-api";

type Props = {
  externalDataConnectionType: ExternalDataConnectionType;
  botId: number;
  parentDocumentFolderId: DocumentFolder["id"] | null;
  folderName: string;
  externalId: string;
  refetch: () => void;
  onClose: () => void;
};

export const StartExternalDataSyncForm = ({
  externalDataConnectionType,
  botId,
  parentDocumentFolderId,
  folderName,
  externalId,
  refetch,
  onClose,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const [syncTime, setSyncTime] = useState<Dayjs>(dayjs().hour(0).minute(0));

  const {
    control,
    getValues: getSyncScheduleValues,
    handleSubmit,
    setValue,
  } = useForm<SyncSchedule>({
    defaultValues: {
      syncFrequencyWeek: 1,
      syncDay: DayOfWeek.Saturday,
      syncHour: 0,
    },
  });

  const { trigger: startExternalDataConnection, isMutating: isLoading } =
    useStartExternalDataConnection(botId);

  const onSubmit = async () => {
    const syncSchedule = getSyncScheduleValues();
    const cron = scheduleToCron(syncSchedule);
    try {
      await startExternalDataConnection({
        external_data_connection_type: externalDataConnectionType,
        external_id: externalId,
        parent_document_folder_id: parentDocumentFolderId ?? undefined,
        sync_schedule: cron,
      });
      enqueueSuccessSnackbar({ message: "連携を開始しました。" });
      refetch();
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg ?? "連携の開始に失敗しました。" });
    }
  };

  return (
    <>
      <Stack direction="row" alignItems="center" spacing={1}>
        <FolderIcon />
        <Typography variant="h5">{folderName}</Typography>
      </Stack>
      <Spacer px={16} />
      <Typography variant="h6">外部ソースからデータを同期するスケジュールの設定</Typography>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack spacing={1} p={1}>
          <CustomTextField
            control={control}
            name="syncFrequencyWeek"
            label="同期の頻度 (週間)"
            type="number"
            rules={{
              min: { value: 1, message: "1以上4以下の数値を入力してください。" },
              max: { value: 4, message: "1以上4以下の数値を入力してください。" },
              required: "同期の頻度は必須です。",
            }}
            tooltip="OCR機能が有効な場合には、同期のたびに更新・追加されたファイルに対するデータ学習による消費トークンが発生します。"
          />
          <CustomFormSelect
            control={control}
            name="syncDay"
            label="同期する曜日/時間"
            tooltip="同期のタイミングは、ユーザー利用に影響のない曜日/時間の設定を推奨いたします。"
            rules={{ required: "同期する曜日は必須です。" }}
          >
            {Object.entries(DayOfWeek).map(([key, value]) => (
              <MenuItem key={key} value={value}>
                {dayOfWeekLabels[value]}
              </MenuItem>
            ))}
          </CustomFormSelect>
          <TimePicker
            value={syncTime}
            onChange={newValue => {
              if (!newValue) {
                return;
              }
              setSyncTime(newValue);
              setValue("syncHour", newValue.hour());
            }}
            views={["hours"]}
            slotProps={{
              textField: {
                size: "small",
              },
            }}
          />
        </Stack>
        <Stack direction="row" justifyContent="flex-end">
          <LoadingButton
            variant="contained"
            onClick={handleSubmit(onSubmit)}
            loading={isLoading}
            type="submit"
          >
            連携を開始
          </LoadingButton>
        </Stack>
      </form>
    </>
  );
};
