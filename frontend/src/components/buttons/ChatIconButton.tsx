import { ReactNode } from "react";

import { IconButtonWithTooltip } from "./IconButtonWithTooltip";

type Props = {
  tooltipTitle: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
};

export const ChatIconButton = ({ tooltipTitle, icon, onClick, disabled }: Props) => {
  return (
    <IconButtonWithTooltip
      tooltipTitle={tooltipTitle}
      placement="bottom"
      onClick={onClick}
      icon={icon}
      arrow={false}
      offset={-10}
      disabled={disabled}
    />
  );
};
