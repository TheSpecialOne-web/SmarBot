import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import { Box, MenuItem, Select, SelectChangeEvent, styled } from "@mui/material";
import { ReactNode, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Spacer } from "@/components/spacers/Spacer";
import { useUserInfo } from "@/hooks/useUserInfo";
import { BotProfile } from "@/modules/layouts/sidebars/ChatSidebar/BotProfile";
import { toggleLikedBot } from "@/orval/backend-api";
import { Bot, LikedBotParam } from "@/orval/models/backend-api";
import { theme } from "@/theme";

import { BasicAiBotProfile } from "../BasicAiBotProfile";
import { SelectedBotDisplay } from "../SelectedBotDisplay";
import { SubtitleText } from "../SubtitleText";

type Props = {
  reorderBots: (bot: Bot) => void;
  chatGptBots: Bot[];
  assistants: Bot[];
};

const MAX_HEIGHT = 492;
const MIN_WIDTH = 228;
const MAX_WIDTH = 320;

const StyledSelect = styled(Select<number>)(() => ({
  fontWeight: "bold",
  fontSize: "16px",
  ":hover": {
    backgroundColor: theme.palette.onHover.main,
  },
  // 枠を消す
  ".MuiOutlinedInput-notchedOutline": {
    border: 0,
  },
  // フォーカス時の枠を消す
  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
    border: 0,
  },
  ".MuiOutlinedInput-input": {
    padding: "12px",
  },
}));

export const BotList = ({ reorderBots, chatGptBots, assistants }: Props) => {
  const { userInfo, fetchUserInfo } = useUserInfo();
  const navigate = useNavigate();
  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const queryParamBotId = parseInt(queryParams.get("botId") || "");

  const onChangeBot = (event: SelectChangeEvent<number>) => {
    const botId = event.target.value;
    const selectedBot = [...chatGptBots, ...assistants].find(bot => bot.id === botId);
    if (!selectedBot) {
      return;
    }

    reorderBots(selectedBot);
    navigate(`/main/chat?botId=${botId}`);
  };

  const likedAssistants = useMemo(() => {
    if (!userInfo.liked_bot_ids || assistants.length === 0) return [];
    return assistants.filter(assistant => userInfo.liked_bot_ids.includes(assistant.id));
  }, [userInfo.liked_bot_ids, assistants]);

  const filteredAssistants = useMemo(
    () =>
      assistants
        .filter(bot => !likedAssistants.some(likedBot => likedBot.id === bot.id))
        .slice(0, 5),
    [assistants, likedAssistants],
  );

  const handleToggleLikedBot = async ({ bot, isLiked }: { bot: Bot; isLiked: boolean }) => {
    const likedBotParam: LikedBotParam = {
      is_liked: isLiked,
    };
    await toggleLikedBot(bot.id, likedBotParam);
    fetchUserInfo();
  };

  const renderValue = (value: number): ReactNode => {
    const selectedBot = [...chatGptBots, ...assistants].find(bot => bot.id === value);
    if (!selectedBot) return null;

    return <SelectedBotDisplay bot={selectedBot} />;
  };

  return (
    <StyledSelect
      value={queryParamBotId || ""}
      onChange={onChangeBot}
      displayEmpty
      IconComponent={ExpandMoreRoundedIcon}
      renderValue={renderValue}
      MenuProps={{
        PaperProps: {
          style: {
            maxHeight: MAX_HEIGHT,
            minWidth: MIN_WIDTH,
            maxWidth: MAX_WIDTH,
          },
        },
      }}
    >
      {/* chatGptBots */}
      {chatGptBots.length > 0 && (
        <Box sx={{ pl: 1 }}>
          <Spacer px={8} />
          <SubtitleText text="基盤モデル" />
        </Box>
      )}
      {chatGptBots.map(bot => (
        <MenuItem
          key={bot.id}
          value={bot.id}
          sx={{ fontWeight: "bold", fontSize: "14px", whiteSpace: "pre-wrap" }}
          disableRipple
        >
          <BasicAiBotProfile bot={bot} />
        </MenuItem>
      ))}

      {/* assistants */}
      {assistants.length > 0 && (
        <Box sx={{ pl: 1 }}>
          <Spacer px={8} />
          <SubtitleText text="アシスタント" />
        </Box>
      )}
      {likedAssistants.map(bot => (
        <MenuItem key={bot.id} value={bot.id} disableRipple>
          <BotProfile bot={bot} isLiked={true} onClick={handleToggleLikedBot} />
        </MenuItem>
      ))}
      {filteredAssistants.map(bot => (
        <MenuItem key={bot.id} value={bot.id} disableRipple>
          <BotProfile bot={bot} isLiked={false} onClick={handleToggleLikedBot} />
        </MenuItem>
      ))}
    </StyledSelect>
  );
};
