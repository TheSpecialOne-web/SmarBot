import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { IconButton, Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
  isLiked: boolean;
  onClick: ({ bot, isLiked }: { bot: Bot; isLiked: boolean }) => void;
};

export const BotProfile = ({ bot, isLiked, onClick }: Props) => {
  const onClickStarIcon = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick({ bot, isLiked: !isLiked });
  };

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between" width="100%">
      <Stack direction="row" spacing={1} alignItems="center">
        <AssistantAvatar size={24} iconUrl={bot.icon_url} iconColor={bot.icon_color} />
        <Typography variant="h6" whiteSpace="pre-wrap">
          {bot.name}
        </Typography>
      </Stack>
      <IconButton
        edge="end"
        onClick={onClickStarIcon}
        sx={{
          padding: 0.5,
        }}
      >
        {isLiked ? (
          <StarIcon fontSize="small" sx={{ color: "gold" }} />
        ) : (
          <StarBorderIcon fontSize="small" />
        )}
      </IconButton>
    </Stack>
  );
};
