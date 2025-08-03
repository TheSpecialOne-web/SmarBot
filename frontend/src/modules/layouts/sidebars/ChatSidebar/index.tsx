import GridViewIcon from "@mui/icons-material/GridView";
import { Box, Button, Divider, Link, Skeleton, Stack, Typography } from "@mui/material";
import { blue } from "@mui/material/colors";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { CHAT_LAYOUT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useScreen } from "@/hooks/useScreen";
import { getErrorMessage } from "@/libs/error";
import { useGetBot } from "@/orval/backend-api";
import { Bot, Conversation } from "@/orval/models/backend-api";

import { BotList } from "./BotList";
import { ChatReturnButton } from "./ChatReturnButton";
import { ConversationHistory } from "./ConversationHistory";

const BOT_LIST_HEIGHT = 48;

type Props = {
  reorderBots: (bot: Bot) => void;
  chatGptBots: Bot[];
  assistants: Bot[];
  conversations: Conversation[];
  onClose?: () => void;
  toggleShowSidebar: () => void;
  isLoadingFetchBots: boolean;
  isLoadingFetchConversations: boolean;
};

export const ChatSidebar = ({
  reorderBots,
  chatGptBots,
  assistants,
  conversations,
  onClose,
  toggleShowSidebar,
  isLoadingFetchBots,
  isLoadingFetchConversations,
}: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const { isTablet } = useScreen();
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const selectedPath = "#" + location.pathname;
  const isBotsSearchPage = selectedPath.startsWith("#/main/bots/search");
  const currentBotId = Number(searchParams.get("botId"));
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [isDividerHovered, setIsDividerHovered] = useState(false);

  const handleMoveToBotsSearch = () => {
    if (isBotsSearchPage) return;
    if (currentBotId !== selectedBotId) {
      setSelectedBotId(currentBotId);
    }
    navigate("/main/bots/search");
  };

  const {
    data: bot,
    error,
    isLoading,
  } = useGetBot(selectedBotId!, {
    swr: { enabled: selectedBotId !== null },
  });
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "アシスタントの取得に失敗しました。" });
  }

  return (
    <>
      <Box
        width={{ xs: "100%", md: CHAT_LAYOUT_SIDEBAR_WIDTH }}
        minWidth={CHAT_LAYOUT_SIDEBAR_WIDTH}
        sx={{
          height: `calc(100vh - ${TOPBAR_HEIGHT}px)`,
          bgcolor: "background.paper",
          overflowY: "auto",
        }}
      >
        <Stack px={2} py={3} sx={{ width: "100%", height: "100%" }}>
          <Stack gap={1} flex={1}>
            {isBotsSearchPage && bot ? (
              <ChatReturnButton bot={bot} />
            ) : isLoadingFetchBots || isLoading ? (
              <Skeleton variant="rounded" width="100%" height={BOT_LIST_HEIGHT} />
            ) : (
              <BotList
                reorderBots={bot => {
                  if (isTablet) {
                    onClose?.();
                  }
                  reorderBots(bot);
                }}
                chatGptBots={chatGptBots}
                assistants={assistants}
              />
            )}
            <Button
              component={Link}
              color="inherit"
              startIcon={<GridViewIcon />}
              fullWidth
              onClick={handleMoveToBotsSearch}
              sx={{
                justifyContent: "flex-start",
                color: selectedPath.startsWith("#/main/bots/search") ? "primary.main" : "inherit",
                pl: 1.8,
                py: 1,
              }}
            >
              <Typography variant="h5">アシスタントを探す</Typography>
            </Button>
            <Divider />
            <ConversationHistory
              conversations={conversations}
              onCloseSidebar={onClose}
              isLoadingFetchConversations={isLoadingFetchConversations}
            />
          </Stack>
        </Stack>
      </Box>
      <Stack
        direction="row"
        onMouseEnter={() => setIsDividerHovered(true)}
        onMouseLeave={() => setIsDividerHovered(false)}
        onClick={toggleShowSidebar}
        sx={{
          cursor: "w-resize",
        }}
      >
        <Box width={4} bgcolor="background.paper" />
        <Divider
          orientation="vertical"
          flexItem
          sx={{
            width: "2px",
            bgcolor: "background.paper",
            ...(isDividerHovered && { backgroundColor: blue[300], borderColor: blue[300] }),
          }}
        />
        <Box width={6} />
      </Stack>
    </>
  );
};
