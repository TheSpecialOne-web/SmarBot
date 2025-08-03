import CheckIcon from "@mui/icons-material/Check";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import RefreshIcon from "@mui/icons-material/Refresh";
import { Stack } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";

import { ChatIconButton } from "@/components/buttons/ChatIconButton";
import { Feedback } from "@/orval/models/backend-api";

import { DownloadButton } from "./DownloadButton";
import { FeedbackButtons } from "./FeedbackButtons";

type Props = {
  isEmbeddedChat: boolean;
  displayCopyButton?: boolean;
  isCopied?: boolean;
  onCopy?: () => void;
  isRegenerateButtonVisible?: boolean;
  onRegenerateAnswer?: () => void;
  isFeedbackButtonVisible?: boolean;
  feedback?: Feedback;
  onClickFeedback?: (feedback: Feedback) => void;
  isDownloadButtonVisible?: boolean;
  isDownloadingDocx?: boolean;
  onClickDownloadDocx?: () => void;
};

export const ChatActionButtons = ({
  isEmbeddedChat,
  displayCopyButton,
  isCopied,
  onCopy,
  isRegenerateButtonVisible,
  onRegenerateAnswer,
  isFeedbackButtonVisible,
  feedback,
  onClickFeedback,
  isDownloadButtonVisible,
  isDownloadingDocx,
  onClickDownloadDocx,
}: Props) => {
  const { tmpRetryConversation } = useFlags();

  return (
    <Stack direction="row" alignItems="center">
      {displayCopyButton &&
        onCopy &&
        (isCopied ? (
          <ChatIconButton
            tooltipTitle="コピーしました"
            onClick={onCopy}
            icon={<CheckIcon fontSize="small" />}
          />
        ) : (
          <ChatIconButton
            tooltipTitle="コピー"
            onClick={onCopy}
            icon={<ContentCopyIcon fontSize="small" />}
          />
        ))}
      {tmpRetryConversation && isRegenerateButtonVisible && onRegenerateAnswer && (
        <ChatIconButton
          tooltipTitle="回答の再生成"
          onClick={onRegenerateAnswer}
          icon={<RefreshIcon />}
        />
      )}
      {isFeedbackButtonVisible && onClickFeedback && (
        <FeedbackButtons feedback={feedback} onClickFeedback={onClickFeedback} />
      )}
      {isDownloadButtonVisible && !isEmbeddedChat && onClickDownloadDocx && (
        <DownloadButton
          tooltipTitle="Word形式でエクスポート"
          isDownloading={isDownloadingDocx}
          onClickDownload={onClickDownloadDocx}
        />
      )}
    </Stack>
  );
};
