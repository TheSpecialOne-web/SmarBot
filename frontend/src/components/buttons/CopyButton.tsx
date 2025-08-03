import CheckIcon from "@mui/icons-material/Check";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Tooltip, Typography } from "@mui/material";

import { IconButtonWithTooltip } from "./IconButtonWithTooltip";

type Props = {
  isCopied: boolean;
  copy: (text: string) => Promise<void>;
  text: string;
  tooltipTitle?: string;
  copyIcon?: React.ReactNode;
};

export const CopyButton = ({ isCopied, copy, text, tooltipTitle, copyIcon }: Props) => {
  return !isCopied ? (
    <IconButtonWithTooltip
      onClick={() => copy(text)}
      tooltipTitle={tooltipTitle ?? "コピー"}
      icon={copyIcon ?? <ContentCopyIcon fontSize="small" />}
      iconButtonSx={{ p: 0 }}
    />
  ) : (
    <Tooltip title={<Typography variant="body2">コピーしました</Typography>} placement="top" arrow>
      <CheckIcon fontSize="small" color="secondary" />
    </Tooltip>
  );
};
