import {
  Autocomplete,
  Box,
  Button,
  Grid,
  InputLabel,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers";
import dayjs, { Dayjs } from "dayjs";
import { SyntheticEvent, useState } from "react";

import { ContentHeader } from "@/components/headers/ContentHeader";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { downloadConversations, useGetBots, useGetUsers } from "@/orval/backend-api";
import { Bot, BotStatus, User } from "@/orval/models/backend-api";
import { downloadFile } from "@/utils/downloadFile";

const initialOption = { id: "all", name: "全て" } as const;
type BotAutoCompleteOption = Bot | typeof initialOption;
type UserAutoCompleteOption = User | typeof initialOption;

export const DownloadConversation = () => {
  const {
    enqueueErrorSnackbar,
    enqueueLoadingSnackbar,
    enqueueSuccessSnackbar,
    closeEnqueuedSnackbar,
  } = useCustomSnackbar();

  const [selectedBotId, setSelectedBotId] = useState<string>(initialOption.id);
  const [selectedUserId, setSelectedUserId] = useState<string>(initialOption.id);
  const [startDate, setStartDate] = useState(dayjs());
  const [endDate, setEndDate] = useState(dayjs());

  const {
    data: botsData,
    error: getBotsError,
    isLoading: isLoadingFetchBots,
  } = useGetBots({ status: [BotStatus.active, BotStatus.archived] });
  const { data: usersData, error: getUsersError, isLoading: isLoadingFetchUsers } = useGetUsers();

  if (getBotsError || getUsersError) {
    const errMsg = getErrorMessage(getBotsError || getUsersError);
    enqueueErrorSnackbar({ message: errMsg || "データの取得に失敗しました。" });
  }

  const bots = botsData ? botsData.bots : [];
  const users = usersData?.users ?? [];

  const handleDownload = async () => {
    const loadingSnackbar = enqueueLoadingSnackbar({
      message: "会話履歴をダウンロードしています。",
    });
    try {
      const data = await downloadConversations({
        start_date_time: startDate.startOf("day").toISOString(),
        end_date_time: endDate.startOf("day").add(1, "day").startOf("day").toISOString(),
        bot_id: selectedBotId === initialOption.id ? undefined : Number(selectedBotId),
        user_id: selectedUserId === initialOption.id ? undefined : Number(selectedUserId),
      });
      const currentDate = dayjs().format("YYYYMMDDHHmm");
      downloadFile(`会話履歴_${currentDate}.csv`, data);
      enqueueSuccessSnackbar({ message: "会話履歴をダウンロードしました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "会話履歴のダウンロードに失敗しました。" });
    } finally {
      closeEnqueuedSnackbar(loadingSnackbar);
    }
  };

  const isLoading = isLoadingFetchBots || isLoadingFetchUsers;

  const isLongTerm = endDate.diff(startDate, "month") >= 3;

  const botAutoCompleteOptions = [initialOption, ...bots];
  const handleBotAutoCompleteChange = (_: SyntheticEvent, value: BotAutoCompleteOption | null) => {
    setSelectedBotId(value?.id.toString() || initialOption.id);
  };

  const userAutoCompleteOptions = [initialOption, ...users];
  const handleUserAutoCompleteChange = (
    _: SyntheticEvent,
    value: UserAutoCompleteOption | null,
  ) => {
    setSelectedUserId(value?.id.toString() || initialOption.id);
  };

  return (
    <Box>
      <ContentHeader>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          会話履歴のダウンロード
        </Typography>
      </ContentHeader>
      <Paper
        sx={{
          px: 2,
          pt: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={3}>
            <InputLabel>基盤モデルまたはアシスタント</InputLabel>
            <Autocomplete<BotAutoCompleteOption>
              value={
                botAutoCompleteOptions.find(value => value.id.toString() === selectedBotId) ||
                initialOption
              }
              onChange={handleBotAutoCompleteChange}
              options={botAutoCompleteOptions}
              getOptionLabel={option => option.name}
              renderInput={params => <TextField {...params} size="small" />}
              fullWidth
              size="small"
            />
            <Spacer px={24} />
          </Grid>
          <Grid item xs={3}>
            <InputLabel>ユーザー</InputLabel>
            <Autocomplete<UserAutoCompleteOption>
              value={
                userAutoCompleteOptions.find(value => value.id.toString() === selectedUserId) ||
                initialOption
              }
              onChange={handleUserAutoCompleteChange}
              options={userAutoCompleteOptions}
              getOptionLabel={option => option.name}
              renderInput={params => <TextField {...params} size="small" />}
              fullWidth
              size="small"
            />
            <Spacer px={24} />
          </Grid>
          <Grid item xs={4}>
            <InputLabel>期間選択</InputLabel>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <DatePicker
                format="MM/DD"
                value={startDate}
                maxDate={endDate}
                onChange={(date: Dayjs | null) => date && setStartDate(date)}
                sx={{
                  ".MuiInputBase-input": {
                    padding: 1,
                  },
                }}
              />
              <Typography>〜</Typography>
              <DatePicker
                format="MM/DD"
                value={endDate}
                minDate={startDate}
                maxDate={dayjs()}
                onChange={(date: Dayjs | null) => date && setEndDate(date)}
                sx={{
                  ".MuiInputBase-input": {
                    padding: 1,
                  },
                }}
              />
            </Stack>
            {isLongTerm ? (
              <Typography variant="caption" color="error">
                3ヶ月を超える期間は選択できません
              </Typography>
            ) : (
              <Spacer px={24} />
            )}
          </Grid>
          <Grid xs={2} item ml="auto">
            <Button
              variant="contained"
              fullWidth
              onClick={handleDownload}
              sx={{
                height: 40,
              }}
              disabled={isLoading || isLongTerm}
            >
              ダウンロード
            </Button>
            <Spacer px={24} />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};
