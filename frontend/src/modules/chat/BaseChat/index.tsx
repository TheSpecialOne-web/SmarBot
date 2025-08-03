import ExpandCircleDownIcon from "@mui/icons-material/ExpandCircleDown";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import { Box, IconButton, Link, MenuItem, Stack, Typography } from "@mui/material";
import { Dispatch, ReactNode, SetStateAction } from "react";

import { ExpandableMenu } from "@/components/menus/ExpandableMenu";
import { Spacer } from "@/components/spacers/Spacer";
import { CHAT_LAYOUT_SIDEBAR_WIDTH, TOPBAR_HEIGHT } from "@/const";
import { Approach, Attachment, Bot, DocumentFolder, Guideline } from "@/orval/models/backend-api";

import { ChatQuestionForm } from "../ChatQuestionForm";
import { InitializeChatButton } from "./InitializeChatButton";
import { WebBrowsingCheckbox } from "./WebBrowsingCheckbox";

const DIVIDER_WIDTH = 12;

type Props = {
  children: ReactNode;
  bot: Bot;
  onChatWithBot: (
    question: string,
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
  ) => Promise<void>;
  onStopChat: () => void;
  stoppableChat: boolean;
  enableAttachment?: boolean;
  enableDocumentFolder?: boolean;
  isAtChatBottom: boolean;
  scrollToChatBottomSmoothly: () => void;
  browsingProps?: {
    botApproach: Approach;
    enableWebBrowsing: boolean;
    useWebBrowsing: boolean;
    setUseWebBrowsing: Dispatch<SetStateAction<boolean>>;
  };
  initializeChat: () => void;
  isEmbedded?: boolean;
  guidelines?: Guideline[];
  onClickGuideline?: (guideline: Guideline) => void;
};

export const BaseChat = ({
  children,
  bot,
  onChatWithBot,
  onStopChat,
  stoppableChat,
  enableAttachment = false,
  enableDocumentFolder = true,
  isAtChatBottom,
  scrollToChatBottomSmoothly,
  browsingProps,
  initializeChat,
  isEmbedded = false,
  guidelines,
  onClickGuideline,
}: Props) => {
  const enableWebBrowsing =
    browsingProps?.enableWebBrowsing && browsingProps.botApproach !== "text_2_image";

  return (
    <Stack
      sx={{
        height: isEmbedded ? "100svh" : `calc(100svh - ${TOPBAR_HEIGHT}px)`,
        width: {
          xs: "100vw",
          md: `calc(100vw - ${CHAT_LAYOUT_SIDEBAR_WIDTH + DIVIDER_WIDTH}px)`,
        },
        mx: "auto",
        px: 2,
      }}
    >
      {children}
      <Box
        sx={{
          width: "100%",
          margin: "0 auto",
          position: "relative",
        }}
      >
        {!isAtChatBottom && (
          <IconButton
            onClick={scrollToChatBottomSmoothly}
            sx={{
              position: "absolute",
              left: "50%",
              transform: "translateX(-50%)",
              bottom: "100%",
              mb: 1,
              width: "fit-content",
              padding: 0,
            }}
          >
            <ExpandCircleDownIcon fontSize="large" />
          </IconButton>
        )}
        <Stack direction="row" alignItems="center">
          {enableWebBrowsing && (
            <WebBrowsingCheckbox
              useWebBrowsing={browsingProps.useWebBrowsing}
              setUseWebBrowsing={browsingProps.setUseWebBrowsing}
              showTooltip={browsingProps.botApproach === Approach.neollm}
            />
          )}
          <Box ml="auto">
            <InitializeChatButton onClick={initializeChat} />
          </Box>
        </Stack>
        <Spacer px={4} />
        <ChatQuestionForm
          bot={bot}
          onSend={onChatWithBot}
          stoppable={stoppableChat}
          onStopChat={onStopChat}
          enableAttachment={enableAttachment}
          enableDocumentFolder={enableDocumentFolder}
        />
        <Stack direction="row" alignItems="center" justifyContent="center">
          <Typography
            fontSize={{ xs: "10px", sm: "12px" }}
            color={"grey.500"}
            sx={{
              py: 0.75,
              textAlign: "center",
            }}
          >
            生成AIが提供する情報は誤りを含む可能性があります。重要な情報はご自身でご確認ください。
          </Typography>

          {!isEmbedded &&
            guidelines &&
            guidelines.length > 0 &&
            onClickGuideline &&
            (guidelines.length > 1 ? (
              <ExpandableMenu
                component="link"
                title={<Typography fontSize={{ xs: "10px", sm: "12px" }}>ガイドライン</Typography>}
              >
                {guidelines.map(guideline => (
                  <MenuItem
                    key={guideline.id}
                    sx={{ gap: "8px", alignItems: "center" }}
                    onClick={() => onClickGuideline(guideline)}
                  >
                    <InsertDriveFileOutlinedIcon />
                    {guideline.filename}
                  </MenuItem>
                ))}
              </ExpandableMenu>
            ) : (
              <Link
                component="button"
                fontSize={{ xs: "10px", sm: "12px" }}
                onClick={() => onClickGuideline(guidelines[0])}
              >
                ガイドライン
              </Link>
            ))}
        </Stack>
      </Box>
    </Stack>
  );
};
