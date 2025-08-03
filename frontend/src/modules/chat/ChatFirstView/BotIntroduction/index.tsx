import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { IconButton, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BasicAiAvater } from "@/components/icons/BasicAiAvatar";
import { Text2ImageAvater } from "@/components/icons/Text2ImageAvater";
import { useScreen } from "@/hooks/useScreen";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getBaseModelColor, isChatGptBot } from "@/libs/bot";
import { toggleLikedBot } from "@/orval/backend-api";
import { Approach, Bot, LikedBotParam } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
  isEmbedded?: boolean;
};

export const BotIntroduction = ({ bot, isEmbedded = false }: Props) => {
  const navigate = useNavigate();
  const { userInfo, fetchUserInfo } = useUserInfo();
  const AvatarComponent =
    bot.approach === "text_2_image"
      ? Text2ImageAvater
      : bot.approach === "chat_gpt_default"
      ? BasicAiAvater
      : AssistantAvatar;
  const { isMobile } = useScreen();

  const handleToggleLikedBot = async ({ bot, isLiked }: { bot: Bot; isLiked: boolean }) => {
    if (isEmbedded) return;
    const likedBotParam: LikedBotParam = {
      is_liked: isLiked,
    };
    await toggleLikedBot(bot.id, likedBotParam);
    fetchUserInfo();
  };

  const isLikedAssistant = isEmbedded ? false : userInfo.liked_bot_ids.includes(bot.id);

  const handleMoveToAssistantPage = () => {
    if (isMobile) return;
    navigate(`/main/assistants/${bot.id}`);
  };

  return (
    <Stack
      textAlign="center"
      alignItems="center"
      flexDirection="column"
      spacing={1}
      sx={{
        pt: 1,
      }}
    >
      <Stack direction="row" position="relative">
        <AvatarComponent
          size={80}
          onClick={
            ([Approach.neollm, Approach.custom_gpt, Approach.ursa] as string[]).includes(
              bot.approach,
            ) && !isEmbedded
              ? handleMoveToAssistantPage
              : undefined
          }
          iconUrl={bot.icon_url}
          iconColor={bot.icon_color}
          bgColor={getBaseModelColor(bot.model_family)}
        />
        {!isChatGptBot(bot) && !isEmbedded && (
          <IconButton
            onClick={e => {
              e.stopPropagation();
              handleToggleLikedBot({ bot, isLiked: !isLikedAssistant });
            }}
            sx={{
              padding: 0.5,
              position: "absolute",
              top: -11,
              right: -14,
            }}
          >
            {isLikedAssistant ? (
              <StarIcon fontSize="medium" sx={{ color: "gold" }} />
            ) : (
              <StarBorderIcon fontSize="medium" />
            )}
          </IconButton>
        )}
      </Stack>
      <Typography variant="h3" gutterBottom>
        {bot.name}
      </Typography>
      <Typography textAlign="center" whiteSpace="pre-wrap">
        {bot.description}
      </Typography>
    </Stack>
  );
};
