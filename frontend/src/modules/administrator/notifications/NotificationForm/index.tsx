import { InputLabel, MenuItem, Stack, Typography } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers";
import dayjs, { Dayjs } from "dayjs";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import {
  CreateNotificationParam,
  RecipientType,
  UpdateNotificationParam,
} from "@/orval/models/administrator-api";

type Props = {
  onSubmit: (params: CreateNotificationParam | UpdateNotificationParam) => void;
  onClose: () => void;
  notification: CreateNotificationParam | UpdateNotificationParam | null;
};

export const NotificationForm = ({ onSubmit, onClose, notification }: Props) => {
  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { isSubmitting },
  } = useForm<CreateNotificationParam | UpdateNotificationParam>({
    defaultValues: {
      title: notification?.title || "",
      content: notification?.content || "",
      start_date: notification
        ? dayjs(notification.start_date).format("YYYY-MM-DD")
        : dayjs().format("YYYY-MM-DD"),
      end_date: notification
        ? dayjs(notification.end_date).format("YYYY-MM-DD")
        : dayjs().add(1, "day").format("YYYY-MM-DD"),
      recipient_type: notification?.recipient_type || RecipientType.user,
    },
  });

  const startDate = dayjs(watch("start_date"));
  const endDate = dayjs(watch("end_date"));

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack gap={2}>
          <CustomTextField
            name="title"
            label="タイトル"
            fullWidth
            control={control}
            rules={{ required: "タイトルは必須です。" }}
          />
          <CustomTextField
            name="content"
            label="内容"
            fullWidth
            multiline
            rows={8}
            control={control}
            rules={{ required: "内容は必須です。" }}
          />
          <CustomFormSelect
            name="recipient_type"
            label="受信者タイプ"
            fullWidth
            control={control}
            defaultValue={RecipientType.user}
          >
            <MenuItem value={RecipientType.user}>ユーザー</MenuItem>
            <MenuItem value={RecipientType.admin}>組織管理者</MenuItem>
          </CustomFormSelect>
          <Stack>
            <InputLabel>期間選択</InputLabel>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <DatePicker
                format="YYYY-MM-DD"
                disabled={Boolean(notification?.start_date)}
                value={startDate}
                minDate={dayjs()}
                onChange={(date: Dayjs | null) => {
                  if (date) {
                    setValue("start_date", date.format("YYYY-MM-DD"));
                  }
                }}
                sx={{
                  ".MuiInputBase-input": {
                    padding: 1,
                  },
                }}
              />
              <Typography>〜</Typography>
              <DatePicker
                format="YYYY-MM-DD"
                value={endDate}
                minDate={startDate.add(1, "day")}
                onChange={(date: Dayjs | null) => {
                  if (date) {
                    setValue("end_date", date.format("YYYY-MM-DD"));
                  }
                }}
                sx={{
                  ".MuiInputBase-input": {
                    padding: 1,
                  },
                }}
              />
            </Stack>
          </Stack>
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
