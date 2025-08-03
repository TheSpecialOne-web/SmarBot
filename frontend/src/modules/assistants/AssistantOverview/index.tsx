import { Box, Divider, Paper, Skeleton, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { modelNames } from "@/const/modelFamily";
import { getPdfParserLabel, isUrsaBot } from "@/libs/bot";
import { displaySearchMethodForUser } from "@/libs/searchMethod";
import { Approach, Bot } from "@/orval/models/backend-api";

type Props = {
  selectedBot: Bot;
  isLoadingSelectBot: boolean;
  isEditButtonVisible?: boolean;
  refetch: () => void;
  enableDocumentIntelligence: boolean;
};

export const AssistantOverview = ({
  selectedBot,
  isLoadingSelectBot,
  isEditButtonVisible = false,
  refetch,
  enableDocumentIntelligence,
}: Props) => {
  const navigate = useNavigate();
  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">概要</Typography>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetch} />
            {isEditButtonVisible && (
              <PrimaryButton
                text={<Typography variant="button">編集</Typography>}
                disabled={isUrsaBot(selectedBot)}
                onClick={() => navigate("edit")}
              />
            )}
          </Stack>
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          padding: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Box sx={{ display: "flex", flexGrow: 1 }}>
          <Stack flex={1} spacing={2}>
            <Box>
              <Typography variant="h5" gutterBottom>
                アイコン
              </Typography>
              <Box sx={{ px: 0.75 }}>
                <AssistantAvatar
                  size={45}
                  iconUrl={selectedBot.icon_url}
                  iconColor={selectedBot.icon_color}
                />
              </Box>
            </Box>
            <Box>
              <Typography variant="h5" gutterBottom>
                名前
              </Typography>
              {isLoadingSelectBot ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography pl={1}>{selectedBot.name}</Typography>
              )}
            </Box>
            <Box>
              <Typography variant="h5" gutterBottom>
                説明
              </Typography>
              {isLoadingSelectBot ? (
                <Skeleton animation="pulse" variant="text" width="80%" height={30} />
              ) : (
                <Typography
                  px={1}
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {selectedBot.description}
                </Typography>
              )}
            </Box>
            {!isUrsaBot(selectedBot) && (
              <>
                <Box>
                  <Typography variant="h5" gutterBottom>
                    モデル
                  </Typography>
                  {isLoadingSelectBot ? (
                    <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                  ) : (
                    <Typography pl={1}>{modelNames[selectedBot.model_family]}</Typography>
                  )}
                </Box>
                <Box>
                  <Typography variant="h5" gutterBottom>
                    ドキュメントの参照
                  </Typography>
                  {isLoadingSelectBot ? (
                    <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                  ) : (
                    <Typography pl={1}>
                      {selectedBot.approach == Approach.neollm ? "有効" : "無効"}
                    </Typography>
                  )}
                </Box>
                {selectedBot.approach === Approach.neollm && (
                  <>
                    <Box>
                      <Typography variant="h5" gutterBottom>
                        関連する質問の生成
                      </Typography>
                      {isLoadingSelectBot ? (
                        <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                      ) : (
                        <Typography pl={1}>
                          {selectedBot.enable_follow_up_questions ? "有効" : "無効"}
                        </Typography>
                      )}
                    </Box>
                    {selectedBot.search_method && (
                      <Box>
                        <Typography variant="h5" gutterBottom>
                          検索方法
                        </Typography>
                        {isLoadingSelectBot ? (
                          <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                        ) : (
                          <Typography pl={1}>
                            {displaySearchMethodForUser(selectedBot.search_method)}
                          </Typography>
                        )}
                      </Box>
                    )}
                    {enableDocumentIntelligence && (
                      <Box>
                        <Typography variant="h5" gutterBottom>
                          資料読み取りオプション
                        </Typography>
                        {isLoadingSelectBot ? (
                          <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                        ) : (
                          <Typography pl={1}>
                            {getPdfParserLabel(selectedBot.pdf_parser)}
                          </Typography>
                        )}
                      </Box>
                    )}
                  </>
                )}
                <Box>
                  <Typography variant="h5">Web検索機能</Typography>
                  {isLoadingSelectBot ? (
                    <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                  ) : (
                    <Typography pl={1}>
                      {selectedBot.enable_web_browsing ? "有効" : "無効"}
                    </Typography>
                  )}
                </Box>
              </>
            )}
          </Stack>

          <Divider orientation="vertical" flexItem />

          <Stack flex={1} spacing={2} pl={2}>
            {!isUrsaBot(selectedBot) && (
              <Box sx={{ whiteSpace: "pre-wrap" }}>
                <Typography variant="h5" gutterBottom>
                  カスタム指示
                </Typography>
                {isLoadingSelectBot ? (
                  <Skeleton animation="pulse" variant="text" width="80%" height={30} />
                ) : (
                  <Typography pl={1}>{selectedBot.system_prompt || "未設定"}</Typography>
                )}
              </Box>
            )}
          </Stack>
        </Box>
      </Paper>
    </>
  );
};
