import { InputLabel, MenuItem, Select, SelectChangeEvent, Stack, Typography } from "@mui/material";
import dayjs, { ManipulateType } from "dayjs";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { isAssistant } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { BotProfile } from "@/modules/tenant-settings/BotProfile";
import { useGetBots } from "@/orval/backend-api";
import { Bot, BotStatus } from "@/orval/models/backend-api";
import { CreateApiKeyParam } from "@/orval/models/backend-api";

type Props = {
  onSubmit: (params: CreateApiKeyParam) => void;
  onClose: () => void;
};

const TIME_SHIFT_FACTOR = 24 - 9;

type ExpirationTimeSpanValue = "1-month" | "3-month" | "6-month" | "1-year" | "no-expiration";

type ExpirationTimeSpan = Readonly<{
  value: ExpirationTimeSpanValue;
  label: string;
}>;

const EXPIRATION_TIME_SPANS: ReadonlyArray<ExpirationTimeSpan> = [
  { value: "1-month", label: "1か月" },
  { value: "3-month", label: "3か月" },
  { value: "6-month", label: "6か月" },
  { value: "1-year", label: "1年" },
  { value: "no-expiration", label: "無期限" },
] as const;

const filterAssistant = (bots: Bot[]) => {
  return bots.filter(bot => {
    return isAssistant(bot);
  });
};

export const CreateApiKeyForm = ({ onSubmit, onClose }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const { data: botsData, error: getBotsError } = useGetBots({
    status: [BotStatus.active],
  });

  if (getBotsError) {
    const errMsg = getErrorMessage(getBotsError);
    enqueueErrorSnackbar({ message: errMsg || "データの取得に失敗しました。" });
  }
  const [previousName, setPreviousName] = useState<string>("");

  const assistants = filterAssistant(botsData?.bots ?? []);

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { isSubmitting },
  } = useForm<CreateApiKeyParam>({
    defaultValues: {
      bot_id: undefined,
      name: "",
      expires_at: dayjs()
        .startOf("day")
        .add(TIME_SHIFT_FACTOR, "hour")
        .add(1, "month")
        .format("YYYY-MM-DD HH:mm"),
    },
  });

  const expiresAt = dayjs(watch("expires_at"));

  const [selectedSpan, setSelectedSpan] = useState<ExpirationTimeSpanValue>("1-month");

  const handleChange = (event: SelectChangeEvent) => {
    const selectedSpan = event.target.value as ExpirationTimeSpanValue;
    setSelectedSpan(selectedSpan);

    if (selectedSpan === "no-expiration") {
      setValue("expires_at", undefined);
      return;
    }

    const [value, unit] = selectedSpan.split("-");

    const newExpiration = dayjs()
      .startOf("day")
      .add(TIME_SHIFT_FACTOR, "hour")
      .add(parseInt(value), unit as ManipulateType)
      .format("YYYY-MM-DD HH:mm");
    setValue("expires_at", newExpiration);
  };

  const onChangeAssistant = (event: SelectChangeEvent<unknown>) => {
    const selectedBotId = event.target.value;
    if (typeof selectedBotId !== "number") return;
    setValue("bot_id", selectedBotId);

    // 選択されたアシスタントの名前を自動入力
    const selectedBot = assistants.find(assistant => assistant.id === selectedBotId);
    if (!selectedBot) return;
    if (!watch("name") || previousName === watch("name")) {
      const name = `${selectedBot.name}のAPIキー`;
      setValue("name", name);
      setPreviousName(name);
    }
  };

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack gap={2}>
          <CustomFormSelect
            name="bot_id"
            label="アシスタント"
            fullWidth
            control={control}
            rules={{ required: "アシスタントは必須です。" }}
            onChange={onChangeAssistant}
          >
            {assistants.map(assistant => (
              <MenuItem key={assistant.id} value={assistant.id}>
                <BotProfile bot={assistant} />
              </MenuItem>
            ))}
          </CustomFormSelect>
          <CustomTextField
            name="name"
            label="名前"
            fullWidth
            control={control}
            rules={{ required: "名前は必須です。" }}
          />
          <Stack>
            <InputLabel sx={{ fontSize: 14 }}>有効期限</InputLabel>
            <Stack direction="row" gap={2} alignItems={"center"}>
              <Select<ExpirationTimeSpanValue>
                value={selectedSpan}
                onChange={handleChange}
                sx={{
                  ".MuiInputBase-input": {
                    paddingY: 1,
                  },
                }}
              >
                {EXPIRATION_TIME_SPANS.map(span => (
                  <MenuItem key={span.label} value={span.value}>
                    {span.label}
                  </MenuItem>
                ))}
              </Select>

              {watch("expires_at") && (
                <Typography variant="subtitle2" color={"grey.700"}>
                  {expiresAt.format("YYYY年MM月DD日まで")}
                </Typography>
              )}
            </Stack>
          </Stack>
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="作成" loading={isSubmitting} />
    </form>
  );
};
