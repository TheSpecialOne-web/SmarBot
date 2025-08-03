import { Box, Grid, Stack, Typography } from "@mui/material";
import { forwardRef } from "react";

import { SecondaryButton } from "@/components/buttons/SecondaryButton";
import { isChatGptBot } from "@/libs/bot";
import { AssistantsSearchCard } from "@/modules/assistants/search-bots/AssistantsSearchCard";
import { BasicAiSearchCard } from "@/modules/assistants/search-bots/BasicAiSearchCard";
import { BotWithLikedStatus } from "@/modules/assistants/search-bots/type";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  title: string;
  bots: BotWithLikedStatus[];
  onClickIcon?: ({ bot, isLiked }: { bot: Bot; isLiked: boolean }) => void;
  onClickCard: (assistant: Bot) => void;
  showMore: boolean;
  onToggleShowMore?: () => void;
  isShowingAll?: boolean;
};

export const BotsSearchSection = forwardRef<HTMLDivElement, Props>(
  ({ title, bots, onClickIcon, onClickCard, showMore, onToggleShowMore, isShowingAll }, ref) => {
    return (
      <Box ref={ref} pt={2}>
        <Typography variant="h3" mb={1}>
          {title}
        </Typography>
        {bots.length === 0 ? (
          <>
            <Stack p={4} direction="row" justifyContent="center">
              <Typography>アシスタントがありません。</Typography>
            </Stack>
          </>
        ) : (
          <Grid container spacing={2} mb={1}>
            {bots.map((bot, index) => (
              <Grid item xs={12} md={6} xl={4} key={index}>
                {isChatGptBot(bot) ? (
                  <BasicAiSearchCard bot={bot} onClickCard={onClickCard} />
                ) : (
                  <AssistantsSearchCard
                    assistant={bot}
                    onClickIcon={onClickIcon}
                    onClickCard={onClickCard}
                  />
                )}
              </Grid>
            ))}
          </Grid>
        )}
        {showMore && (
          <Box justifyContent="center" display="flex">
            <SecondaryButton
              variant="outlined"
              text={isShowingAll ? "表示を減らす" : "もっと見る"}
              onClick={onToggleShowMore}
            />
          </Box>
        )}
      </Box>
    );
  },
);

BotsSearchSection.displayName = "AssistantSection";
