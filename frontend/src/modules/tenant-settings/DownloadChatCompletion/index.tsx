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
import { downloadChatCompletions, useGetApiKeys, useGetBots } from "@/orval/backend-api";
import { ApiKey, Bot, BotStatus } from "@/orval/models/backend-api";
import { downloadFile } from "@/utils/downloadFile";

const initialOption = { id: "all", name: "全て" };
type BotAutoCompleteOption = Bot | typeof initialOption;
type ApiKeyAutoCompleteOption = ApiKey | typeof initialOption;

export const DownloadChatCompletion = () => {
  const {
    enqueueErrorSnackbar,
    enqueueLoadingSnackbar,
    enqueueSuccessSnackbar,
    closeEnqueuedSnackbar,
  } = useCustomSnackbar();

  const [selectedBotId, setSelectedBotId] = useState(initialOption.id);
  const [selectedApiKeyId, setSelectedApiKeyId] = useState(initialOption.id);
  const [startDate, setStartDate] = useState<Dayjs>(dayjs());
  const [endDate, setEndDate] = useState<Dayjs>(dayjs());

  const {
    data: botsData,
    error: getBotsError,
    isLoading: isLoadingFetchBots,
  } = useGetBots({ status: [BotStatus.active, BotStatus.archived] });

  const {
    data: apiKeysData,
    error: getApiKeysError,
    isLoading: isLoadingFetchApiKeys,
  } = useGetApiKeys();

  if (getBotsError || getApiKeysError) {
    const errMsg = getErrorMessage(getBotsError || getApiKeysError);
    enqueueErrorSnackbar({ message: errMsg || "情報の取得に失敗しました。" });
  }

  const bots = botsData ? botsData.bots : [];
  const apiKeys = apiKeysData?.api_keys ?? [];

  const selectableBots = bots.filter(bot => apiKeys.some(apiKey => apiKey.bot.id === bot.id));
  const selectableApiKeys = apiKeys.filter(
    apiKey => selectedBotId === "all" || apiKey.bot.id === Number(selectedBotId),
  );

  const handleDownload = async () => {
    const loadingSnackbar = enqueueLoadingSnackbar({
      message: "API連携の会話履歴をダウンロードしています。",
    });
    try {
      const data = await downloadChatCompletions({
        start_date_time: startDate.startOf("day").toISOString(),
        end_date_time: endDate.startOf("day").add(1, "day").toISOString(),
        bot_id: selectedBotId === "all" ? undefined : Number(selectedBotId),
        api_key_id: selectedApiKeyId === "all" ? undefined : selectedApiKeyId,
      });
      const currentDate = dayjs().format("YYYYMMDDHHmm");
      downloadFile(`API連携_会話履歴_${currentDate}.csv`, data);
      enqueueSuccessSnackbar({ message: "API連携の会話履歴をダウンロードしました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "API連携の会話履歴のダウンロードに失敗しました。",
      });
    } finally {
      closeEnqueuedSnackbar(loadingSnackbar);
    }
  };

  const isLoading = isLoadingFetchBots || isLoadingFetchApiKeys;

  const isLongTerm = endDate.diff(startDate, "month") >= 3;

  const botAutoCompleteOptions = [initialOption, ...selectableBots];
  const handleSelectBot = (_: SyntheticEvent, value: BotAutoCompleteOption | null) => {
    setSelectedBotId(value?.id.toString() ?? initialOption.id);
    // botを選択した際にapiキーを全て選択する
    setSelectedApiKeyId(initialOption.id);
  };

  const apiKeyAutoCompleteOptions = [initialOption, ...selectableApiKeys];
  const handleSelectApiKey = (_: SyntheticEvent, value: ApiKeyAutoCompleteOption | null) => {
    setSelectedApiKeyId(value?.id ?? initialOption.id);
    if (value?.id === initialOption.id) {
      return;
    }
    // apiキーを選択した際にbotも選択する
    const bot = apiKeys.find(apiKey => apiKey.id === value?.id)?.bot;
    if (bot) {
      setSelectedBotId(bot.id.toString());
    }
  };

  return (
    <Box>
      <ContentHeader>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          API連携の会話履歴のダウンロード
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
            <InputLabel>アシスタント</InputLabel>
            <Autocomplete<BotAutoCompleteOption>
              options={botAutoCompleteOptions}
              value={
                botAutoCompleteOptions.find(option => option.id.toString() === selectedBotId) ||
                initialOption
              }
              getOptionLabel={option => option.name}
              onChange={handleSelectBot}
              fullWidth
              size="small"
              renderInput={params => <TextField {...params} size="small" />}
            />
            <Spacer px={24} />
          </Grid>
          <Grid item xs={3}>
            <InputLabel>APIキー</InputLabel>
            <Autocomplete<ApiKeyAutoCompleteOption>
              options={apiKeyAutoCompleteOptions}
              value={
                apiKeyAutoCompleteOptions.find(option => option.id === selectedApiKeyId) ||
                initialOption
              }
              getOptionLabel={option => option.name}
              onChange={handleSelectApiKey}
              fullWidth
              size="small"
              renderInput={params => <TextField {...params} size="small" />}
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
